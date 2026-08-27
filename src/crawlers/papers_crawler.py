"""
Research Papers Vertical Crawler:
Extracts AI papers from arXiv API and PapersWithCode, correlates GitHub repositories,
and fetches live GitHub star counts.
"""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse
from src.crawlers.base import BaseAsyncCrawler
from src.schemas import ResearchPaperEntity, ResearchPaperContent
from src.config import GITHUB_TOKEN, TARGET_PAPERS_COUNT

logger = logging.getLogger("PapersCrawler")


class PapersCrawler(BaseAsyncCrawler):
    ARXIV_API_URL = "https://export.arxiv.org/api/query"
    PWC_API_URL = "https://paperswithcode.com/api/v1/papers/"

    def __init__(self, concurrency: int = 15):
        super().__init__(concurrency=concurrency)
        self.github_star_cache: Dict[str, int] = {}

    def _extract_github_url(self, text: str) -> Optional[str]:
        """Extract valid GitHub repo URL from abstract or paper metadata."""
        if not text:
            return None
        match = re.search(r'https?://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)', text)
        if match:
            owner, repo = match.group(1), match.group(2)
            repo = re.sub(r'[.,\)\;\'\"]+$', '', repo)  # clean trailing punctuation
            if owner.lower() not in ("topics", "features", "collections", "trending", "pricing"):
                return f"https://github.com/{owner}/{repo}"
        return None

    async def fetch_github_stars(self, github_url: str) -> int:
        """Fetch live star count from GitHub API or HTML scraping with fallback caching."""
        if not github_url:
            return 0
        if github_url in self.github_star_cache:
            return self.github_star_cache[github_url]

        parsed = urlparse(github_url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(path_parts) < 2:
            return 0
        owner, repo = path_parts[0], path_parts[1].replace(".git", "")

        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

        data = await self.fetch_json(api_url, headers=headers)
        if data and isinstance(data, dict) and "stargazers_count" in data:
            stars = int(data["stargazers_count"])
            self.github_star_cache[github_url] = stars
            return stars

        # Fallback: scrape from GitHub page meta tags if unauthenticated rate limit hit
        html = await self.fetch_text(github_url)
        if html:
            star_match = re.search(r'id="repo-stars-counter-star"[^>]*title="([\d,]+)"', html)
            if star_match:
                try:
                    stars = int(star_match.group(1).replace(",", ""))
                    self.github_star_cache[github_url] = stars
                    return stars
                except ValueError:
                    pass
            # Alternate match
            star_match_alt = re.search(r'([\d\.]+[kKmM]?)\s*stars?', html)
            if star_match_alt:
                val = star_match_alt.group(1).lower()
                if "k" in val:
                    stars = int(float(val.replace("k", "")) * 1000)
                elif "m" in val:
                    stars = int(float(val.replace("m", "")) * 1000000)
                else:
                    try:
                        stars = int(val)
                    except ValueError:
                        stars = 0
                self.github_star_cache[github_url] = stars
                return stars

        return 0

    async def fetch_arxiv_batch(self, search_query: str, start_index: int, max_results: int) -> List[Dict[str, Any]]:
        """Fetch batch of research papers from arXiv API using Atom XML format."""
        params = f"?search_query={search_query}&start={start_index}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        url = f"{self.ARXIV_API_URL}{params}"
        
        xml_text = await self.fetch_text(url)
        if not xml_text:
            logger.warning(f"Failed to fetch arXiv batch at start index {start_index}")
            return []

        papers = []
        try:
            root = ET.fromstring(xml_text)
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

            for entry in root.findall("atom:entry", ns):
                title_elem = entry.find("atom:title", ns)
                id_elem = entry.find("atom:id", ns)
                published_elem = entry.find("atom:published", ns)
                summary_elem = entry.find("atom:summary", ns)
                
                title = " ".join(title_elem.text.split()) if title_elem is not None and title_elem.text else "Untitled Paper"
                paper_url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
                published_date = published_elem.text.strip() if published_elem is not None and published_elem.text else ""
                summary = " ".join(summary_elem.text.split()) if summary_elem is not None and summary_elem.text else ""

                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())

                papers.append({
                    "title": title,
                    "paper_url": paper_url,
                    "published_date": published_date,
                    "summary": summary,
                    "authors": authors
                })
        except Exception as e:
            logger.error(f"Error parsing arXiv XML response: {e}")

        return papers

    async def fetch_paperswithcode_links(self) -> Dict[str, str]:
        """Fetch trending papers from PapersWithCode for repo correlation."""
        pwc_url = "https://paperswithcode.com/api/v1/papers/?ordering=-stars&page_size=100"
        pwc_data = await self.fetch_json(pwc_url)
        correlations = {}
        if pwc_data and "results" in pwc_data:
            for item in pwc_data.get("results", []):
                arxiv_id = item.get("arxiv_id")
                repo_url = item.get("url_abs")
                if arxiv_id and repo_url:
                    correlations[arxiv_id] = repo_url
        return correlations

    async def crawl(self, target_count: int = TARGET_PAPERS_COUNT) -> List[ResearchPaperEntity]:
        """Crawl and correlate research papers with GitHub repositories and star metrics."""
        logger.info(f"Starting Research Papers crawl (Target: {target_count} papers)...")
        categories = ["cat:cs.AI", "cat:cs.LG", "cat:cs.CV", "cat:cs.CL", "cat:cs.NE", "cat:stat.ML"]
        query = " OR ".join(categories)

        batch_size = 200
        total_batches = (target_count // batch_size) + 2
        tasks = []

        for i in range(total_batches):
            start = i * batch_size
            tasks.append(self.fetch_arxiv_batch(query, start, batch_size))

        batch_results = await asyncio.gather(*tasks)
        all_raw_papers = [paper for batch in batch_results for paper in batch]
        logger.info(f"Fetched {len(all_raw_papers)} raw papers from arXiv API.")

        # Correlate GitHub repos and stars
        entities: List[ResearchPaperEntity] = []
        star_tasks = []
        paper_records = []

        seen_urls = set()

        for paper in all_raw_papers:
            if len(entities) >= target_count:
                break
            if paper["paper_url"] in seen_urls:
                continue
            seen_urls.add(paper["paper_url"])

            # Extract GitHub repo from summary/abstract
            github_url = self._extract_github_url(paper["summary"])
            if not github_url and "github.com" in paper["title"]:
                github_url = self._extract_github_url(paper["title"])

            paper_records.append((paper, github_url))
            if github_url:
                star_tasks.append(self.fetch_github_stars(github_url))
            else:
                star_tasks.append(asyncio.sleep(0, result=0))

        # Fetch stars concurrently with rate limiting
        star_results = await asyncio.gather(*star_tasks)

        for (paper, github_url), stars in zip(paper_records, star_results):
            entity = ResearchPaperEntity(
                schemaVersion="1.0",
                recordType="RESEARCH_PAPER",
                content=ResearchPaperContent(
                    title=paper["title"],
                    authors=paper["authors"] if paper["authors"] else ["Anonymous"],
                    paper_url=paper["paper_url"],
                    github_url=github_url,
                    github_stars=stars if stars else 0,
                    published_date=paper["published_date"],
                    summary=paper["summary"][:500] if paper["summary"] else None
                )
            )
            entities.append(entity)
            if len(entities) >= target_count:
                break

        logger.info(f"Successfully collected {len(entities)} research papers ({sum(1 for e in entities if e.content.github_url)} with GitHub links).")
        return entities

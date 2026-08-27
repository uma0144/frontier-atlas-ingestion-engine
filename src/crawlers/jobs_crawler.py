"""
AI Jobs Signal Crawler:
Monitors 5 distinct AI/Tech job platforms with automated field extraction and strict 24-hour freshness verification.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import feedparser
from bs4 import BeautifulSoup
from src.crawlers.base import BaseAsyncCrawler
from src.schemas import JobEntity, JobContent
from src.utils.date_parser import parse_flexible_date, is_within_last_24_hours, format_iso8601

logger = logging.getLogger("JobsCrawler")


class JobsCrawler(BaseAsyncCrawler):
    def _categorize_role(self, title: str) -> str:
        """Categorize job title into a standardized role family."""
        title_lower = title.lower()
        if any(w in title_lower for w in ["research", "scientist", "phd", "postdoc"]):
            return "AI Research"
        elif any(w in title_lower for w in ["mlops", "devops", "infrastructure", "platform"]):
            return "AI Infrastructure & MLOps"
        elif any(w in title_lower for w in ["engineer", "developer", "backend", "full stack", "frontend"]):
            return "Engineering"
        elif any(w in title_lower for w in ["product", "pm", "owner"]):
            return "Product Management"
        elif any(w in title_lower for w in ["data", "analyst", "analytics"]):
            return "Data Science & Analytics"
        else:
            return "Engineering"

    async def fetch_remoteok(self) -> List[JobEntity]:
        """Fetch AI jobs from RemoteOK."""
        url = "https://remoteok.com/api?tag=ai"
        entities = []
        data = await self.fetch_json(url, headers={"User-Agent": "Mozilla/5.0 FrontierAtlas/1.0"})
        if not data or not isinstance(data, list):
            return []

        for item in data[1:]:  # skip first metadata entry
            title = item.get("position") or item.get("title")
            company = item.get("company")
            date_str = item.get("date")
            apply_url = item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id')}"

            if not title or not company:
                continue

            parsed_dt = parse_flexible_date(date_str)
            if parsed_dt and is_within_last_24_hours(parsed_dt):
                entity = JobEntity(
                    schemaVersion="1.0",
                    recordType="JOB",
                    content=JobContent(
                        job_title=title,
                        company=company,
                        date=format_iso8601(parsed_dt),
                        is_remote=True,
                        role_family=self._categorize_role(title),
                        location=item.get("location") or "Remote Worldwide",
                        job_url=apply_url
                    )
                )
                entities.append(entity)
        return entities

    async def fetch_jobicy(self) -> List[JobEntity]:
        """Fetch remote engineering and AI jobs from Jobicy."""
        url = "https://jobicy.com/api/v2/remote-jobs?count=50&industry=engineering"
        entities = []
        data = await self.fetch_json(url)
        if not data or "jobs" not in data:
            return []

        for item in data.get("jobs", []):
            title = item.get("jobTitle")
            company = item.get("companyName")
            pub_date = item.get("pubDate")
            job_url = item.get("url")

            if not title or not company:
                continue

            parsed_dt = parse_flexible_date(pub_date)
            if parsed_dt and is_within_last_24_hours(parsed_dt):
                entity = JobEntity(
                    schemaVersion="1.0",
                    recordType="JOB",
                    content=JobContent(
                        job_title=title,
                        company=company,
                        date=format_iso8601(parsed_dt),
                        is_remote=True,
                        role_family=self._categorize_role(title),
                        location=item.get("jobGeo") or "Remote",
                        job_url=job_url
                    )
                )
                entities.append(entity)
        return entities

    async def fetch_weworkremotely(self) -> List[JobEntity]:
        """Fetch programming jobs from WeWorkRemotely RSS feed."""
        url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
        entities = []
        xml_text = await self.fetch_text(url)
        if not xml_text:
            return []

        feed = feedparser.parse(xml_text)
        for entry in feed.entries:
            title_full = entry.get("title", "")
            # WWR format: "CompanyName: JobTitle"
            parts = title_full.split(":", 1)
            company = parts[0].strip() if len(parts) > 1 else "Tech Startup"
            title = parts[1].strip() if len(parts) > 1 else title_full

            pub_date = entry.get("published") or entry.get("pubDate")
            job_url = entry.get("link", "")

            parsed_dt = parse_flexible_date(pub_date)
            if parsed_dt and is_within_last_24_hours(parsed_dt):
                entity = JobEntity(
                    schemaVersion="1.0",
                    recordType="JOB",
                    content=JobContent(
                        job_title=title,
                        company=company,
                        date=format_iso8601(parsed_dt),
                        is_remote=True,
                        role_family=self._categorize_role(title),
                        location="Remote",
                        job_url=job_url
                    )
                )
                entities.append(entity)
        return entities

    async def fetch_remotive(self) -> List[JobEntity]:
        """Fetch jobs from Remotive API."""
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=50"
        entities = []
        data = await self.fetch_json(url)
        if not data or "jobs" not in data:
            return []

        for item in data.get("jobs", []):
            title = item.get("title")
            company = item.get("company_name")
            pub_date = item.get("publication_date")
            job_url = item.get("url")

            if not title or not company:
                continue

            parsed_dt = parse_flexible_date(pub_date)
            if parsed_dt and is_within_last_24_hours(parsed_dt):
                entity = JobEntity(
                    schemaVersion="1.0",
                    recordType="JOB",
                    content=JobContent(
                        job_title=title,
                        company=company,
                        date=format_iso8601(parsed_dt),
                        is_remote=True,
                        role_family=self._categorize_role(title),
                        location=item.get("candidate_required_location") or "Remote",
                        job_url=job_url
                    )
                )
                entities.append(entity)
        return entities

    async def fetch_arbeitnow(self) -> List[JobEntity]:
        """Fetch tech and AI jobs from Arbeitnow."""
        url = "https://www.arbeitnow.com/api/job-board-api"
        entities = []
        data = await self.fetch_json(url)
        if not data or "data" not in data:
            return []

        for item in data.get("data", []):
            title = item.get("title")
            company = item.get("company_name")
            created_at = item.get("created_at")
            job_url = item.get("url")
            remote = item.get("remote", True)

            if not title or not company:
                continue

            parsed_dt = parse_flexible_date(created_at)
            if parsed_dt and is_within_last_24_hours(parsed_dt):
                entity = JobEntity(
                    schemaVersion="1.0",
                    recordType="JOB",
                    content=JobContent(
                        job_title=title,
                        company=company,
                        date=format_iso8601(parsed_dt),
                        is_remote=remote,
                        role_family=self._categorize_role(title),
                        location=item.get("location") or "Remote",
                        job_url=job_url
                    )
                )
                entities.append(entity)
        return entities

    async def crawl(self) -> List[JobEntity]:
        """Crawl all 5 AI job boards and return strictly 24h fresh jobs."""
        logger.info("Starting Fresh AI Jobs Crawl (5 distinct sources)...")
        tasks = [
            self.fetch_remoteok(),
            self.fetch_jobicy(),
            self.fetch_weworkremotely(),
            self.fetch_remotive(),
            self.fetch_arbeitnow()
        ]
        results = await asyncio.gather(*tasks)
        all_jobs = [item for sublist in results for item in sublist]
        logger.info(f"Collected {len(all_jobs)} strictly 24-hour fresh job postings.")
        return all_jobs

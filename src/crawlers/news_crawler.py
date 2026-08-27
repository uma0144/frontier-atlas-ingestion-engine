"""
AI News Signal Crawler:
Monitors 5 top AI news feeds with automated full-text extraction and strict 24-hour freshness normalization.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import feedparser
from bs4 import BeautifulSoup
from src.crawlers.base import BaseAsyncCrawler
from src.schemas import NewsEntity, NewsContent
from src.utils.date_parser import parse_flexible_date, is_within_last_24_hours, format_iso8601

logger = logging.getLogger("NewsCrawler")


class NewsCrawler(BaseAsyncCrawler):
    SOURCES = [
        {
            "name": "TechCrunch AI",
            "type": "rss",
            "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        },
        {
            "name": "VentureBeat AI",
            "type": "rss",
            "url": "https://venturebeat.com/category/ai/feed/",
        },
        {
            "name": "The Verge AI",
            "type": "rss",
            "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        },
        {
            "name": "MIT Technology Review",
            "type": "rss",
            "url": "https://www.technologyreview.com/feed/",
        },
        {
            "name": "Hacker News AI Signals",
            "type": "api",
            "url": "https://hn.algolia.com/api/v1/search_by_date?tags=story&query=AI%20OR%20LLM&hitsPerPage=50",
        }
    ]

    async def _parse_rss_source(self, source_info: Dict[str, str]) -> List[NewsEntity]:
        """Fetch and parse RSS feed with 24h freshness check."""
        entities = []
        xml_content = await self.fetch_text(source_info["url"])
        if not xml_content:
            logger.warning(f"Could not fetch RSS feed for {source_info['name']}")
            return []

        feed = feedparser.parse(xml_content)
        for entry in feed.entries:
            title = entry.get("title", "Untitled")
            link = entry.get("link", "")
            raw_date = entry.get("published") or entry.get("updated") or entry.get("pubDate")
            author = entry.get("author")

            # Extract clean summary text
            summary_raw = entry.get("summary") or entry.get("description", "")
            soup = BeautifulSoup(summary_raw, "html.parser")
            summary = " ".join(soup.get_text().split())

            parsed_dt = parse_flexible_date(raw_date)
            # Enforce 24-hour freshness
            if parsed_dt and is_within_last_24_hours(parsed_dt):
                entity = NewsEntity(
                    schemaVersion="1.0",
                    recordType="NEWS",
                    content=NewsContent(
                        title=title,
                        source_name=source_info["name"],
                        url=link,
                        published_date=format_iso8601(parsed_dt),
                        summary=summary[:1000] if summary else f"Article on {title}",
                        author=author
                    )
                )
                entities.append(entity)

        return entities

    async def _parse_hn_source(self, source_info: Dict[str, str]) -> List[NewsEntity]:
        """Fetch Hacker News AI stories via Algolia API with 24h filter."""
        entities = []
        data = await self.fetch_json(source_info["url"])
        if not data or "hits" not in data:
            return []

        for hit in data.get("hits", []):
            title = hit.get("title")
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            created_at = hit.get("created_at")
            author = hit.get("author")

            parsed_dt = parse_flexible_date(created_at)
            if parsed_dt and is_within_last_24_hours(parsed_dt):
                points = hit.get("points", 0)
                comments = hit.get("num_comments", 0)
                entity = NewsEntity(
                    schemaVersion="1.0",
                    recordType="NEWS",
                    content=NewsContent(
                        title=title,
                        source_name=source_info["name"],
                        url=url,
                        published_date=format_iso8601(parsed_dt),
                        summary=f"Hacker News AI signal with {points} points and {comments} comments.",
                        author=author
                    )
                )
                entities.append(entity)

        return entities

    async def crawl(self) -> List[NewsEntity]:
        """Crawl all 5 AI news sources and return strictly 24h fresh news."""
        logger.info("Starting Fresh AI News Crawl (5 distinct sources)...")
        tasks = []
        for src in self.SOURCES:
            if src["type"] == "rss":
                tasks.append(self._parse_rss_source(src))
            else:
                tasks.append(self._parse_hn_source(src))

        results = await asyncio.gather(*tasks)
        all_news = [item for sublist in results for item in sublist]
        logger.info(f"Collected {len(all_news)} strictly 24-hour fresh news articles.")
        return all_news

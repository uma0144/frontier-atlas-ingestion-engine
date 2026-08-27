"""
Base Asynchronous Crawler with retry resilience, concurrency management,
User-Agent rotation, and rate-limit handling.
"""

import asyncio
import logging
import random
from typing import Optional, Dict, Any
import aiohttp
from src.config import (
    DEFAULT_CONCURRENCY,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_RETRIES,
    INITIAL_BACKOFF_SECONDS,
    BACKOFF_FACTOR,
    MAX_BACKOFF_SECONDS,
    JITTER_RANGE
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("BaseCrawler")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36",
]


class BaseAsyncCrawler:
    def __init__(self, concurrency: int = DEFAULT_CONCURRENCY, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS):
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds, connect=10)
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=self.concurrency * 2, ssl=False)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers={"Accept-Language": "en-US,en;q=0.9"}
            )
        return self._session

    def get_random_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers

    async def fetch_text(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Fetch URL with retries, exponential backoff, and 429 jitter handling."""
        session = await self.get_session()
        request_headers = self.get_random_headers(headers)
        backoff = INITIAL_BACKOFF_SECONDS

        async with self.semaphore:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    async with session.get(url, headers=request_headers) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 429:
                            retry_after = response.headers.get("Retry-After")
                            wait_time = float(retry_after) if retry_after else backoff + random.uniform(*JITTER_RANGE)
                            logger.warning(f"Rate limited (429) on {url}. Backing off for {wait_time:.2f}s (Attempt {attempt}/{MAX_RETRIES})")
                            await asyncio.sleep(wait_time)
                            backoff = min(backoff * BACKOFF_FACTOR, MAX_BACKOFF_SECONDS)
                        elif response.status in (500, 502, 503, 504):
                            logger.warning(f"Server error ({response.status}) on {url}. Retrying in {backoff:.2f}s...")
                            await asyncio.sleep(backoff + random.uniform(*JITTER_RANGE))
                            backoff = min(backoff * BACKOFF_FACTOR, MAX_BACKOFF_SECONDS)
                        else:
                            logger.debug(f"HTTP {response.status} when fetching {url}")
                            return None
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.warning(f"Network error fetching {url} on attempt {attempt}: {e}")
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(backoff + random.uniform(*JITTER_RANGE))
                        backoff = min(backoff * BACKOFF_FACTOR, MAX_BACKOFF_SECONDS)
                    else:
                        logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts.")
                        return None
                except Exception as e:
                    logger.error(f"Unexpected error fetching {url}: {e}")
                    return None
        return None

    async def fetch_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[Any]:
        """Fetch JSON payload with retries and rate limit handling."""
        session = await self.get_session()
        request_headers = self.get_random_headers(headers)
        request_headers["Accept"] = "application/json"
        backoff = INITIAL_BACKOFF_SECONDS

        async with self.semaphore:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    async with session.get(url, headers=request_headers) as response:
                        if response.status == 200:
                            return await response.json(content_type=None)
                        elif response.status == 429:
                            retry_after = response.headers.get("Retry-After")
                            wait_time = float(retry_after) if retry_after else backoff + random.uniform(*JITTER_RANGE)
                            logger.warning(f"Rate limited (429) on JSON {url}. Waiting {wait_time:.2f}s...")
                            await asyncio.sleep(wait_time)
                            backoff = min(backoff * BACKOFF_FACTOR, MAX_BACKOFF_SECONDS)
                        elif response.status in (500, 502, 503, 504):
                            await asyncio.sleep(backoff + random.uniform(*JITTER_RANGE))
                            backoff = min(backoff * BACKOFF_FACTOR, MAX_BACKOFF_SECONDS)
                        else:
                            return None
                except Exception as e:
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(backoff + random.uniform(*JITTER_RANGE))
                        backoff = min(backoff * BACKOFF_FACTOR, MAX_BACKOFF_SECONDS)
                    else:
                        return None
        return None

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

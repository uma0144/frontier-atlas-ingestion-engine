"""
Token Bucket Rate Limiter and Exponential Backoff with Jitter for Anti-429 Resilience.
"""

import asyncio
import random
import time
import logging
from typing import Callable, Any
from functools import wraps
from src.config import INITIAL_BACKOFF_SECONDS, MAX_BACKOFF_SECONDS, BACKOFF_FACTOR, JITTER_RANGE

logger = logging.getLogger("RateLimiter")


class AsyncTokenBucket:
    """Async Token Bucket algorithm for steady-state rate control."""
    def __init__(self, rate_per_second: float = 10.0, capacity: float = 20.0):
        self.rate = rate_per_second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

            if self.tokens < tokens:
                needed = tokens - self.tokens
                wait_time = needed / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
                self.last_update = time.monotonic()
            else:
                self.tokens -= tokens


def with_retry_and_jitter(max_retries: int = 3, initial_delay: float = INITIAL_BACKOFF_SECONDS):
    """Decorator to retry asynchronous LLM calls on 429 / rate limits with jittered exponential backoff."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    err_str = str(e).lower()
                    if "429" in err_str or "rate limit" in err_str or "quota" in err_str:
                        jitter = random.uniform(*JITTER_RANGE)
                        sleep_time = min(delay + jitter, MAX_BACKOFF_SECONDS)
                        logger.warning(f"429 Rate Limit hit in {func.__name__} (attempt {attempt}/{max_retries}). Sleeping for {sleep_time:.2f}s...")
                        await asyncio.sleep(sleep_time)
                        delay *= BACKOFF_FACTOR
                    else:
                        if attempt == max_retries:
                            raise e
                        await asyncio.sleep(delay + random.uniform(0.1, 0.3))
                        delay *= BACKOFF_FACTOR
            return None
        return wrapper
    return decorator

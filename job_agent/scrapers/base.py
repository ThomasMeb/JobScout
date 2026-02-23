import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds: 2, 4, 8


async def retry_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs,
) -> httpx.Response:
    """Execute an HTTP request with retry and exponential backoff.

    Retries on status codes 429, 500, 502, 503, 504 and connection errors.
    Does NOT retry on 400, 401, 403, 404 (raises immediately).
    Max 3 attempts with backoff: 2s, 4s, 8s.
    """
    last_exception = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if method.upper() == "GET":
                resp = await client.get(url, **kwargs)
            elif method.upper() == "POST":
                resp = await client.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if resp.status_code in RETRYABLE_STATUS_CODES:
                delay = BACKOFF_BASE ** attempt
                logger.warning(
                    f"HTTP {resp.status_code} on {method} {url} "
                    f"(attempt {attempt}/{MAX_RETRIES}), retrying in {delay}s"
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(delay)
                    continue
                # Last attempt — raise
                resp.raise_for_status()

            # Non-retryable errors (4xx except 429) — raise immediately
            resp.raise_for_status()
            return resp

        except httpx.HTTPStatusError:
            raise
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout, httpx.ConnectTimeout) as e:
            last_exception = e
            delay = BACKOFF_BASE ** attempt
            logger.warning(
                f"Connection error on {method} {url} "
                f"(attempt {attempt}/{MAX_RETRIES}): {e}, retrying in {delay}s"
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(delay)
                continue
            raise

    # Should not reach here, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError(f"retry_request exhausted {MAX_RETRIES} attempts for {url}")


@dataclass
class RawJob:
    title: str
    company: str
    source: str
    source_url: str
    location: str | None = None
    remote_type: str = "unknown"
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "EUR"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    apply_url: str | None = None
    company_url: str | None = None
    posted_at: datetime | None = None


class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        ...

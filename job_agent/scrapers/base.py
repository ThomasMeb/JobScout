from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


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

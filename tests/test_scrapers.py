"""Tests for scraper base classes, RawJob validation, and parsing utilities."""
import asyncio
from dataclasses import asdict
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from job_agent.scrapers.base import RawJob, retry_request, RETRYABLE_STATUS_CODES


class TestRawJob:
    def test_minimal_raw_job(self):
        job = RawJob(title="Dev Python", company="Acme", source="test", source_url="https://example.com")
        assert job.title == "Dev Python"
        assert job.company == "Acme"
        assert job.location is None
        assert job.remote_type == "unknown"
        assert job.salary_currency == "EUR"
        assert job.tags == []

    def test_full_raw_job(self):
        job = RawJob(
            title="ML Engineer",
            company="DeepCo",
            source="wttj",
            source_url="https://wttj.com/job/1",
            location="Paris, France",
            remote_type="partial",
            salary_min=50000,
            salary_max=70000,
            salary_currency="EUR",
            description="Great job",
            tags=["python", "ml"],
            apply_url="https://wttj.com/apply/1",
            company_url="https://deepco.ai",
            posted_at=datetime(2026, 2, 25),
        )
        d = asdict(job)
        assert d["title"] == "ML Engineer"
        assert d["salary_min"] == 50000
        assert len(d["tags"]) == 2

    def test_raw_job_default_tags(self):
        job1 = RawJob(title="A", company="B", source="test", source_url="#")
        job2 = RawJob(title="C", company="D", source="test", source_url="#")
        # Ensure default list is not shared between instances
        job1.tags.append("python")
        assert job2.tags == []


class TestRetryRequest:
    def test_success_on_first_try(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        resp = asyncio.run(retry_request(mock_client, "GET", "https://example.com"))
        assert resp.status_code == 200
        assert mock_client.get.call_count == 1

    def test_non_retryable_error_raises_immediately(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            asyncio.run(retry_request(mock_client, "GET", "https://example.com"))
        assert mock_client.get.call_count == 1

    def test_retryable_status_codes(self):
        assert 429 in RETRYABLE_STATUS_CODES
        assert 500 in RETRYABLE_STATUS_CODES
        assert 502 in RETRYABLE_STATUS_CODES
        assert 503 in RETRYABLE_STATUS_CODES
        assert 504 in RETRYABLE_STATUS_CODES
        assert 400 not in RETRYABLE_STATUS_CODES
        assert 401 not in RETRYABLE_STATUS_CODES

    def test_unsupported_method(self):
        mock_client = AsyncMock()
        with pytest.raises(ValueError, match="Unsupported HTTP method"):
            asyncio.run(retry_request(mock_client, "DELETE", "https://example.com"))


class TestScraperSourceNames:
    """Verify each scraper has a valid source_name."""

    def test_wttj_source_name(self):
        from job_agent.scrapers.wttj import WTTJScraper
        assert WTTJScraper().source_name == "wttj"

    def test_remoteok_source_name(self):
        from job_agent.scrapers.remoteok import RemoteOKScraper
        assert RemoteOKScraper().source_name == "remoteok"

    def test_adzuna_source_name(self):
        from job_agent.scrapers.adzuna import AdzunaScraper
        assert AdzunaScraper().source_name == "adzuna"

    def test_francetravail_source_name(self):
        from job_agent.scrapers.francetravail import FranceTravailScraper
        assert FranceTravailScraper().source_name == "francetravail"

    def test_jobspy_source_name(self):
        # JobSpy is disabled in production (worker/tasks.py) and pulls in heavy
        # deps (pandas, python-jobspy). Skip the import test if they're absent
        # rather than failing CI.
        pytest.importorskip("pandas")
        pytest.importorskip("jobspy")
        from job_agent.scrapers.jobspy import JobSpyScraper
        assert JobSpyScraper().source_name == "jobspy"

    def test_hellowork_source_name(self):
        from job_agent.scrapers.hellowork import HelloWorkScraper
        assert HelloWorkScraper().source_name == "hellowork"

    def test_apec_source_name(self):
        from job_agent.scrapers.apec import APECScraper
        assert APECScraper().source_name == "apec"

    def test_freework_source_name(self):
        from job_agent.scrapers.freework import FreeWorkScraper
        assert FreeWorkScraper().source_name == "freework"

    def test_welovedevs_source_name(self):
        from job_agent.scrapers.welovedevs import WeLoveDevsScraper
        assert WeLoveDevsScraper().source_name == "welovedevs"


class TestScraperConfig:
    """Test scraper configuration defaults."""

    def test_all_scrapers_in_config(self):
        from worker.config import SCRAPER_CONFIGS
        expected = {"wttj", "remoteok", "adzuna", "francetravail", "jobspy",
                    "hellowork", "apec", "freework", "welovedevs", "indeed_rss"}
        assert expected.issubset(set(SCRAPER_CONFIGS.keys()))

    def test_active_scrapers(self):
        from worker.config import SCRAPER_CONFIGS
        active = [k for k, v in SCRAPER_CONFIGS.items() if v.get("enabled")]
        assert "wttj" in active
        assert "adzuna" in active
        assert "remoteok" in active

    def test_playwright_scrapers_enabled(self):
        from worker.config import SCRAPER_CONFIGS
        active = [k for k, v in SCRAPER_CONFIGS.items() if v.get("enabled")]
        assert "hellowork" in active
        assert "apec" in active
        assert "freework" in active
        assert "welovedevs" in active

    def test_disabled_scrapers(self):
        from worker.config import SCRAPER_CONFIGS
        disabled = [k for k, v in SCRAPER_CONFIGS.items() if not v.get("enabled")]
        assert "indeed_rss" in disabled


class TestAdzunaQuotaGuards:
    """Regression coverage for Adzuna 250-call/month free-tier quota.

    Without these guards we hit the cap in a few hours and stop getting jobs
    from Adzuna for the rest of the month.
    """

    def test_quota_exhausted_error_class_exported(self):
        from job_agent.scrapers.adzuna import AdzunaQuotaExhaustedError
        assert issubclass(AdzunaQuotaExhaustedError, Exception)

    @pytest.mark.asyncio
    async def test_429_raises_quota_exhausted_no_retry(self, monkeypatch):
        """A 429 must abort immediately — every retry burns more quota."""
        from job_agent.scrapers import adzuna as adzuna_mod
        from job_agent.scrapers.adzuna import AdzunaScraper, AdzunaQuotaExhaustedError

        monkeypatch.setattr(adzuna_mod, "ADZUNA_APP_ID", "id")
        monkeypatch.setattr(adzuna_mod, "ADZUNA_APP_KEY", "key")

        call_count = 0

        class FakeResp:
            def __init__(self, status):
                self.status_code = status
                self.text = "rate limit"
            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPStatusError("err", request=None, response=self)
            def json(self):
                return {}

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return None
            async def get(self, *a, **kw):
                nonlocal call_count
                call_count += 1
                return FakeResp(429)

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: FakeClient())

        with pytest.raises(AdzunaQuotaExhaustedError):
            await AdzunaScraper().scrape(["dev"], ["Paris"], {"max_calls_per_cycle": 10})

        # Critically: only ONE call before bailing — not 3 retries.
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_per_cycle_cap_enforced(self, monkeypatch):
        """Cap on calls per cycle must trigger early break."""
        from job_agent.scrapers import adzuna as adzuna_mod
        from job_agent.scrapers.adzuna import AdzunaScraper

        monkeypatch.setattr(adzuna_mod, "ADZUNA_APP_ID", "id")
        monkeypatch.setattr(adzuna_mod, "ADZUNA_APP_KEY", "key")

        call_count = 0

        class FakeResp:
            status_code = 200
            def raise_for_status(self): return None
            def json(self): return {"results": []}

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return None
            async def get(self, *a, **kw):
                nonlocal call_count
                call_count += 1
                return FakeResp()

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: FakeClient())
        # Avoid the 2s sleep between requests in tests
        monkeypatch.setattr(adzuna_mod.asyncio, "sleep", AsyncMock())

        # 5 queries × 5 locations = 25 potential calls, capped at 3
        await AdzunaScraper().scrape(
            ["a", "b", "c", "d", "e"],
            ["P", "L", "M", "N", "O"],
            {"max_calls_per_cycle": 3},
        )
        assert call_count == 3

"""Integration tests for scrapers — real network calls.

Run with: pytest -m integration tests/test_integration_scrapers.py -v
Excluded from default test run (no -m flag needed to skip).
"""
import pytest

from job_agent.scrapers.base import RawJob

pytestmark = pytest.mark.integration

# Default search params for testing
TEST_QUERIES = ["data scientist"]
TEST_LOCATIONS = ["Paris"]
MIN_EXPECTED_FIELDS = {"title", "company", "source", "source_url"}


def _validate_raw_jobs(jobs: list[RawJob], source_name: str):
    """Validate a list of RawJob objects from a scraper."""
    assert isinstance(jobs, list), f"{source_name}: expected list, got {type(jobs)}"
    # Integration tests may return 0 if site is down / CAPTCHA
    for job in jobs:
        assert isinstance(job, RawJob), f"{source_name}: expected RawJob, got {type(job)}"
        assert job.title, f"{source_name}: empty title"
        assert job.company, f"{source_name}: empty company"
        assert job.source == source_name, f"{source_name}: wrong source '{job.source}'"
        assert job.source_url, f"{source_name}: empty source_url"
        assert job.source_url.startswith("http"), f"{source_name}: invalid URL '{job.source_url}'"


# ---------------------------------------------------------------------------
# HTTP scrapers
# ---------------------------------------------------------------------------

class TestWTTJIntegration:
    async def test_scrape_returns_valid_jobs(self):
        from job_agent.scrapers.wttj import WTTJScraper
        scraper = WTTJScraper()
        jobs = await scraper.scrape(TEST_QUERIES, TEST_LOCATIONS, {"max_results_per_query": 5})
        _validate_raw_jobs(jobs, "wttj")
        if jobs:
            assert any(j.location for j in jobs), "Expected at least one job with location"


class TestRemoteOKIntegration:
    async def test_scrape_returns_valid_jobs(self):
        from job_agent.scrapers.remoteok import RemoteOKScraper
        scraper = RemoteOKScraper()
        jobs = await scraper.scrape(TEST_QUERIES, TEST_LOCATIONS, {"filter_tags": ["python"]})
        _validate_raw_jobs(jobs, "remoteok")


class TestAdzunaIntegration:
    async def test_scrape_returns_valid_jobs(self):
        from worker.config import get_settings
        settings = get_settings()
        if not settings.adzuna_app_id:
            pytest.skip("Adzuna API key not configured")
        from job_agent.scrapers.adzuna import AdzunaScraper
        scraper = AdzunaScraper()
        jobs = await scraper.scrape(TEST_QUERIES, TEST_LOCATIONS, {"country": "fr"})
        _validate_raw_jobs(jobs, "adzuna")
        if jobs:
            assert any(j.salary_min for j in jobs), "Expected Adzuna to return salary data"


class TestFranceTravailIntegration:
    async def test_scrape_returns_valid_jobs(self):
        from worker.config import get_settings
        settings = get_settings()
        if not settings.france_travail_client_id:
            pytest.skip("France Travail credentials not configured")
        from job_agent.scrapers.francetravail import FranceTravailScraper
        scraper = FranceTravailScraper()
        jobs = await scraper.scrape(TEST_QUERIES, TEST_LOCATIONS, {"contract_types": "CDI"})
        _validate_raw_jobs(jobs, "francetravail")


class TestJobSpyIntegration:
    async def test_scrape_returns_valid_jobs(self):
        from job_agent.scrapers.jobspy import JobSpyScraper
        scraper = JobSpyScraper()
        jobs = await scraper.scrape(
            TEST_QUERIES, TEST_LOCATIONS,
            {"sites": ["indeed"], "results_per_query": 5, "country": "France"},
        )
        _validate_raw_jobs(jobs, "jobspy_indeed")


# ---------------------------------------------------------------------------
# Playwright scrapers
# ---------------------------------------------------------------------------

class TestHelloWorkIntegration:
    async def test_scrape_returns_valid_jobs(self):
        from job_agent.scrapers.hellowork import HelloWorkScraper
        scraper = HelloWorkScraper()
        jobs = await scraper.scrape(TEST_QUERIES, TEST_LOCATIONS, {"max_pages": 1, "delay_between_requests": 2})
        _validate_raw_jobs(jobs, "hellowork")


class TestAPECIntegration:
    async def test_scrape_returns_valid_jobs(self):
        from job_agent.scrapers.apec import APECScraper
        scraper = APECScraper()
        jobs = await scraper.scrape(TEST_QUERIES, TEST_LOCATIONS, {"max_results": 10, "delay_between_requests": 2})
        _validate_raw_jobs(jobs, "apec")


class TestFreeWorkIntegration:
    async def test_scrape_returns_valid_jobs(self):
        from job_agent.scrapers.freework import FreeWorkScraper
        scraper = FreeWorkScraper()
        jobs = await scraper.scrape(TEST_QUERIES, TEST_LOCATIONS, {"max_pages": 1, "delay_between_requests": 2})
        _validate_raw_jobs(jobs, "freework")


class TestWeLoveDevsIntegration:
    async def test_scrape_returns_valid_jobs(self):
        from job_agent.scrapers.welovedevs import WeLoveDevsScraper
        scraper = WeLoveDevsScraper()
        jobs = await scraper.scrape(TEST_QUERIES, TEST_LOCATIONS, {"max_pages": 1, "delay_between_requests": 2})
        _validate_raw_jobs(jobs, "welovedevs")


# ---------------------------------------------------------------------------
# Cross-scraper validation
# ---------------------------------------------------------------------------

class TestAllScrapersContract:
    """Verify all scrapers in ALL_SCRAPERS conform to the BaseScraper contract."""

    def test_all_scrapers_have_source_name(self):
        from worker.tasks import ALL_SCRAPERS
        for key, scraper in ALL_SCRAPERS:
            assert hasattr(scraper, "source_name"), f"{key} missing source_name"
            assert scraper.source_name == key, f"{key}: source_name is '{scraper.source_name}'"

    def test_all_scrapers_have_scrape_method(self):
        from worker.tasks import ALL_SCRAPERS
        for key, scraper in ALL_SCRAPERS:
            assert hasattr(scraper, "scrape"), f"{key} missing scrape method"
            assert callable(scraper.scrape), f"{key}.scrape is not callable"

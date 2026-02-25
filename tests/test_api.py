"""Integration tests for FastAPI endpoints with mocked Supabase."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_settings():
    """Mock settings to avoid needing real env vars."""
    with patch("app.config.get_settings") as mock:
        settings = MagicMock()
        settings.supabase_url = "https://fake.supabase.co"
        settings.supabase_anon_key = "fake-anon-key"
        settings.supabase_service_role_key = "fake-service-key"
        settings.supabase_jwt_secret = "fake-jwt-secret"
        settings.cors_origins = "http://localhost:3000"
        settings.sentry_dsn = ""
        settings.environment = "test"
        mock.return_value = settings
        yield settings


@pytest.fixture
def client(mock_settings):
    """Create test client with mocked dependencies."""
    from app.main import app
    from app.auth import get_current_user_id, get_rls_supabase

    mock_sb = MagicMock()

    app.dependency_overrides[get_current_user_id] = lambda: "test-user-uuid"
    app.dependency_overrides[get_rls_supabase] = lambda: mock_sb

    yield TestClient(app), mock_sb

    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health(self, client):
        tc, _ = client
        resp = tc.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestProfileEndpoints:
    def test_get_profile(self, client):
        tc, mock_sb = client
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "test-user-uuid",
                "name": "Thomas",
                "monthly_budget_usd": 5.0,
                "min_score_notify": 70,
                "onboarding_completed": True,
            }]
        )
        resp = tc.get("/api/profile/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Thomas"

    def test_get_profile_not_found(self, client):
        tc, mock_sb = client
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        resp = tc.get("/api/profile/")
        assert resp.status_code == 404


class TestJobEndpoints:
    def test_list_jobs_empty(self, client):
        tc, mock_sb = client
        mock_result = MagicMock(data=[], count=0)
        (mock_sb.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .range.return_value
            .execute.return_value) = mock_result
        resp = tc.get("/api/jobs/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["jobs"] == []

    def test_min_score_validation(self, client):
        tc, _ = client
        resp = tc.get("/api/jobs/?min_score=-5")
        assert resp.status_code == 422

    def test_min_score_too_high(self, client):
        tc, _ = client
        resp = tc.get("/api/jobs/?min_score=150")
        assert resp.status_code == 422

    def test_invalid_status_filter(self, client):
        tc, _ = client
        resp = tc.get("/api/jobs/?status=invalid")
        assert resp.status_code == 422

    def test_valid_status_filter(self, client):
        tc, mock_sb = client
        mock_result = MagicMock(data=[], count=0)
        (mock_sb.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .eq.return_value
            .range.return_value
            .execute.return_value) = mock_result
        resp = tc.get("/api/jobs/?status=interested")
        assert resp.status_code == 200

    def test_feedback_invalid_status(self, client):
        tc, _ = client
        resp = tc.patch("/api/jobs/1/feedback", json={"status": "bogus"})
        assert resp.status_code == 422

    def test_feedback_valid_status(self, client):
        tc, mock_sb = client
        # Mock update
        mock_sb.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1}]
        )
        # Mock get_job refetch
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": 1,
                "raw_job_id": 10,
                "match_score": 75,
                "match_reasoning": "Good",
                "match_keywords": "[]",
                "missing_keywords": "[]",
                "match_priority": "high",
                "status": "interested",
                "user_notes": None,
                "scored_at": None,
                "raw_jobs": {
                    "title": "Dev Python",
                    "company": "Acme",
                    "location": "Paris",
                    "remote_type": "hybrid",
                    "salary_min": None,
                    "salary_max": None,
                    "salary_currency": "EUR",
                    "source": "wttj",
                    "source_url": "https://example.com",
                    "apply_url": None,
                    "tags": "[]",
                    "posted_at": None,
                },
            }]
        )
        resp = tc.patch("/api/jobs/1/feedback", json={"status": "interested"})
        assert resp.status_code == 200


class TestExportCSV:
    def test_export_csv_empty(self, client):
        tc, mock_sb = client
        (mock_sb.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .limit.return_value
            .execute.return_value) = MagicMock(data=[])
        resp = tc.get("/api/jobs/export/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "jobscout-export.csv" in resp.headers["content-disposition"]
        lines = resp.text.strip().split("\n")
        assert len(lines) == 1  # header only

    def test_export_csv_with_data(self, client):
        tc, mock_sb = client
        (mock_sb.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .limit.return_value
            .execute.return_value) = MagicMock(data=[{
                "match_score": 80,
                "match_priority": "high",
                "match_keywords": '["python"]',
                "missing_keywords": "[]",
                "match_reasoning": "Good match",
                "status": "new",
                "user_notes": None,
                "scored_at": "2026-02-23",
                "raw_jobs": {
                    "title": "Dev Python",
                    "company": "Acme",
                    "location": "Paris",
                    "remote_type": "hybrid",
                    "salary_min": 45000,
                    "salary_max": 55000,
                    "salary_currency": "EUR",
                    "source": "wttj",
                    "source_url": "https://example.com",
                    "apply_url": None,
                },
            }])
        resp = tc.get("/api/jobs/export/csv")
        assert resp.status_code == 200
        lines = resp.text.strip().split("\n")
        assert len(lines) == 2  # header + 1 row
        assert "Dev Python" in lines[1]
        assert "Acme" in lines[1]

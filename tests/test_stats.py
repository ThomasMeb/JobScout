"""Tests for stats and scrape runs endpoints."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_settings():
    with patch("app.config.get_settings") as mock:
        settings = MagicMock()
        settings.supabase_url = "https://fake.supabase.co"
        settings.supabase_anon_key = "fake-anon-key"
        settings.supabase_service_role_key = "fake-service-key"
        settings.supabase_jwt_secret = "fake-jwt-secret"
        settings.cors_origins = "http://localhost:3000"
        settings.sentry_dsn = ""
        settings.environment = "test"
        settings.stripe_secret_key = ""
        settings.stripe_webhook_secret = ""
        settings.stripe_pro_price_id = ""
        settings.frontend_url = "http://localhost:3000"
        mock.return_value = settings
        yield settings


@pytest.fixture
def client(mock_settings):
    from app.main import app
    from app.auth import get_current_user_id, get_rls_supabase

    mock_sb = MagicMock()
    app.dependency_overrides[get_current_user_id] = lambda: "test-user-uuid"
    app.dependency_overrides[get_rls_supabase] = lambda: mock_sb
    yield TestClient(app), mock_sb
    app.dependency_overrides.clear()


class TestStatsEndpoint:
    def test_stats_empty(self, client):
        tc, mock_sb = client
        # user_jobs query
        jobs_result = MagicMock(data=[], count=0)
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = jobs_result
        # llm_usage query
        cost_result = MagicMock(data=[])
        mock_sb.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = cost_result

        resp = tc.get("/api/stats/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_jobs"] == 0
        assert data["new_jobs"] == 0
        assert data["avg_score"] is None

    def test_stats_with_jobs(self, client):
        tc, mock_sb = client

        jobs_result = MagicMock(
            data=[
                {"status": "new", "match_score": 80},
                {"status": "interested", "match_score": 90},
                {"status": "rejected", "match_score": 40},
            ],
            count=3,
        )
        cost_result = MagicMock(data=[{"cost_usd": 0.05}])
        budget_result = MagicMock(data=[{"monthly_budget_usd": 5.0}])

        # Use side_effect to return different results for sequential calls
        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "user_jobs":
                mock_table.select.return_value.eq.return_value.execute.return_value = jobs_result
            elif name == "llm_usage":
                mock_table.select.return_value.eq.return_value.gte.return_value.execute.return_value = cost_result
            elif name == "profiles":
                mock_table.select.return_value.eq.return_value.execute.return_value = budget_result
            return mock_table

        mock_sb.table.side_effect = table_side_effect

        resp = tc.get("/api/stats/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_jobs"] == 3
        assert data["new_jobs"] == 1
        assert data["interested"] == 1
        assert data["rejected"] == 1


class TestChartsEndpoint:
    def test_charts_empty(self, client):
        tc, mock_sb = client
        result = MagicMock(data=[])
        (mock_sb.table.return_value
         .select.return_value
         .eq.return_value
         .not_.return_value
         .is_.return_value
         .order.return_value
         .limit.return_value
         .execute.return_value) = result
        resp = tc.get("/api/stats/charts")
        assert resp.status_code == 200
        data = resp.json()
        assert "score_buckets" in data
        assert "daily_jobs" in data

    def test_charts_with_data(self, client):
        tc, mock_sb = client
        result = MagicMock(data=[
            {"match_score": 85, "scored_at": "2026-02-25T10:00:00"},
            {"match_score": 72, "scored_at": "2026-02-25T11:00:00"},
            {"match_score": 45, "scored_at": "2026-02-24T10:00:00"},
        ])
        # The charts endpoint chains: .not_.is_() — MagicMock handles this auto
        # We just need any .execute() in the chain to return our result
        mock_sb.configure_mock(**{
            "table.return_value.select.return_value.eq.return_value"
            ".not_.return_value.is_.return_value"
            ".order.return_value.limit.return_value"
            ".execute.return_value": result,
        })
        resp = tc.get("/api/stats/charts")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["score_buckets"]) == 10
        assert isinstance(data["daily_jobs"], list)


class TestScrapeRunsEndpoint:
    def test_list_scrape_runs(self, client):
        tc, mock_sb = client
        runs = MagicMock(data=[
            {"id": 1, "source": "wttj", "status": "success", "jobs_found": 50,
             "jobs_new": 10, "error_message": None,
             "started_at": "2026-02-25T08:00:00", "finished_at": "2026-02-25T08:05:00"},
        ])
        (mock_sb.table.return_value
         .select.return_value
         .order.return_value
         .limit.return_value
         .execute.return_value) = runs
        resp = tc.get("/api/scrape-runs/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["source"] == "wttj"

    def test_scrape_runs_custom_limit(self, client):
        tc, mock_sb = client
        runs = MagicMock(data=[])
        (mock_sb.table.return_value
         .select.return_value
         .order.return_value
         .limit.return_value
         .execute.return_value) = runs
        resp = tc.get("/api/scrape-runs/?limit=5")
        assert resp.status_code == 200

    def test_scrape_runs_invalid_limit(self, client):
        tc, _ = client
        resp = tc.get("/api/scrape-runs/?limit=0")
        # Global RequestValidationError handler rewrites 422 → 400
        assert resp.status_code == 400

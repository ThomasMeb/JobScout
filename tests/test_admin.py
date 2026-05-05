"""Tests for admin endpoints — access control and data retrieval."""
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
def admin_client(mock_settings):
    """Client where user is admin — override _require_admin dependency."""
    from app.main import app
    from app.routers.admin import _require_admin

    app.dependency_overrides[_require_admin] = lambda: "admin-user-uuid"

    mock_admin_sb = MagicMock()
    with patch("app.routers.admin._get_admin_sb", return_value=mock_admin_sb):
        yield TestClient(app), mock_admin_sb

    app.dependency_overrides.clear()


@pytest.fixture
def non_admin_client(mock_settings):
    """Client where user is NOT admin — mock DB to return is_admin=False."""
    from app.main import app
    from app.auth import get_current_user_id

    app.dependency_overrides[get_current_user_id] = lambda: "regular-user-uuid"

    mock_admin_sb = MagicMock()
    admin_check_result = MagicMock()
    admin_check_result.data = {"is_admin": False}
    mock_admin_sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = admin_check_result

    with patch("app.routers.admin._get_admin_sb", return_value=mock_admin_sb):
        yield TestClient(app), mock_admin_sb

    app.dependency_overrides.clear()


class TestAdminAccess:
    def test_non_admin_users_rejected(self, non_admin_client):
        tc, _ = non_admin_client
        resp = tc.get("/api/admin/users")
        assert resp.status_code == 403
        assert "administrateur" in resp.json()["detail"].lower()

    def test_non_admin_scrapers_rejected(self, non_admin_client):
        tc, _ = non_admin_client
        resp = tc.get("/api/admin/scrapers")
        assert resp.status_code == 403

    def test_non_admin_metrics_rejected(self, non_admin_client):
        tc, _ = non_admin_client
        resp = tc.get("/api/admin/metrics")
        assert resp.status_code == 403


class TestAdminUsers:
    def test_list_users(self, admin_client):
        tc, mock_sb = admin_client
        profiles_result = MagicMock()
        profiles_result.data = [
            {"id": "user-1", "name": "Alice", "notification_email": "a@test.com",
             "plan": "free", "onboarding_completed": True, "created_at": "2026-01-01", "updated_at": "2026-02-01"},
        ]
        jobs_count_result = MagicMock()
        jobs_count_result.count = 42

        mock_sb.table.return_value.select.return_value.order.return_value.execute.return_value = profiles_result
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = jobs_count_result

        resp = tc.get("/api/admin/users")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1


class TestAdminMetrics:
    def test_metrics(self, admin_client):
        tc, mock_sb = admin_client
        count_result = MagicMock()
        count_result.count = 10
        mock_sb.table.return_value.select.return_value.execute.return_value = count_result
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = count_result
        # heartbeat
        hb_result = MagicMock()
        hb_result.data = {"status": "running", "cycle_count": 5, "last_cycle_at": "2026-02-25T10:00:00"}
        mock_sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = hb_result

        resp = tc.get("/api/admin/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "worker_status" in data


class TestAdminScrapers:
    def test_scraper_health(self, admin_client):
        tc, mock_sb = admin_client
        runs_result = MagicMock()
        runs_result.data = [
            {"source": "wttj", "status": "success", "jobs_found": 50, "jobs_new": 10,
             "error_message": None, "started_at": "2026-02-25T08:00:00", "finished_at": "2026-02-25T08:05:00"},
            {"source": "wttj", "status": "error", "jobs_found": 0, "jobs_new": 0,
             "error_message": "Timeout", "started_at": "2026-02-24T08:00:00", "finished_at": None},
            {"source": "adzuna", "status": "success", "jobs_found": 30, "jobs_new": 5,
             "error_message": None, "started_at": "2026-02-25T08:00:00", "finished_at": "2026-02-25T08:02:00"},
        ]
        mock_sb.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = runs_result

        resp = tc.get("/api/admin/scrapers")
        assert resp.status_code == 200
        data = resp.json()
        scrapers = data["scrapers"]
        assert len(scrapers) == 2

        wttj = next(s for s in scrapers if s["source"] == "wttj")
        assert wttj["total_runs"] == 2
        assert wttj["success_runs"] == 1
        assert wttj["success_rate"] == 50
        assert wttj["last_error"] == "Timeout"

"""Tests for billing endpoints — status, checkout, portal, webhook."""
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
        settings.stripe_secret_key = "sk_test_fake"
        settings.stripe_webhook_secret = "whsec_test_fake"
        settings.stripe_pro_price_id = "price_test_123"
        settings.frontend_url = "http://localhost:3000"
        mock.return_value = settings
        yield settings


@pytest.fixture
def client(mock_settings):
    from app.main import app
    from app.auth import get_current_user_id

    app.dependency_overrides[get_current_user_id] = lambda: "test-user-uuid"
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestBillingStatus:
    def test_billing_status_free(self, client):
        mock_sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {
            "plan": "free", "stripe_customer_id": None,
            "stripe_subscription_id": None, "plan_expires_at": None, "trial_started_at": None,
        }
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        with patch("app.routers.billing._get_admin_sb", return_value=mock_sb):
            resp = client.get("/api/billing/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "free"
        assert data["has_subscription"] is False

    def test_billing_status_pro(self, client):
        mock_sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {
            "plan": "pro", "stripe_customer_id": "cus_123",
            "stripe_subscription_id": "sub_456", "plan_expires_at": None, "trial_started_at": None,
        }
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        with patch("app.routers.billing._get_admin_sb", return_value=mock_sb):
            resp = client.get("/api/billing/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "pro"
        assert data["has_subscription"] is True


class TestBillingCheckout:
    def test_checkout_creates_session(self, client):
        mock_sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {"stripe_customer_id": "cus_existing", "notification_email": "t@test.com", "name": "Test"}
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("app.routers.billing._get_admin_sb", return_value=mock_sb), \
             patch("app.routers.billing._get_stripe", return_value=mock_stripe):
            resp = client.post("/api/billing/checkout")
        assert resp.status_code == 200
        assert resp.json()["checkout_url"] == "https://checkout.stripe.com/test"

    def test_checkout_not_configured(self, client, mock_settings):
        """Checkout returns 503 when stripe key is empty."""
        mock_settings.stripe_secret_key = ""
        from fastapi import HTTPException
        with patch("app.routers.billing._get_stripe",
                   side_effect=HTTPException(status_code=503, detail="Billing not configured")):
            resp = client.post("/api/billing/checkout")
        assert resp.status_code == 503


class TestBillingPortal:
    def test_portal_no_customer(self, client):
        mock_sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {"stripe_customer_id": None}
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        mock_stripe = MagicMock()
        with patch("app.routers.billing._get_admin_sb", return_value=mock_sb), \
             patch("app.routers.billing._get_stripe", return_value=mock_stripe):
            resp = client.post("/api/billing/portal")
        assert resp.status_code == 400
        assert "facturation" in resp.json()["detail"].lower()


class TestBillingWebhook:
    def test_webhook_no_secret(self, mock_settings):
        """Webhook returns 503 when secret is not configured."""
        mock_settings.stripe_webhook_secret = ""

        from app.main import app

        with patch("app.routers.billing.get_settings", return_value=mock_settings):
            tc = TestClient(app)
            resp = tc.post("/api/billing/webhook", content=b'{}',
                          headers={"stripe-signature": "fake"})
        assert resp.status_code == 503

    def test_webhook_invalid_signature(self, mock_settings):
        """Webhook rejects invalid signatures with 400."""
        mock_settings.stripe_webhook_secret = "whsec_test"
        mock_settings.stripe_secret_key = "sk_test"

        from app.main import app

        with patch("app.routers.billing.get_settings", return_value=mock_settings), \
             patch("app.routers.billing.stripe.Webhook.construct_event",
                   side_effect=ValueError("Invalid payload")):
            tc = TestClient(app)
            resp = tc.post("/api/billing/webhook", content=b'{"type":"test"}',
                          headers={"stripe-signature": "t=123,v1=bad"})
        assert resp.status_code == 400

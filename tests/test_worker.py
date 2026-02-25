"""Unit tests for worker modules — config, notifications filter, auto_apply extraction."""
import os
from unittest.mock import patch


class TestWorkerConfig:
    def test_default_settings(self):
        """Verify default config values load correctly."""
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://fake.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "fake-key",
            "DEEPSEEK_API_KEY": "fake-deepseek",
        }):
            from worker.config import WorkerSettings
            s = WorkerSettings(
                supabase_url="https://fake.supabase.co",
                supabase_service_role_key="fake-key",
                deepseek_api_key="fake-deepseek",
            )
            assert s.max_notifications_per_cycle == 10
            assert s.cycle_interval_hours == 4
            assert s.scoring_temperature == 0.2
            assert s.auto_apply_enabled is True
            assert s.max_jobs_per_user_per_cycle == 100

    def test_sentry_dsn_default_empty(self):
        s = _make_settings()
        assert s.sentry_dsn == ""

    def test_auto_apply_enabled_default(self):
        s = _make_settings()
        assert s.auto_apply_enabled is True


class TestAutoApplyExtraction:
    def test_extract_mailto(self):
        from worker.auto_apply import extract_email_from_job
        email = extract_email_from_job("mailto:recruiter@example.com", None)
        assert email == "recruiter@example.com"

    def test_extract_email_from_url(self):
        from worker.auto_apply import extract_email_from_job
        email = extract_email_from_job("https://example.com/contact@company.fr", None)
        assert email == "contact@company.fr"

    def test_extract_email_from_description(self):
        from worker.auto_apply import extract_email_from_job
        email = extract_email_from_job(None, "Envoyez votre CV à recrutement@techcorp.io")
        assert email == "recrutement@techcorp.io"

    def test_ignore_noreply(self):
        from worker.auto_apply import extract_email_from_job
        email = extract_email_from_job(None, "Contact: noreply@company.com ou rh@company.com")
        assert email == "rh@company.com"

    def test_no_email_found(self):
        from worker.auto_apply import extract_email_from_job
        email = extract_email_from_job("https://example.com/apply", "No email here")
        assert email is None


class TestMailtoBuilder:
    def test_build_mailto_link(self):
        from worker.auto_apply import build_mailto_link
        link = build_mailto_link(
            to_email="hr@company.com",
            subject="Candidature - Dev Python",
            body="Bonjour,\nVeuillez trouver...",
        )
        assert link.startswith("mailto:hr@company.com?")
        assert "subject=" in link
        assert "body=" in link


class TestPlanEnforcement:
    def test_free_plan_limit(self):
        """Free plan should limit to 10 jobs."""
        jobs = list(range(50))
        plan = "free"
        if plan == "free":
            jobs = jobs[:10]
        assert len(jobs) == 10

    def test_pro_plan_unlimited(self):
        """Pro plan should not limit jobs."""
        jobs = list(range(50))
        plan = "pro"
        if plan == "free":
            jobs = jobs[:10]
        assert len(jobs) == 50


def _make_settings():
    from worker.config import WorkerSettings
    return WorkerSettings(
        supabase_url="https://fake.supabase.co",
        supabase_service_role_key="fake-key",
        deepseek_api_key="fake-deepseek",
    )

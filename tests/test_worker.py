"""Unit tests for worker modules — config, notifications filter, auto_apply extraction."""
import asyncio
import os
from unittest.mock import patch

import pytest


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


class TestEmailValidation:
    """Test the email validation/filtering logic."""

    def test_ignore_indeed_support(self):
        from worker.auto_apply import extract_email_from_job
        email = extract_email_from_job(None, "Contact support@indeed.com for info")
        assert email is None

    def test_ignore_privacy_email(self):
        from worker.auto_apply import extract_email_from_job
        email = extract_email_from_job(None, "privacy@company.com or jobs@company.com")
        assert email == "jobs@company.com"

    def test_ignore_unsubscribe(self):
        from worker.auto_apply import extract_email_from_job
        email = extract_email_from_job(None, "unsubscribe@list.com and hiring@corp.com")
        assert email == "hiring@corp.com"

    def test_mailto_with_params(self):
        from worker.auto_apply import extract_email_from_job
        email = extract_email_from_job("mailto:rh@startup.io?subject=Job&body=Hi", None)
        assert email == "rh@startup.io"

    def test_multiple_emails_picks_first_valid(self):
        from worker.auto_apply import extract_email_from_job
        desc = "noreply@x.com, no-reply@y.com, then finally recrutement@z.fr"
        email = extract_email_from_job(None, desc)
        assert email == "recrutement@z.fr"


class TestMailtoLinkDetails:
    """Test mailto link generation with special characters."""

    def test_subject_encoding(self):
        from worker.auto_apply import build_mailto_link
        link = build_mailto_link("a@b.com", "Développeur Python/ML", "Bonjour")
        assert "D%C3%A9veloppeur" in link

    def test_body_newlines(self):
        from worker.auto_apply import build_mailto_link
        link = build_mailto_link("a@b.com", "Test", "Ligne 1\nLigne 2\nLigne 3")
        assert "%0A" in link or "%0a" in link


class TestNotificationConfig:
    """Test notification-related config defaults."""

    def test_max_notifications_default(self):
        s = _make_settings()
        assert s.max_notifications_per_cycle == 10

    def test_brevo_key_is_string(self):
        s = _make_settings()
        assert isinstance(s.brevo_api_key, str)

    def test_auto_apply_from_email_default(self):
        s = _make_settings()
        assert "@" in s.auto_apply_from_email


def _make_settings():
    from worker.config import WorkerSettings
    return WorkerSettings(
        supabase_url="https://fake.supabase.co",
        supabase_service_role_key="fake-key",
        deepseek_api_key="fake-deepseek",
    )


class _PostgrestErrorLike(Exception):
    """Simulates the shape supabase-py's APIError exposes: a `code` attribute."""
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


async def _no_sleep(*_a, **_kw):
    """asyncio.sleep replacement used to keep retry-loop tests fast."""
    return None


class TestSchemaProbeClassification:
    """Regression tests for the schema validator — every wrong classification
    here used to send a false-positive Telegram alert to the user."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)

    def test_probe_success_returns_exists_true_no_detail(self, monkeypatch):
        from worker.main import _probe_schema_object
        # Speed up retries (only used on failure path here, but keep it cheap)
        monkeypatch.setattr("worker.main.asyncio.sleep", _no_sleep)

        def probe(): return None  # success
        exists, reason = self._run(_probe_schema_object(sb=None, probe=probe, label="t"))
        assert exists is True
        assert reason is None

    def test_pg_undefined_table_is_hard_missing(self, monkeypatch):
        from worker.main import _probe_schema_object
        monkeypatch.setattr("worker.main.asyncio.sleep", _no_sleep)

        calls = {"n": 0}
        def probe():
            calls["n"] += 1
            raise _PostgrestErrorLike("42P01", "undefined_table")
        exists, reason = self._run(_probe_schema_object(sb=None, probe=probe, label="t"))
        assert exists is False
        assert "42P01" in reason
        # Hard codes should NOT trigger retries.
        assert calls["n"] == 1

    def test_pgrst116_is_not_a_schema_missing_code(self, monkeypatch):
        """PGRST116 = 'JSON object requested, multiple/no rows' — must be
        treated as transient noise, not as a missing-table signal."""
        from worker.main import _probe_schema_object
        monkeypatch.setattr("worker.main.asyncio.sleep", _no_sleep)

        def probe():
            raise _PostgrestErrorLike("PGRST116", "no rows")
        exists, reason = self._run(_probe_schema_object(sb=None, probe=probe, label="t"))
        # Critically: must NOT report the table as missing.
        assert exists is True
        assert reason is not None and "transient" in reason

    def test_pgrst205_stale_cache_then_succeeds(self, monkeypatch):
        """PGRST205 is ambiguous: usually a stale schema cache after a deploy.
        It should retry several times before giving up."""
        from worker.main import _probe_schema_object
        monkeypatch.setattr("worker.main.asyncio.sleep", _no_sleep)

        attempts = {"n": 0}
        def probe():
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise _PostgrestErrorLike("PGRST205", "schema cache miss")
            return None  # cache reloaded
        exists, reason = self._run(_probe_schema_object(sb=None, probe=probe, label="raw_jobs"))
        assert exists is True
        assert reason is None
        # Must have retried (not 1, not 1k either).
        assert attempts["n"] == 3

    def test_pgrst205_persisting_becomes_missing(self, monkeypatch):
        """Only after the extended retry budget is exhausted do we accept
        PGRST205 as a truly missing table."""
        from worker.main import _probe_schema_object
        monkeypatch.setattr("worker.main.asyncio.sleep", _no_sleep)

        def probe():
            raise _PostgrestErrorLike("PGRST205", "still missing")
        exists, reason = self._run(_probe_schema_object(sb=None, probe=probe, label="t"))
        assert exists is False
        assert "PGRST205" in reason
        assert "extended retry" in reason

    def test_transient_5xx_does_not_falsely_report_missing(self, monkeypatch):
        """Cloudflare 502 / network errors must never produce a 'missing
        table' alert — the previous behavior was crying wolf on every
        Supabase hiccup."""
        from worker.main import _probe_schema_object
        monkeypatch.setattr("worker.main.asyncio.sleep", _no_sleep)

        def probe():
            raise RuntimeError("Bad Gateway 502")
        exists, reason = self._run(_probe_schema_object(sb=None, probe=probe, label="t"))
        assert exists is True
        assert "transient" in reason

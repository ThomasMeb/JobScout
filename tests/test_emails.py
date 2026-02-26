"""Tests for transactional email templates and logic."""
from unittest.mock import MagicMock, patch


class TestWelcomeEmail:
    def test_welcome_html_contains_name(self):
        from worker.emails import _build_welcome_html
        html = _build_welcome_html("Thomas")
        assert "Thomas" in html
        assert "Bienvenue" in html

    def test_welcome_html_contains_features(self):
        from worker.emails import _build_welcome_html
        html = _build_welcome_html("Alice")
        assert "9 sources" in html
        assert "Scoring IA" in html
        assert "Candidature auto" in html

    def test_welcome_skips_if_already_sent(self):
        import asyncio
        from worker.emails import send_welcome_email

        mock_sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {
            "name": "Bob",
            "notification_email": "bob@test.com",
            "welcome_email_sent_at": "2026-02-25T10:00:00Z",
        }
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        with patch("worker.emails.get_supabase", return_value=mock_sb):
            result = asyncio.run(send_welcome_email("user-123"))
        assert result is False

    def test_welcome_skips_if_no_email(self):
        import asyncio
        from worker.emails import send_welcome_email

        mock_sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {
            "name": "NoEmail",
            "notification_email": None,
            "welcome_email_sent_at": None,
        }
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        with patch("worker.emails.get_supabase", return_value=mock_sb):
            result = asyncio.run(send_welcome_email("user-456"))
        assert result is False


class TestWeeklyDigest:
    def test_digest_html_contains_jobs(self):
        from worker.emails import _build_weekly_digest_html
        jobs = [
            {"match_score": 92, "raw_jobs": {"title": "ML Engineer", "company": "Acme", "location": "Paris", "source_url": "https://example.com/1"}},
            {"match_score": 85, "raw_jobs": {"title": "Data Scientist", "company": "BigCo", "location": "Lyon", "source_url": "https://example.com/2"}},
        ]
        html = _build_weekly_digest_html("Thomas", jobs)
        assert "Thomas" in html
        assert "ML Engineer" in html
        assert "Data Scientist" in html
        assert "Acme" in html

    def test_digest_html_max_5_jobs(self):
        from worker.emails import _build_weekly_digest_html
        jobs = [
            {"match_score": 90 - i, "raw_jobs": {"title": f"Job {i}", "company": f"Co {i}", "location": "Paris", "source_url": f"https://example.com/{i}"}}
            for i in range(10)
        ]
        html = _build_weekly_digest_html("Alice", jobs)
        assert "Job 0" in html
        assert "Job 4" in html
        assert "Job 5" not in html

    def test_digest_skips_if_sent_recently(self):
        import asyncio
        from worker.emails import send_weekly_digest
        from datetime import datetime, timezone

        mock_sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {
            "name": "Test",
            "notification_email": "test@test.com",
            "last_digest_at": datetime.now(timezone.utc).isoformat(),
            "min_score_notify": 70,
        }
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        with patch("worker.emails.get_supabase", return_value=mock_sb):
            result = asyncio.run(send_weekly_digest("user-789"))
        assert result is False


class TestApplicationConfirmation:
    def test_confirmation_html(self):
        from worker.emails import _build_confirmation_html
        html = _build_confirmation_html("Thomas", "ML Engineer", "Acme Corp", "rh@acme.com")
        assert "Thomas" in html
        assert "ML Engineer" in html
        assert "Acme Corp" in html
        assert "rh@acme.com" in html
        assert "envoyée" in html.lower()


class TestScrapeDuration:
    def test_log_scrape_finish_with_duration(self):
        from worker.tasks import _log_scrape_finish

        mock_sb = MagicMock()
        _log_scrape_finish(mock_sb, 42, 10, 3, "success", duration=15.7)

        call_args = mock_sb.table.return_value.update.call_args
        row = call_args[0][0]
        assert row["duration_seconds"] == 15.7
        assert row["jobs_found"] == 10
        assert row["jobs_new"] == 3

    def test_log_scrape_finish_without_duration(self):
        from worker.tasks import _log_scrape_finish

        mock_sb = MagicMock()
        _log_scrape_finish(mock_sb, 42, 5, 1, "error", error="timeout")

        call_args = mock_sb.table.return_value.update.call_args
        row = call_args[0][0]
        assert "duration_seconds" not in row
        assert row["error_message"] == "timeout"

    def test_log_scrape_finish_none_run_id(self):
        from worker.tasks import _log_scrape_finish

        mock_sb = MagicMock()
        _log_scrape_finish(mock_sb, None, 0, 0, "error")
        mock_sb.table.assert_not_called()

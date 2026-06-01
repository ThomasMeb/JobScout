"""Tests for the notification pipeline diagnostic tool."""
from unittest.mock import MagicMock


class TestAgeFormatting:
    def test_age_never(self):
        from worker.diagnose import _age
        assert _age(None) == "never"

    def test_age_minutes(self):
        from datetime import datetime, timezone, timedelta
        from worker.diagnose import _age
        iso = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        assert "min ago" in _age(iso)

    def test_age_hours(self):
        from datetime import datetime, timezone, timedelta
        from worker.diagnose import _age
        iso = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        assert "h ago" in _age(iso)

    def test_age_days(self):
        from datetime import datetime, timezone, timedelta
        from worker.diagnose import _age
        iso = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        assert "days ago" in _age(iso)

    def test_age_garbage_returns_input(self):
        from worker.diagnose import _age
        assert _age("not-a-date") == "not-a-date"


class TestDiagnoseChecksHandleEmptyData:
    """The diagnostic must never crash on missing rows — it has to run
    against a half-broken production DB and still report."""

    def test_check_worker_no_heartbeat(self, capsys):
        from worker.diagnose import check_worker
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(data=None)
        check_worker(sb)
        out = capsys.readouterr().out
        assert "NEVER run" in out

    def test_check_scraping_no_runs(self, capsys):
        from worker.diagnose import check_scraping
        sb = MagicMock()
        sb.table.return_value.select.return_value.gte.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        check_scraping(sb)
        out = capsys.readouterr().out
        assert "No scrape runs" in out

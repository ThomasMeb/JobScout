"""Tests for feedback loop analysis logic."""
import json
from unittest.mock import MagicMock, patch


class TestKeywordAnalysis:
    def test_preferred_keywords(self):
        """Keywords appearing mostly in interested jobs should be preferred."""
        from worker.feedback_loop import analyze_keyword_preferences

        interested_data = [
            {"match_keywords": json.dumps(["python", "ml", "fastapi"]), "raw_jobs": {"company": "A", "location": "Paris", "source": "wttj"}},
            {"match_keywords": json.dumps(["python", "ml"]), "raw_jobs": {"company": "B", "location": "Paris", "source": "wttj"}},
            {"match_keywords": json.dumps(["python", "django"]), "raw_jobs": {"company": "C", "location": "Lyon", "source": "adzuna"}},
        ]
        rejected_data = [
            {"match_keywords": json.dumps(["java", "spring"]), "raw_jobs": {"company": "D", "location": "Toulouse", "source": "wttj"}},
            {"match_keywords": json.dumps(["java", "spring"]), "raw_jobs": {"company": "E", "location": "Toulouse", "source": "adzuna"}},
        ]

        mock_sb = MagicMock()
        interested_result = MagicMock()
        interested_result.data = interested_data
        rejected_result = MagicMock()
        rejected_result.data = rejected_data

        mock_sb.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value = interested_result
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = rejected_result

        with patch("worker.feedback_loop.get_supabase", return_value=mock_sb):
            result = analyze_keyword_preferences("test-user")

        preferred_kws = [kw for kw, _ in result["preferred_keywords"]]
        avoided_kws = [kw for kw, _ in result["avoided_keywords"]]
        assert "python" in preferred_kws
        assert "java" in avoided_kws

    def test_empty_feedback(self):
        from worker.feedback_loop import analyze_keyword_preferences

        mock_sb = MagicMock()
        empty = MagicMock()
        empty.data = []
        mock_sb.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value = empty
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = empty

        with patch("worker.feedback_loop.get_supabase", return_value=mock_sb):
            result = analyze_keyword_preferences("test-user")

        assert result["preferred_keywords"] == []
        assert result["avoided_keywords"] == []


class TestPreferenceSummary:
    def test_not_enough_feedback(self):
        from worker.feedback_loop import generate_preference_summary

        mock_sb = MagicMock()
        count_result = MagicMock()
        count_result.count = 2
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = count_result

        with patch("worker.feedback_loop.get_supabase", return_value=mock_sb):
            summary = generate_preference_summary("test-user")

        assert summary == ""

    def test_company_preferences(self):
        """Companies from interested jobs should appear in preferences."""
        from worker.feedback_loop import analyze_keyword_preferences

        interested_data = [
            {"match_keywords": "[]", "raw_jobs": {"company": "Google", "location": "Paris", "source": "wttj"}},
            {"match_keywords": "[]", "raw_jobs": {"company": "Google", "location": "Paris", "source": "wttj"}},
            {"match_keywords": "[]", "raw_jobs": {"company": "Meta", "location": "London", "source": "adzuna"}},
        ]

        mock_sb = MagicMock()
        interested_result = MagicMock()
        interested_result.data = interested_data
        empty = MagicMock()
        empty.data = []
        mock_sb.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value = interested_result
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = empty

        with patch("worker.feedback_loop.get_supabase", return_value=mock_sb):
            result = analyze_keyword_preferences("test-user")

        companies = [c for c, _ in result["preferred_companies"]]
        assert "Google" in companies


class TestFeedbackStats:
    def test_feedback_stats(self):
        from worker.feedback_loop import get_feedback_stats

        mock_sb = MagicMock()
        interested = MagicMock()
        interested.count = 5
        rejected = MagicMock()
        rejected.count = 3
        applied = MagicMock()
        applied.count = 2

        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            interested, rejected, applied
        ]

        with patch("worker.feedback_loop.get_supabase", return_value=mock_sb):
            stats = get_feedback_stats("test-user")

        assert stats["interested"] == 5
        assert stats["rejected"] == 3
        assert stats["applied"] == 2
        assert stats["total_feedback"] == 10

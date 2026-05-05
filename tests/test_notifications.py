"""Tests for notification formatting and filtering."""
import json


class TestDigestHtml:
    def test_build_digest_html(self):
        from worker.notifications import _build_digest_html

        jobs = [{
            "match_score": 85,
            "match_priority": "high",
            "match_keywords": json.dumps(["python", "ml", "fastapi"]),
            "raw_jobs": {
                "title": "ML Engineer",
                "company": "TechCorp",
                "location": "Paris",
                "source_url": "https://example.com/job1",
            },
        }]
        html = _build_digest_html("Thomas", jobs)
        assert "Thomas" in html
        assert "ML Engineer" in html
        assert "TechCorp" in html
        assert "85" in html
        assert "#16a34a" in html  # high priority green

    def test_digest_multiple_jobs(self):
        from worker.notifications import _build_digest_html

        jobs = [
            {"match_score": 90, "match_priority": "high",
             "match_keywords": "[]", "raw_jobs": {"title": "Job A", "company": "A", "location": "Paris", "source_url": "#"}},
            {"match_score": 60, "match_priority": "medium",
             "match_keywords": "[]", "raw_jobs": {"title": "Job B", "company": "B", "location": "Lyon", "source_url": "#"}},
            {"match_score": 40, "match_priority": "low",
             "match_keywords": "[]", "raw_jobs": {"title": "Job C", "company": "C", "location": "Remote", "source_url": "#"}},
        ]
        html = _build_digest_html("User", jobs)
        assert "Job A" in html
        assert "Job B" in html
        assert "Job C" in html

    def test_digest_json_string_keywords(self):
        from worker.notifications import _build_digest_html

        jobs = [{
            "match_score": 75,
            "match_priority": "medium",
            "match_keywords": '["django", "postgres"]',
            "raw_jobs": {"title": "Backend", "company": "X", "location": "Y", "source_url": "#"},
        }]
        html = _build_digest_html("Test", jobs)
        assert "django" in html
        assert "postgres" in html

    def test_digest_list_keywords(self):
        from worker.notifications import _build_digest_html

        jobs = [{
            "match_score": 75,
            "match_priority": "medium",
            "match_keywords": ["react", "typescript"],
            "raw_jobs": {"title": "Frontend", "company": "Y", "location": "Z", "source_url": "#"},
        }]
        html = _build_digest_html("Test", jobs)
        assert "react" in html


class TestTelegramDigest:
    def test_build_digest_text(self):
        from worker.notifications import _build_digest_text

        jobs = [{
            "match_score": 88,
            "match_priority": "high",
            "raw_jobs": {"title": "Data Scientist", "company": "DeepCo", "source_url": "https://example.com"},
        }]
        text = _build_digest_text("Thomas", jobs)
        assert "Thomas" in text
        assert "88" in text
        assert "Data Scientist" in text
        assert "🔴" in text  # high priority

    def test_digest_medium_priority(self):
        from worker.notifications import _build_digest_text

        jobs = [{
            "match_score": 65,
            "match_priority": "medium",
            "raw_jobs": {"title": "Dev", "company": "Corp", "source_url": ""},
        }]
        text = _build_digest_text("User", jobs)
        assert "🟡" in text

    def test_digest_lists_all_jobs(self):
        from worker.notifications import _build_digest_text

        jobs = [
            {"match_score": i * 5, "match_priority": "low",
             "raw_jobs": {"title": f"Job {i}", "company": "C", "source_url": ""}}
            for i in range(15)
        ]
        text = _build_digest_text("User", jobs)
        for i in range(15):
            assert f"Job {i}" in text

    def test_digest_keyboard_one_row_per_job(self):
        from worker.notifications import _build_digest_keyboard

        jobs = [
            {"id": "abc", "match_score": 90, "match_priority": "high",
             "raw_jobs": {"title": "Job A", "source_url": "https://example.com/a"}},
            {"id": "def", "match_score": 60, "match_priority": "medium",
             "raw_jobs": {"title": "Job B", "source_url": ""}},
        ]
        kb = _build_digest_keyboard(jobs)
        assert "inline_keyboard" in kb
        rows = kb["inline_keyboard"]
        assert len(rows) == 2
        assert rows[0][0]["callback_data"] == "detail_abc"
        assert rows[0][1]["url"] == "https://example.com/a"
        # Second job has no source_url → only the detail button
        assert len(rows[1]) == 1

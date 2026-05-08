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


class TestMarkdownSafety:
    """Regression coverage for the Telegram parse-error class of bugs.

    A single unescaped underscore or asterisk in a job title used to drop the
    entire digest with a silent 400 — this guards against that.
    """

    def test_md_escape_special_chars(self):
        from worker.notifications import _md_escape
        assert _md_escape("A_B") == r"A\_B"
        assert _md_escape("Senior *Dev*") == r"Senior \*Dev\*"
        assert _md_escape("[awesome](spam)") == r"\[awesome\](spam)"
        assert _md_escape("`code`") == r"\`code\`"

    def test_md_escape_handles_none_and_non_str(self):
        from worker.notifications import _md_escape
        assert _md_escape(None) == ""
        assert _md_escape(42) == "42"

    def test_digest_escapes_company_with_underscore(self):
        from worker.notifications import _build_digest_text
        jobs = [{
            "match_score": 80,
            "match_priority": "high",
            "raw_jobs": {
                "title": "Backend_Engineer",
                "company": "ACME_Co",
                "source_url": "https://example.com/job",
            },
        }]
        text = _build_digest_text("user_name", jobs)
        # No raw underscore in user-supplied content → cannot break Markdown
        assert "ACME\\_Co" in text
        assert "Backend\\_Engineer" in text
        assert "user\\_name" in text

    def test_digest_drops_link_when_url_has_paren(self):
        """URLs with '(' or ')' break Markdown V1 link syntax — fall back to plain title."""
        from worker.notifications import _build_digest_text
        jobs = [{
            "match_score": 80,
            "match_priority": "low",
            "raw_jobs": {
                "title": "Job",
                "company": "Co",
                "source_url": "https://example.com/path(weird)",
            },
        }]
        text = _build_digest_text("U", jobs)
        # No Markdown link should be rendered — plain title only
        assert "[Job](" not in text
        assert "Job" in text

    def test_digest_truncates_to_telegram_limit(self):
        from worker.notifications import _build_digest_text, TELEGRAM_MAX_TEXT
        jobs = [{
            "match_score": 80,
            "match_priority": "high",
            "raw_jobs": {
                "title": "T" * 200,
                "company": "C" * 200,
                "location": "L" * 200,
                "source_url": "",
            },
        } for _ in range(50)]
        text = _build_digest_text("U", jobs)
        assert len(text) <= TELEGRAM_MAX_TEXT + 5  # +5 for the ellipsis suffix


class TestStripMarkdown:
    def test_strip_removes_link_keeps_text(self):
        from worker.notifications import _strip_markdown
        assert _strip_markdown("see [here](https://x.com)") == "see here"

    def test_strip_removes_emphasis(self):
        from worker.notifications import _strip_markdown
        assert _strip_markdown("*bold* and _italic_ and `code`") == "bold and italic and code"

    def test_strip_unescapes_backslashed(self):
        from worker.notifications import _strip_markdown
        assert _strip_markdown(r"A\_B") == "A_B"

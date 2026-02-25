"""Tests for Notion bidirectional sync logic."""
from unittest.mock import MagicMock, patch


class TestStatusMapping:
    def test_map_status_forward(self):
        from worker.notion_sync import _map_status
        assert _map_status("new") == "Nouveau"
        assert _map_status("interested") == "Intéressé"
        assert _map_status("rejected") == "Rejeté"
        assert _map_status("applied") == "Postulé"
        assert _map_status("notified") == "Notifié"

    def test_map_status_unknown(self):
        from worker.notion_sync import _map_status
        assert _map_status("custom_status") == "custom_status"

    def test_reverse_map_status(self):
        from worker.notion_sync import _reverse_map_status
        assert _reverse_map_status("Nouveau") == "new"
        assert _reverse_map_status("Intéressé") == "interested"
        assert _reverse_map_status("Rejeté") == "rejected"
        assert _reverse_map_status("Postulé") == "applied"
        assert _reverse_map_status("Notifié") == "new"

    def test_reverse_map_unknown(self):
        from worker.notion_sync import _reverse_map_status
        assert _reverse_map_status("Unknown") is None
        assert _reverse_map_status("") is None


class TestJobToNotionProperties:
    def test_minimal_job(self):
        from worker.notion_sync import _job_to_notion_properties
        job = {
            "match_score": 85,
            "match_priority": "high",
            "match_keywords": ["python", "ml"],
            "match_reasoning": "Good match",
            "status": "new",
            "user_notes": None,
            "raw_jobs": {
                "title": "Dev Python",
                "company": "Acme",
                "source": "wttj",
                "location": None,
                "source_url": None,
                "remote_type": "unknown",
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "EUR",
                "scraped_at": None,
            },
        }
        props = _job_to_notion_properties(job)
        assert props["Titre"]["title"][0]["text"]["content"] == "Dev Python"
        assert props["Score"]["number"] == 85
        assert props["Statut"]["select"]["name"] == "Nouveau"
        assert "Notes" not in props

    def test_job_with_notes(self):
        from worker.notion_sync import _job_to_notion_properties
        job = {
            "match_score": 70,
            "match_priority": "medium",
            "match_keywords": [],
            "match_reasoning": "",
            "status": "interested",
            "user_notes": "Looks promising, follow up next week",
            "raw_jobs": {
                "title": "ML Engineer",
                "company": "DeepCo",
                "source": "adzuna",
                "location": "Paris",
                "source_url": "https://example.com/job/1",
                "remote_type": "partial",
                "salary_min": 50000,
                "salary_max": 70000,
                "salary_currency": "EUR",
                "scraped_at": "2026-02-25T10:00:00",
            },
        }
        props = _job_to_notion_properties(job)
        assert props["Notes"]["rich_text"][0]["text"]["content"] == "Looks promising, follow up next week"
        assert props["Salaire"]["rich_text"][0]["text"]["content"] == "50K-70K EUR"
        assert props["Remote"]["select"]["name"] == "partial"

    def test_job_with_json_keywords(self):
        from worker.notion_sync import _job_to_notion_properties
        job = {
            "match_score": 60,
            "match_priority": "low",
            "match_keywords": '["python", "fastapi"]',
            "match_reasoning": "",
            "status": "new",
            "user_notes": "",
            "raw_jobs": {"title": "Dev", "company": "Co", "source": "wttj",
                         "location": None, "source_url": None, "remote_type": "unknown",
                         "salary_min": None, "salary_max": None, "salary_currency": "EUR",
                         "scraped_at": None},
        }
        props = _job_to_notion_properties(job)
        assert "python" in props["Keywords"]["rich_text"][0]["text"]["content"]


class TestFormatSalary:
    def test_salary_range(self):
        from worker.notion_sync import _format_salary
        assert _format_salary({"salary_min": 50000, "salary_max": 70000, "salary_currency": "EUR"}) == "50K-70K EUR"

    def test_salary_min_only(self):
        from worker.notion_sync import _format_salary
        assert _format_salary({"salary_min": 40000, "salary_max": None, "salary_currency": "EUR"}) == "40K+ EUR"

    def test_no_salary(self):
        from worker.notion_sync import _format_salary
        assert _format_salary({"salary_min": None, "salary_max": None}) == ""


class TestPullNotionChanges:
    def test_pull_status_change(self):
        """When Notion status changes, local DB should update."""
        import asyncio
        from worker.notion_sync import pull_notion_changes

        mock_sb = MagicMock()

        # Profile with last sync
        profile_result = MagicMock()
        profile_result.data = {"notion_last_sync_at": "2026-02-24T00:00:00Z"}

        # Local jobs with notion page IDs
        local_jobs_result = MagicMock()
        local_jobs_result.data = [
            {"id": 1, "notion_page_id": "page-abc", "status": "new", "user_notes": ""},
        ]

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "profiles":
                mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result
                mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
            elif name == "user_jobs":
                mock_table.select.return_value.eq.return_value.not_.is_.return_value.execute.return_value = local_jobs_result
                mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
            return mock_table

        mock_sb.table.side_effect = table_side_effect

        # Notion API returns a page with changed status
        notion_response = {
            "results": [{
                "id": "page-abc",
                "properties": {
                    "Statut": {"select": {"name": "Intéressé"}},
                    "Notes": {"rich_text": []},
                },
            }],
        }

        with patch("worker.notion_sync.get_supabase", return_value=mock_sb), \
             patch("worker.notion_sync.get_settings") as mock_settings, \
             patch("worker.notion_sync._notion_request", return_value=notion_response):
            mock_settings.return_value.notion_token = "secret_token"
            mock_settings.return_value.notion_jobs_db_id = "db-123"
            count = asyncio.run(pull_notion_changes("test-user"))

        assert count == 1

    def test_pull_no_changes(self):
        """When no Notion pages changed, nothing should update."""
        import asyncio
        from worker.notion_sync import pull_notion_changes

        mock_sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {"notion_last_sync_at": "2026-02-24T00:00:00Z"}
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        with patch("worker.notion_sync.get_supabase", return_value=mock_sb), \
             patch("worker.notion_sync.get_settings") as mock_settings, \
             patch("worker.notion_sync._notion_request", return_value={"results": []}):
            mock_settings.return_value.notion_token = "secret_token"
            mock_settings.return_value.notion_jobs_db_id = "db-123"
            count = asyncio.run(pull_notion_changes("test-user"))

        assert count == 0

    def test_pull_notes_sync(self):
        """Notes from Notion should sync to local user_notes."""
        import asyncio
        from worker.notion_sync import pull_notion_changes

        mock_sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {"notion_last_sync_at": None}

        local_jobs_result = MagicMock()
        local_jobs_result.data = [
            {"id": 42, "notion_page_id": "page-xyz", "status": "interested", "user_notes": ""},
        ]

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "profiles":
                mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result
                mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
            elif name == "user_jobs":
                mock_table.select.return_value.eq.return_value.not_.is_.return_value.execute.return_value = local_jobs_result
                mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
            return mock_table

        mock_sb.table.side_effect = table_side_effect

        notion_response = {
            "results": [{
                "id": "page-xyz",
                "properties": {
                    "Statut": {"select": {"name": "Intéressé"}},
                    "Notes": {"rich_text": [{"plain_text": "Super opportunité"}]},
                },
            }],
        }

        with patch("worker.notion_sync.get_supabase", return_value=mock_sb), \
             patch("worker.notion_sync.get_settings") as mock_settings, \
             patch("worker.notion_sync._notion_request", return_value=notion_response):
            mock_settings.return_value.notion_token = "secret_token"
            mock_settings.return_value.notion_jobs_db_id = "db-123"
            count = asyncio.run(pull_notion_changes("test-user"))

        assert count == 1

    def test_pull_disabled_when_no_token(self):
        """Pull should return 0 when notion_token is empty."""
        import asyncio
        from worker.notion_sync import pull_notion_changes

        with patch("worker.notion_sync.get_settings") as mock_settings:
            mock_settings.return_value.notion_token = ""
            mock_settings.return_value.notion_jobs_db_id = "db-123"
            count = asyncio.run(pull_notion_changes("test-user"))

        assert count == 0

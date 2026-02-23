"""Unit tests for Pydantic models — validation constraints."""
import pytest
from pydantic import ValidationError

from backend.app.models.profile import ProfileRead, ProfileUpdate
from backend.app.models.job import JobFeedback


class TestProfileValidation:
    def test_valid_profile(self):
        p = ProfileRead(id="abc-123", monthly_budget_usd=5.0, min_score_notify=70)
        assert p.monthly_budget_usd == 5.0

    def test_budget_too_high(self):
        with pytest.raises(ValidationError):
            ProfileRead(id="abc", monthly_budget_usd=200.0)

    def test_budget_negative(self):
        with pytest.raises(ValidationError):
            ProfileRead(id="abc", monthly_budget_usd=-1.0)

    def test_min_salary_negative(self):
        with pytest.raises(ValidationError):
            ProfileUpdate(min_salary=-5000)

    def test_min_salary_too_high(self):
        with pytest.raises(ValidationError):
            ProfileUpdate(min_salary=600_000)

    def test_min_score_notify_out_of_range(self):
        with pytest.raises(ValidationError):
            ProfileUpdate(min_score_notify=150)

    def test_valid_update(self):
        u = ProfileUpdate(
            name="Thomas",
            monthly_budget_usd=10.0,
            min_salary=45000,
            min_score_notify=60,
        )
        assert u.name == "Thomas"
        assert u.monthly_budget_usd == 10.0


class TestJobFeedback:
    def test_valid_statuses(self):
        for s in ("interested", "rejected", "applied", "new"):
            f = JobFeedback(status=s)
            assert f.status == s

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            JobFeedback(status="pending")

    def test_invalid_status_empty(self):
        with pytest.raises(ValidationError):
            JobFeedback(status="")

    def test_with_notes(self):
        f = JobFeedback(status="interested", user_notes="Great company")
        assert f.user_notes == "Great company"

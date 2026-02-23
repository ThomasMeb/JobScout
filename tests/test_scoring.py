"""Unit tests for worker/scoring.py — scoring logic, cost estimation, response parsing."""
import json

from worker.scoring import (
    estimate_cost,
    format_salary,
    parse_scoring_response,
)


class TestParseScoring:
    def test_valid_json(self):
        response = json.dumps({
            "skills": 25,
            "seniority": 20,
            "location": 15,
            "domain": 10,
            "compensation": 8,
            "match_keywords": ["python", "fastapi"],
            "missing_keywords": ["kubernetes"],
            "reasoning": "Bon match technique",
        })
        result = parse_scoring_response(response)
        assert result["score"] == 78
        assert result["priority"] == "high"
        assert "python" in result["match_keywords"]
        assert "kubernetes" in result["missing_keywords"]
        assert "Bon match technique" in result["reasoning"]

    def test_medium_priority(self):
        response = json.dumps({
            "skills": 15,
            "seniority": 12,
            "location": 10,
            "domain": 8,
            "compensation": 5,
        })
        result = parse_scoring_response(response)
        assert result["score"] == 50
        assert result["priority"] == "medium"

    def test_low_priority(self):
        response = json.dumps({
            "skills": 10,
            "seniority": 5,
            "location": 5,
            "domain": 3,
            "compensation": 2,
        })
        result = parse_scoring_response(response)
        assert result["score"] == 25
        assert result["priority"] == "low"

    def test_clamped_values(self):
        """Scores exceeding max should be clamped."""
        response = json.dumps({
            "skills": 50,
            "seniority": 40,
            "location": 30,
            "domain": 20,
            "compensation": 15,
        })
        result = parse_scoring_response(response)
        # Clamped: 30 + 25 + 20 + 15 + 10 = 100
        assert result["score"] == 100
        assert result["priority"] == "high"

    def test_negative_values_clamped_to_zero(self):
        response = json.dumps({
            "skills": -5,
            "seniority": -10,
            "location": 0,
            "domain": 0,
            "compensation": 0,
        })
        result = parse_scoring_response(response)
        assert result["score"] == 0
        assert result["priority"] == "low"

    def test_markdown_wrapped_json(self):
        """LLM sometimes wraps JSON in markdown code blocks."""
        response = "```json\n" + json.dumps({
            "skills": 20,
            "seniority": 15,
            "location": 10,
            "domain": 5,
            "compensation": 5,
        }) + "\n```"
        result = parse_scoring_response(response)
        assert result["score"] == 55

    def test_invalid_json(self):
        result = parse_scoring_response("this is not json")
        assert result["score"] == 0
        assert result["priority"] == "low"
        assert result["reasoning"] == "Parsing error"

    def test_empty_response(self):
        result = parse_scoring_response("")
        assert result["score"] == 0

    def test_missing_fields_default_to_zero(self):
        response = json.dumps({"skills": 20, "reasoning": "Partiel"})
        result = parse_scoring_response(response)
        assert result["score"] == 20


class TestEstimateCost:
    def test_deepseek_chat(self):
        cost = estimate_cost("deepseek-chat", 1000, 500)
        # (1000 * 0.28 + 500 * 1.10) / 1_000_000 = 0.00083
        assert cost == 0.000830

    def test_zero_tokens(self):
        cost = estimate_cost("deepseek-chat", 0, 0)
        assert cost == 0.0

    def test_unknown_model_uses_default(self):
        cost = estimate_cost("unknown-model", 1000, 500)
        assert cost == 0.000830


class TestFormatSalary:
    def test_range(self):
        assert format_salary(40000, 60000) == "40000-60000 EUR"

    def test_min_only(self):
        assert format_salary(40000, None) == "40000+ EUR"

    def test_max_only(self):
        assert format_salary(None, 60000) == "up to 60000 EUR"

    def test_none(self):
        assert format_salary(None, None) == "Non précisé"

    def test_custom_currency(self):
        assert format_salary(50000, 70000, "USD") == "50000-70000 USD"

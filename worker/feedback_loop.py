"""Feedback loop — analyse les preferences utilisateur a partir des jobs interested/rejected.

Adapted from legacy/job_agent/feedback_loop.py for multi-tenant SaaS (Supabase).
"""

import json
import logging
from collections import Counter

from worker.db import get_supabase

logger = logging.getLogger(__name__)


def get_feedback_stats(user_id: str) -> dict:
    """Return simple feedback counts for a user."""
    sb = get_supabase()

    interested = (
        sb.table("user_jobs")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("status", "interested")
        .execute()
    )
    rejected = (
        sb.table("user_jobs")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("status", "rejected")
        .execute()
    )
    applied = (
        sb.table("user_jobs")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("status", "applied")
        .execute()
    )

    i_count = interested.count or 0
    r_count = rejected.count or 0
    a_count = applied.count or 0

    return {
        "interested": i_count,
        "rejected": r_count,
        "applied": a_count,
        "total_feedback": i_count + r_count + a_count,
    }


def analyze_keyword_preferences(user_id: str) -> dict:
    """Analyze keyword frequency in interested vs rejected jobs.

    Returns dict with preferred/avoided keywords, companies, locations, sources.
    """
    sb = get_supabase()

    interested_rows = (
        sb.table("user_jobs")
        .select("match_keywords, raw_jobs(company, location, source)")
        .eq("user_id", user_id)
        .in_("status", ["interested", "applied"])
        .execute()
    ).data or []

    rejected_rows = (
        sb.table("user_jobs")
        .select("match_keywords, raw_jobs(company, location, source)")
        .eq("user_id", user_id)
        .eq("status", "rejected")
        .execute()
    ).data or []

    if not interested_rows and not rejected_rows:
        return {
            "preferred_keywords": [], "avoided_keywords": [],
            "preferred_companies": [], "preferred_locations": [],
            "preferred_sources": [],
        }

    interested_kw = Counter()
    rejected_kw = Counter()

    for row in interested_rows:
        kws = row.get("match_keywords") or "[]"
        if isinstance(kws, str):
            kws = json.loads(kws)
        for kw in kws:
            interested_kw[kw.lower()] += 1

    for row in rejected_rows:
        kws = row.get("match_keywords") or "[]"
        if isinstance(kws, str):
            kws = json.loads(kws)
        for kw in kws:
            rejected_kw[kw.lower()] += 1

    all_keywords = set(interested_kw.keys()) | set(rejected_kw.keys())
    preferred = []
    avoided = []

    for kw in all_keywords:
        pos = interested_kw.get(kw, 0)
        neg = rejected_kw.get(kw, 0)
        total = pos + neg
        if total < 2:
            continue
        ratio = pos / total
        if ratio >= 0.7:
            preferred.append((kw, ratio, total))
        elif ratio <= 0.3:
            avoided.append((kw, ratio, total))

    preferred.sort(key=lambda x: (-x[1], -x[2]))
    avoided.sort(key=lambda x: (x[1], -x[2]))

    # Count companies, locations, sources from interested jobs
    interested_companies = Counter()
    interested_locations = Counter()
    interested_sources = Counter()

    for row in interested_rows:
        raw = row.get("raw_jobs") or {}
        if raw.get("company"):
            interested_companies[raw["company"]] += 1
        if raw.get("location"):
            interested_locations[raw["location"]] += 1
        if raw.get("source"):
            interested_sources[raw["source"]] += 1

    return {
        "preferred_keywords": [(kw, r) for kw, r, _ in preferred[:15]],
        "avoided_keywords": [(kw, r) for kw, r, _ in avoided[:15]],
        "preferred_companies": interested_companies.most_common(5),
        "preferred_locations": interested_locations.most_common(5),
        "preferred_sources": interested_sources.most_common(5),
    }


def generate_preference_summary(user_id: str) -> str:
    """Generate a text summary of user preferences for injection into the scoring prompt.

    Returns empty string if fewer than 5 feedbacks.
    """
    stats = get_feedback_stats(user_id)
    if stats["total_feedback"] < 5:
        return ""

    prefs = analyze_keyword_preferences(user_id)

    parts = []

    if prefs["preferred_keywords"]:
        kws = ", ".join(kw for kw, _ in prefs["preferred_keywords"][:10])
        parts.append(f"Keywords preferes par le candidat : {kws}")

    if prefs["avoided_keywords"]:
        kws = ", ".join(kw for kw, _ in prefs["avoided_keywords"][:10])
        parts.append(f"Keywords evites par le candidat : {kws}")

    if prefs["preferred_companies"]:
        companies = ", ".join(c for c, _ in prefs["preferred_companies"][:5])
        parts.append(f"Entreprises appreciees : {companies}")

    if prefs["preferred_locations"]:
        locations = ", ".join(loc for loc, _ in prefs["preferred_locations"][:5])
        parts.append(f"Localisations preferees : {locations}")

    if not parts:
        return ""

    return "\n".join(parts)

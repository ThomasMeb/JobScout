"""Feedback loop — analyse les preferences utilisateur a partir des jobs interested/rejected."""

import json
import logging
import sqlite3
from collections import Counter

logger = logging.getLogger(__name__)


def get_feedback_stats(conn: sqlite3.Connection) -> dict:
    """Return simple feedback counts."""
    interested = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'interested'"
    ).fetchone()[0]
    rejected = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'rejected'"
    ).fetchone()[0]
    applied = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'applied'"
    ).fetchone()[0]
    return {
        "interested": interested,
        "rejected": rejected,
        "applied": applied,
        "total_feedback": interested + rejected + applied,
    }


def analyze_keyword_preferences(conn: sqlite3.Connection) -> dict:
    """Analyze keyword frequency in interested vs rejected jobs.

    Returns dict with preferred/avoided keywords, companies, locations, sources.
    """
    interested_rows = conn.execute(
        "SELECT match_keywords, company, location, source FROM jobs WHERE status IN ('interested', 'applied')"
    ).fetchall()
    rejected_rows = conn.execute(
        "SELECT match_keywords, company, location, source FROM jobs WHERE status = 'rejected'"
    ).fetchall()

    if not interested_rows and not rejected_rows:
        return {"preferred_keywords": [], "avoided_keywords": [],
                "preferred_companies": [], "preferred_locations": [],
                "preferred_sources": []}

    # Count keywords
    interested_kw = Counter()
    rejected_kw = Counter()

    for row in interested_rows:
        kws = json.loads(row[0] or "[]")
        for kw in kws:
            interested_kw[kw.lower()] += 1

    for row in rejected_rows:
        kws = json.loads(row[0] or "[]")
        for kw in kws:
            rejected_kw[kw.lower()] += 1

    # Compute preference ratio for keywords appearing at least twice
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
    interested_companies = Counter(row[1] for row in interested_rows if row[1])
    interested_locations = Counter(row[2] for row in interested_rows if row[2])
    interested_sources = Counter(row[3] for row in interested_rows if row[3])

    return {
        "preferred_keywords": [(kw, r) for kw, r, _ in preferred[:15]],
        "avoided_keywords": [(kw, r) for kw, r, _ in avoided[:15]],
        "preferred_companies": interested_companies.most_common(5),
        "preferred_locations": interested_locations.most_common(5),
        "preferred_sources": interested_sources.most_common(5),
    }


def generate_preference_summary(conn: sqlite3.Connection) -> str:
    """Generate a text summary of user preferences for injection into the scoring prompt.

    Returns empty string if fewer than 5 feedbacks (graceful degradation).
    """
    stats = get_feedback_stats(conn)
    if stats["total_feedback"] < 5:
        return ""

    prefs = analyze_keyword_preferences(conn)

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

#!/usr/bin/env python3
"""Migrate Thomas's SQLite data to Supabase.

One-shot script: reads local jobs.db and inserts into Supabase
raw_jobs + user_jobs (for Thomas's UUID) + llm_usage.

Usage:
    export SUPABASE_URL=https://your-project.supabase.co
    export SUPABASE_SERVICE_ROLE_KEY=your_key
    export THOMAS_USER_ID=your-uuid-from-supabase-auth
    python scripts/migrate_to_supabase.py
"""
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime

from supabase import create_client


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "jobs.db")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
THOMAS_USER_ID = os.environ.get("THOMAS_USER_ID", "")


def job_hash(title: str, company: str, source_url: str) -> str:
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{source_url.strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def migrate():
    if not all([SUPABASE_URL, SUPABASE_KEY, THOMAS_USER_ID]):
        print("Error: Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and THOMAS_USER_ID")
        sys.exit(1)

    if not os.path.exists(DB_PATH):
        print(f"Error: SQLite database not found at {DB_PATH}")
        sys.exit(1)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 1. Migrate jobs → raw_jobs + user_jobs
    jobs = conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
    print(f"Found {len(jobs)} jobs in SQLite")

    raw_job_map = {}  # sqlite_id → supabase_raw_job_id
    migrated_raw = 0
    migrated_user = 0
    skipped = 0

    for job in jobs:
        job = dict(job)
        h = job_hash(job["title"], job["company"], job["source_url"])

        # Parse tags
        tags = job.get("tags")
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except (json.JSONDecodeError, TypeError):
                tags = []
        if not tags:
            tags = []

        # Upsert into raw_jobs
        existing = sb.table("raw_jobs").select("id").eq("hash", h).execute()
        if existing.data:
            raw_job_id = existing.data[0]["id"]
            skipped += 1
        else:
            result = sb.table("raw_jobs").insert({
                "hash": h,
                "title": job["title"],
                "company": job["company"],
                "location": job.get("location"),
                "remote_type": job.get("remote_type", "unknown"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "salary_currency": job.get("salary_currency", "EUR"),
                "description": job.get("description"),
                "tags": json.dumps(tags),
                "source": job["source"],
                "source_url": job["source_url"],
                "apply_url": job.get("apply_url"),
                "company_url": job.get("company_url"),
                "posted_at": job.get("posted_at"),
                "scraped_at": job.get("scraped_at") or datetime.now().isoformat(),
            }).execute()
            raw_job_id = result.data[0]["id"]
            migrated_raw += 1

        raw_job_map[job["id"]] = raw_job_id

        # Insert into user_jobs if scored
        if job.get("match_score") is not None:
            # Parse keywords
            match_kw = job.get("match_keywords")
            if isinstance(match_kw, str):
                try:
                    match_kw = json.loads(match_kw)
                except (json.JSONDecodeError, TypeError):
                    match_kw = []

            missing_kw = job.get("missing_keywords")
            if isinstance(missing_kw, str):
                try:
                    missing_kw = json.loads(missing_kw)
                except (json.JSONDecodeError, TypeError):
                    missing_kw = []

            # Check if already exists
            uj_exists = (
                sb.table("user_jobs")
                .select("id")
                .eq("user_id", THOMAS_USER_ID)
                .eq("raw_job_id", raw_job_id)
                .execute()
            )
            if not uj_exists.data:
                sb.table("user_jobs").insert({
                    "user_id": THOMAS_USER_ID,
                    "raw_job_id": raw_job_id,
                    "match_score": job["match_score"],
                    "match_reasoning": job.get("match_reasoning"),
                    "match_keywords": json.dumps(match_kw or []),
                    "missing_keywords": json.dumps(missing_kw or []),
                    "match_priority": job.get("match_priority", "low"),
                    "status": job.get("status", "new"),
                    "user_notes": job.get("user_notes"),
                    "scored_at": job.get("scored_at"),
                }).execute()
                migrated_user += 1

        if (migrated_raw + skipped) % 100 == 0:
            print(f"  Progress: {migrated_raw + skipped}/{len(jobs)}")

    print(f"raw_jobs: {migrated_raw} new, {skipped} already existed")
    print(f"user_jobs: {migrated_user} scored jobs migrated")

    # 2. Migrate llm_usage
    usage_rows = conn.execute("SELECT * FROM llm_usage ORDER BY id").fetchall()
    migrated_usage = 0

    for usage in usage_rows:
        usage = dict(usage)
        sqlite_job_id = usage.get("job_id")
        supabase_uj_id = None

        if sqlite_job_id and sqlite_job_id in raw_job_map:
            raw_jid = raw_job_map[sqlite_job_id]
            uj = (
                sb.table("user_jobs")
                .select("id")
                .eq("user_id", THOMAS_USER_ID)
                .eq("raw_job_id", raw_jid)
                .execute()
            )
            if uj.data:
                supabase_uj_id = uj.data[0]["id"]

        sb.table("llm_usage").insert({
            "user_id": THOMAS_USER_ID,
            "operation": usage.get("operation", "scoring"),
            "user_job_id": supabase_uj_id,
            "model": usage.get("model", "deepseek-chat"),
            "tokens_in": usage.get("input_tokens", 0),
            "tokens_out": usage.get("output_tokens", 0),
            "cost_usd": usage.get("cost_usd", 0),
            "created_at": usage.get("created_at"),
        }).execute()
        migrated_usage += 1

    print(f"llm_usage: {migrated_usage} rows migrated")

    conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()

"""Export an anonymized demo database for Streamlit Cloud deployment.

Reads data/jobs.db, anonymizes sensitive data (company names, URLs),
and exports to assets/demo.db.
"""

import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC_DB = ROOT / "data" / "jobs.db"
DST_DB = ROOT / "assets" / "demo.db"


def anonymize_db():
    if not SRC_DB.exists():
        print(f"ERROR: source DB not found at {SRC_DB}")
        return

    DST_DB.parent.mkdir(parents=True, exist_ok=True)

    # Copy full DB first, then anonymize in place
    shutil.copy2(SRC_DB, DST_DB)
    conn = sqlite3.connect(str(DST_DB))
    cur = conn.cursor()

    # --- Build company name mapping ---
    cur.execute("SELECT DISTINCT company FROM jobs WHERE match_score IS NOT NULL ORDER BY company")
    job_companies = [r[0] for r in cur.fetchall()]
    company_map = {}
    for i, name in enumerate(job_companies, 1):
        company_map[name] = f"Company_{i}"

    cur.execute("SELECT DISTINCT name FROM companies ORDER BY name")
    for r in cur.fetchall():
        if r[0] not in company_map:
            company_map[r[0]] = f"Company_{len(company_map) + 1}"

    # --- Anonymize jobs table ---
    for original, anon in company_map.items():
        cur.execute("UPDATE jobs SET company = ? WHERE company = ?", (anon, original))

    # Clear sensitive URLs and descriptions
    cur.execute("""
        UPDATE jobs SET
            source_url = '',
            apply_url = '',
            company_url = '',
            description = '',
            hash = 'demo_' || id
    """)

    # Remove jobs without score (not shown in dashboard)
    cur.execute("DELETE FROM jobs WHERE match_score IS NULL")

    # --- Anonymize companies table ---
    for original, anon in company_map.items():
        cur.execute("UPDATE companies SET name = ? WHERE name = ?", (anon, original))

    cur.execute("""
        UPDATE companies SET
            website = '',
            careers_url = '',
            notes = ''
    """)

    # --- Clear applications (may contain personal data) ---
    cur.execute("DELETE FROM applications")

    # --- Keep scrape_runs and llm_usage as-is (no personal data, useful for charts) ---

    # --- Vacuum to reduce file size ---
    conn.commit()
    cur.execute("VACUUM")
    conn.close()

    size_mb = DST_DB.stat().st_size / (1024 * 1024)
    cur2 = sqlite3.connect(str(DST_DB))
    job_count = cur2.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    company_count = cur2.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    cur2.close()

    print(f"Demo DB exported to {DST_DB}")
    print(f"  Jobs: {job_count}, Companies: {company_count}")
    print(f"  Size: {size_mb:.1f} MB")


if __name__ == "__main__":
    anonymize_db()

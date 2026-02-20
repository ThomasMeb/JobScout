import hashlib
import json
import sqlite3
from datetime import datetime

from job_agent.config import DB_PATH, DATA_DIR

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    remote_type TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT DEFAULT 'EUR',
    description TEXT,
    tags TEXT,
    source TEXT NOT NULL,
    source_url TEXT NOT NULL,
    apply_url TEXT,
    company_url TEXT,
    posted_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    match_score REAL,
    match_reasoning TEXT,
    match_keywords TEXT,
    missing_keywords TEXT,
    match_priority TEXT,
    scored_at TIMESTAMP,
    status TEXT DEFAULT 'new',
    user_notes TEXT,
    tokens_scoring INTEGER DEFAULT 0,
    tokens_tailoring INTEGER DEFAULT 0,
    notion_page_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(match_score);
CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs(hash);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    cv_path TEXT,
    cover_letter_path TEXT,
    language TEXT DEFAULT 'fr',
    tailoring_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    status TEXT DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS scrape_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    jobs_found INTEGER DEFAULT 0,
    jobs_new INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS llm_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,
    job_id INTEGER REFERENCES jobs(id),
    model TEXT DEFAULT 'deepseek-chat',
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    website TEXT,
    careers_url TEXT,
    sector TEXT,
    location TEXT,
    source TEXT,
    relevance_score REAL,
    has_open_ml_roles BOOLEAN DEFAULT FALSE,
    last_checked_at TIMESTAMP,
    spontaneous_status TEXT DEFAULT 'pending',
    notion_page_id TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(spontaneous_status);

CREATE VIEW IF NOT EXISTS v_monthly_costs AS
SELECT
    strftime('%Y-%m', created_at) AS month,
    operation,
    SUM(input_tokens) AS total_input_tokens,
    SUM(output_tokens) AS total_output_tokens,
    SUM(cost_usd) AS total_cost_usd
FROM llm_usage
GROUP BY month, operation;
"""


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.close()


def _migrate(conn: sqlite3.Connection):
    """Apply schema migrations for existing databases."""
    # Check if notion_page_id column exists in jobs
    jobs_cols = {row[1] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}
    if "notion_page_id" not in jobs_cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN notion_page_id TEXT")
        conn.commit()

    # Add linkedin_tips_path and cost_usd to applications
    app_cols = {row[1] for row in conn.execute("PRAGMA table_info(applications)").fetchall()}
    if "linkedin_tips_path" not in app_cols:
        conn.execute("ALTER TABLE applications ADD COLUMN linkedin_tips_path TEXT")
        conn.commit()
    if "cost_usd" not in app_cols:
        conn.execute("ALTER TABLE applications ADD COLUMN cost_usd REAL DEFAULT 0")
        conn.commit()


def job_hash(title: str, company: str, source_url: str) -> str:
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{source_url.strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def insert_job(conn: sqlite3.Connection, **kwargs) -> int | None:
    """Insert a job if not already present. Returns job id or None if duplicate."""
    h = job_hash(kwargs["title"], kwargs["company"], kwargs["source_url"])
    existing = conn.execute("SELECT id FROM jobs WHERE hash = ?", (h,)).fetchone()
    if existing:
        return None

    tags = kwargs.get("tags")
    if isinstance(tags, list):
        tags = json.dumps(tags)

    conn.execute(
        """INSERT INTO jobs (hash, title, company, location, remote_type,
           salary_min, salary_max, salary_currency, description, tags,
           source, source_url, apply_url, company_url, posted_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            h,
            kwargs["title"],
            kwargs["company"],
            kwargs.get("location"),
            kwargs.get("remote_type", "unknown"),
            kwargs.get("salary_min"),
            kwargs.get("salary_max"),
            kwargs.get("salary_currency", "EUR"),
            kwargs.get("description"),
            tags,
            kwargs["source"],
            kwargs["source_url"],
            kwargs.get("apply_url"),
            kwargs.get("company_url"),
            kwargs.get("posted_at"),
        ),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_unscored_jobs(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM jobs WHERE match_score IS NULL ORDER BY scraped_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def update_job_score(
    conn: sqlite3.Connection,
    job_id: int,
    score: float,
    reasoning: str,
    match_keywords: list[str],
    missing_keywords: list[str],
    priority: str,
    tokens_in: int,
    tokens_out: int,
):
    conn.execute(
        """UPDATE jobs SET match_score=?, match_reasoning=?, match_keywords=?,
           missing_keywords=?, match_priority=?, scored_at=?, tokens_scoring=?
           WHERE id=?""",
        (
            score,
            reasoning,
            json.dumps(match_keywords),
            json.dumps(missing_keywords),
            priority,
            datetime.now().isoformat(),
            tokens_in + tokens_out,
            job_id,
        ),
    )
    conn.commit()


def update_job_status(conn: sqlite3.Connection, job_id: int, status: str):
    conn.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
    conn.commit()


def get_jobs_to_notify(conn: sqlite3.Connection, min_score: float) -> list[dict]:
    rows = conn.execute(
        """SELECT * FROM jobs WHERE match_score >= ? AND status = 'new'
           ORDER BY match_score DESC""",
        (min_score,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_job_by_id(conn: sqlite3.Connection, job_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return dict(row) if row else None


def log_scrape_run(
    conn: sqlite3.Connection,
    source: str,
    jobs_found: int,
    jobs_new: int,
    status: str = "success",
    error_message: str | None = None,
):
    conn.execute(
        """INSERT INTO scrape_runs (source, finished_at, jobs_found, jobs_new, status, error_message)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (source, datetime.now().isoformat(), jobs_found, jobs_new, status, error_message),
    )
    conn.commit()


def log_llm_usage(
    conn: sqlite3.Connection,
    operation: str,
    job_id: int | None,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
):
    conn.execute(
        """INSERT INTO llm_usage (operation, job_id, model, input_tokens, output_tokens, cost_usd)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (operation, job_id, model, input_tokens, output_tokens, cost_usd),
    )
    conn.commit()


def get_monthly_cost(conn: sqlite3.Connection) -> float:
    month = datetime.now().strftime("%Y-%m")
    row = conn.execute(
        "SELECT COALESCE(SUM(cost_usd), 0) as total FROM llm_usage WHERE strftime('%Y-%m', created_at) = ?",
        (month,),
    ).fetchone()
    return row[0]


def insert_company(conn: sqlite3.Connection, **kwargs) -> int | None:
    """Insert a company if not already present (by name+website). Returns id or None."""
    existing = conn.execute(
        "SELECT id FROM companies WHERE name = ? AND website = ?",
        (kwargs["name"], kwargs.get("website")),
    ).fetchone()
    if existing:
        return None

    conn.execute(
        """INSERT INTO companies (name, website, careers_url, sector, location,
           source, relevance_score, has_open_ml_roles)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            kwargs["name"],
            kwargs.get("website"),
            kwargs.get("careers_url"),
            kwargs.get("sector"),
            kwargs.get("location"),
            kwargs.get("source", "manual"),
            kwargs.get("relevance_score"),
            kwargs.get("has_open_ml_roles", False),
        ),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_companies(conn: sqlite3.Connection, status: str | None = None) -> list[dict]:
    if status:
        rows = conn.execute(
            "SELECT * FROM companies WHERE spontaneous_status = ? ORDER BY relevance_score DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM companies ORDER BY relevance_score DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_company_by_id(conn: sqlite3.Connection, company_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
    return dict(row) if row else None


def update_company_status(conn: sqlite3.Connection, company_id: int, status: str):
    conn.execute(
        "UPDATE companies SET spontaneous_status=? WHERE id=?", (status, company_id)
    )
    conn.commit()


def update_company_notion_id(conn: sqlite3.Connection, company_id: int, notion_page_id: str):
    conn.execute(
        "UPDATE companies SET notion_page_id=? WHERE id=?", (notion_page_id, company_id)
    )
    conn.commit()


def get_jobs_without_notion(conn: sqlite3.Connection, min_score: float) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM jobs WHERE match_score >= ? AND notion_page_id IS NULL ORDER BY match_score DESC",
        (min_score,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_job_notion_id(conn: sqlite3.Connection, job_id: int, notion_page_id: str):
    conn.execute("UPDATE jobs SET notion_page_id=? WHERE id=?", (notion_page_id, job_id))
    conn.commit()


def get_stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    new = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='new'").fetchone()[0]
    notified = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='notified'").fetchone()[0]
    interested = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='interested'").fetchone()[0]
    applied = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='applied'").fetchone()[0]
    rejected = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='rejected'").fetchone()[0]
    cost = get_monthly_cost(conn)
    return {
        "total": total,
        "new": new,
        "notified": notified,
        "interested": interested,
        "applied": applied,
        "rejected": rejected,
        "monthly_cost_usd": round(cost, 4),
    }

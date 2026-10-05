"""Database layer - SQLite via stdlib sqlite3."""
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "pasti_sukses.db"

FIELDS = ["it", "design", "marketing", "finance", "other"]
LOCATIONS = ["remote", "jakarta", "bandung", "surabaya", "yogyakarta", "semarang", "medan", "makassar", "other"]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            created_at  INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS preferences (
            user_id     INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
            field       TEXT NOT NULL DEFAULT 'any',
            location    TEXT NOT NULL DEFAULT 'any',
            is_remote   INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT NOT NULL,
            title       TEXT NOT NULL,
            company     TEXT NOT NULL,
            location    TEXT NOT NULL DEFAULT '',
            is_remote   INTEGER NOT NULL DEFAULT 0,
            url         TEXT NOT NULL UNIQUE,
            category    TEXT NOT NULL DEFAULT 'other',
            posted_at   INTEGER,
            created_at  INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS deliveries (
            user_id     INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            job_id      INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            sent_at     INTEGER NOT NULL,
            PRIMARY KEY (user_id, job_id)
        );
        CREATE TABLE IF NOT EXISTS saved_jobs (
            user_id     INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            job_id      INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            saved_at    INTEGER NOT NULL,
            PRIMARY KEY (user_id, job_id)
        );
        CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category);
        CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);
        """
    )
    conn.commit()
    conn.close()


def upsert_user(user_id: int, username: str | None) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO users (user_id, username, created_at) VALUES (?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username",
        (user_id, username, int(time.time())),
    )
    conn.commit()
    conn.close()


def set_preferences(user_id: int, field: str, location: str, is_remote: bool) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO preferences (user_id, field, location, is_remote) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET field=excluded.field, location=excluded.location, is_remote=excluded.is_remote",
        (user_id, field, location, int(is_remote)),
    )
    conn.commit()
    conn.close()


def get_preferences(user_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM preferences WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_job(source: str, title: str, company: str, location: str, is_remote: bool, url: str, category: str, posted_at: int | None) -> int | None:
    """Insert a job; returns new job id, or None if duplicate."""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO jobs (source, title, company, location, is_remote, url, category, posted_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (source, title.strip()[:300], company.strip()[:200], location.strip()[:200], int(is_remote), url, category, posted_at, int(time.time())),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def find_matching_users(job_category: str, job_is_remote: bool, job_location: str) -> list[int]:
    """Users whose simple preference matches the job.

    Match rules (simple as agreed):
    - field: 'any' matches all, otherwise must equal job category (category 'other' only matches users choosing 'other' or 'any')
    - is_remote: user wants remote only -> job must be remote
    - location: 'any' matches all; 'remote' requires job remote; otherwise compares to job location text
    """
    conn = get_conn()
    rows = conn.execute("SELECT user_id, field, location, is_remote FROM preferences").fetchall()
    conn.close()
    loc = (job_location or "").lower()
    matched = []
    for r in rows:
        if r["field"] not in ("any", job_category):
            continue
        if r["is_remote"] and not job_is_remote:
            continue
        if r["location"] not in ("any",):
            if r["location"] == "remote":
                if not job_is_remote:
                    continue
            elif r["location"] not in loc:
                continue
        matched.append(r["user_id"])
    return matched


def mark_delivered(user_id: int, job_id: int) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO deliveries (user_id, job_id, sent_at) VALUES (?, ?, ?)",
        (user_id, job_id, int(time.time())),
    )
    conn.commit()
    conn.close()


def already_delivered(user_id: int, job_id: int) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM deliveries WHERE user_id = ? AND job_id = ?",
        (user_id, job_id),
    ).fetchone()
    conn.close()
    return row is not None


def latest_jobs(limit: int = 10, category: str | None = None) -> list[dict]:
    conn = get_conn()
    if category and category != "any":
        rows = conn.execute(
            "SELECT * FROM jobs WHERE category = ? ORDER BY created_at DESC, id DESC LIMIT ?",
            (category, limit),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def job_stats() -> dict:
    conn = get_conn()
    jobs = conn.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()["n"]
    users = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    conn.close()
    return {"jobs": jobs, "users": users}


def save_job(user_id: int, job_id: int) -> bool:
    """Bookmark a job for a user. Returns True if newly saved."""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO saved_jobs (user_id, job_id, saved_at) VALUES (?, ?, ?)",
            (user_id, job_id, int(time.time())),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def unsave_job(user_id: int, job_id: int) -> bool:
    """Remove a bookmark. Returns True if a row was deleted."""
    conn = get_conn()
    cur = conn.execute(
        "DELETE FROM saved_jobs WHERE user_id = ? AND job_id = ?",
        (user_id, job_id),
    )
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def get_saved_jobs(user_id: int, limit: int = 30) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT j.*, s.saved_at FROM saved_jobs s "
        "JOIN jobs j ON j.id = s.job_id "
        "WHERE s.user_id = ? ORDER BY s.saved_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def is_saved(user_id: int, job_id: int) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM saved_jobs WHERE user_id = ? AND job_id = ?",
        (user_id, job_id),
    ).fetchone()
    conn.close()
    return row is not None

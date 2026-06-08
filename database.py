import sqlite3
from pathlib import Path

DB_PATH = Path("data/agent.db")


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS brand_config (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            media_type   TEXT NOT NULL,
            media_url    TEXT NOT NULL,
            caption      TEXT,
            image_prompt TEXT,
            scheduled_at TEXT NOT NULL,
            status       TEXT DEFAULT 'pending',
            error        TEXT,
            published_at TEXT,
            created_at   TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS metrics_history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            date          TEXT NOT NULL,
            followers     INTEGER,
            impressions   INTEGER,
            reach         INTEGER,
            profile_views INTEGER,
            recorded_at   TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


# ── Brand config ─────────────────────────────────────────────────────────────

def get_brand_config() -> dict:
    conn = get_conn()
    rows = conn.execute("SELECT key, value FROM brand_config").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


def set_brand_config(data: dict):
    conn = get_conn()
    for key, value in data.items():
        conn.execute(
            "INSERT INTO brand_config (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
    conn.commit()
    conn.close()


# ── Scheduled posts ──────────────────────────────────────────────────────────

def add_post(media_type, media_url, caption, scheduled_at, image_prompt="") -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO scheduled_posts (media_type, media_url, caption, image_prompt, scheduled_at) VALUES (?,?,?,?,?)",
        (media_type, media_url, caption, image_prompt, scheduled_at),
    )
    post_id = c.lastrowid
    conn.commit()
    conn.close()
    return post_id


def get_pending_posts(before: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM scheduled_posts WHERE status='pending' AND scheduled_at <= ?",
        (before,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_post_status(post_id, status, error=None, published_at=None):
    conn = get_conn()
    conn.execute(
        "UPDATE scheduled_posts SET status=?, error=?, published_at=? WHERE id=?",
        (status, error, published_at, post_id),
    )
    conn.commit()
    conn.close()


def list_posts(status=None, limit=50) -> list[dict]:
    conn = get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM scheduled_posts WHERE status=? ORDER BY scheduled_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM scheduled_posts ORDER BY scheduled_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def cancel_post(post_id) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE scheduled_posts SET status='cancelled' WHERE id=? AND status='pending'",
        (post_id,),
    )
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

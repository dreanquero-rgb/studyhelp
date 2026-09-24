"""Persistence layer — stores ONLY the personal notes, so your work is never lost.

Two backends, chosen automatically:
- Postgres (Supabase) when a connection string is configured (see app/config.py).
- SQLite locally otherwise (for development).

Course content is NOT in the database: it lives in files under /content and is
managed via Claude Code. The database only keeps notes, keyed by lesson.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from . import config

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "studyhelp.db"

# The Postgres pool is a module-level singleton: modules are imported once, so
# it SURVIVES Streamlit reruns and connections are reused (no TLS handshake per
# query -> fast).
_pool = None
_initialized = False


def _get_pool():
    global _pool
    if _pool is None:
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        def _configure(conn) -> None:
            conn.prepare_threshold = None  # Supabase transaction-pooler friendly.

        _pool = ConnectionPool(
            config.get_db_url(),
            min_size=1,
            max_size=5,
            max_idle=300,
            kwargs={"autocommit": True, "row_factory": dict_row},
            configure=_configure,
            open=True,
        )
    return _pool


@contextmanager
def _conn():
    if config.using_postgres():
        with _get_pool().connection() as conn:
            yield conn
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def _adapt(sql: str) -> str:
    return sql.replace("?", "%s") if config.using_postgres() else sql


_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS notes (
    lesson_key  TEXT PRIMARY KEY,
    blocks_json TEXT NOT NULL DEFAULT '[]',
    updated_at  REAL NOT NULL
);
"""

_SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS notes (
    lesson_key  TEXT PRIMARY KEY,
    blocks_json TEXT NOT NULL DEFAULT '[]',
    updated_at  DOUBLE PRECISION NOT NULL
);
"""


def init_db() -> None:
    global _initialized
    if _initialized:
        return
    schema = _SCHEMA_PG if config.using_postgres() else _SCHEMA_SQLITE
    with _conn() as conn:
        for statement in schema.split(";"):
            if statement.strip():
                conn.execute(statement)
    _initialized = True


def get_note(lesson_key: str) -> list:
    with _conn() as conn:
        row = conn.execute(
            _adapt("SELECT blocks_json FROM notes WHERE lesson_key = ?"), (lesson_key,)
        ).fetchone()
        if row is None:
            return []
        row = dict(row)
        return json.loads(row["blocks_json"])


def save_note(lesson_key: str, blocks: list) -> None:
    with _conn() as conn:
        conn.execute(
            _adapt(
                "INSERT INTO notes (lesson_key, blocks_json, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(lesson_key) DO UPDATE SET "
                "blocks_json = excluded.blocks_json, updated_at = excluded.updated_at"
            ),
            (lesson_key, json.dumps(blocks, ensure_ascii=False), time.time()),
        )

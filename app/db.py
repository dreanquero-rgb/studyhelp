"""Livello dati di StudyHelp — funziona su due backend, scelto automaticamente:

- SQLite  : se non è configurata alcuna connessione (sviluppo locale).
- Postgres: se è presente una connessione Supabase (vedi app/config.py).

Le query sono scritte una sola volta con il segnaposto `?`; per Postgres
vengono adattate a `%s`. Le uniche differenze restano nello schema (tipi e
auto-incremento) e nel recupero dell'id appena inserito (RETURNING vs lastrowid).

Modello:
    users     -> account con ruolo e stato di approvazione
    courses   -> corsi (struttura globale, gestita dall'owner/admin)
    sections  -> sezioni dentro un corso
    lessons   -> lezioni dentro una sezione; content_json = materiale didattico
    notes     -> appunti personali di un utente su una lezione (blocks_json)
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from . import config

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "studyhelp.db"

# Il pool di connessioni Postgres è un singleton di modulo: i moduli vengono
# importati una sola volta, quindi il pool SOPRAVVIVE ai rerun di Streamlit e
# le connessioni vengono riusate (niente handshake TLS a ogni query -> veloce).
_pool = None
_initialized = False


def _get_pool():
    global _pool
    if _pool is None:
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        def _configure(conn) -> None:
            # Compatibile con il pooler Supabase in modalità "transaction".
            conn.prepare_threshold = None

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
    """Fornisce una connessione: dal pool (Postgres) o nuova (SQLite)."""
    if config.using_postgres():
        with _get_pool().connection() as conn:
            yield conn
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def _adapt(sql: str) -> str:
    return sql.replace("?", "%s") if config.using_postgres() else sql


def fetchone(sql: str, params: tuple = ()) -> dict | None:
    with _conn() as conn:
        row = conn.execute(_adapt(sql), params).fetchone()
        return dict(row) if row is not None else None


def fetchall(sql: str, params: tuple = ()) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(_adapt(sql), params).fetchall()
        return [dict(r) for r in rows]


def execute(sql: str, params: tuple = ()) -> None:
    with _conn() as conn:
        conn.execute(_adapt(sql), params)


def insert(sql: str, params: tuple = ()) -> int:
    """Esegue un INSERT e ritorna l'id della riga creata."""
    with _conn() as conn:
        if config.using_postgres():
            row = conn.execute(_adapt(sql) + " RETURNING id", params).fetchone()
            return int(row["id"])
        return int(conn.execute(sql, params).lastrowid)


# --------------------------------------------------------------------------- #
# Schema                                                                       #
# --------------------------------------------------------------------------- #
_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    status TEXT NOT NULL DEFAULT 'pending',
    anthropic_key TEXT NOT NULL DEFAULT '',
    ai_model TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    icon TEXT DEFAULT '📘',
    description TEXT DEFAULT '',
    position INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    content_json TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    blocks_json TEXT NOT NULL DEFAULT '[]',
    updated_at REAL NOT NULL,
    UNIQUE(user_id, lesson_id)
);
"""

_SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    status TEXT NOT NULL DEFAULT 'pending',
    anthropic_key TEXT NOT NULL DEFAULT '',
    ai_model TEXT NOT NULL DEFAULT '',
    created_at DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS courses (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL,
    icon TEXT DEFAULT '📘',
    description TEXT DEFAULT '',
    position INTEGER NOT NULL DEFAULT 0,
    created_at DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS sections (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS lessons (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    section_id BIGINT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    content_json TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS notes (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id BIGINT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    blocks_json TEXT NOT NULL DEFAULT '[]',
    updated_at DOUBLE PRECISION NOT NULL,
    UNIQUE(user_id, lesson_id)
);
"""


def init_db() -> None:
    # Esegue lo schema/migrazione/seed UNA VOLTA per processo (non a ogni rerun).
    global _initialized
    if _initialized:
        return
    schema = _SCHEMA_PG if config.using_postgres() else _SCHEMA_SQLITE
    with _conn() as conn:
        for statement in schema.split(";"):
            if statement.strip():
                conn.execute(statement)
    _migrate()
    _seed_from_json_if_empty()
    _initialized = True


def _migrate() -> None:
    """Aggiunge colonne mancanti a tabelle già esistenti (idempotente)."""
    for col in ("anthropic_key", "ai_model"):
        if config.using_postgres():
            execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} TEXT NOT NULL DEFAULT ''")
        else:
            try:
                execute(f"ALTER TABLE users ADD COLUMN {col} TEXT NOT NULL DEFAULT ''")
            except Exception:
                pass  # La colonna esiste già.


# --------------------------------------------------------------------------- #
# Seeding iniziale dai file JSON in /content                                    #
# --------------------------------------------------------------------------- #
def _seed_from_json_if_empty() -> None:
    if (fetchone("SELECT COUNT(*) AS c FROM courses") or {}).get("c", 0) > 0:
        return

    content_dir = Path(__file__).resolve().parent.parent / "content"
    index = content_dir / "courses.json"
    if not index.exists():
        return

    courses = json.loads(index.read_text(encoding="utf-8"))
    for pos, course in enumerate(courses):
        course_id = create_course(
            title=course.get("title", "Corso"),
            icon=course.get("icon", "📘"),
            description=course.get("description", ""),
            position=pos,
        )
        section_id = create_section(course_id, "Module 1", 0)
        for lpos, lesson_id in enumerate(course.get("lessons", [])):
            lpath = content_dir / course["id"] / f"{lesson_id}.json"
            if not lpath.exists():
                continue
            data = json.loads(lpath.read_text(encoding="utf-8"))
            create_lesson(
                section_id=section_id,
                title=data.get("title", lesson_id),
                content=data.get("blocks", []),
                position=lpos,
            )


# --------------------------------------------------------------------------- #
# Users                                                                        #
# --------------------------------------------------------------------------- #
def count_users() -> int:
    return (fetchone("SELECT COUNT(*) AS c FROM users") or {}).get("c", 0)


def create_user(email: str, password_hash: str, role: str, status: str) -> int:
    return insert(
        "INSERT INTO users (email, password_hash, role, status, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (email.lower().strip(), password_hash, role, status, time.time()),
    )


def get_user_by_email(email: str) -> dict | None:
    return fetchone("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))


def list_users() -> list[dict]:
    return fetchall("SELECT * FROM users ORDER BY created_at")


def set_user_status(user_id: int, status: str) -> None:
    execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))


def set_user_role(user_id: int, role: str) -> None:
    execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))


def set_user_ai(user_id: int, anthropic_key: str, ai_model: str) -> None:
    """Salva (persistente) la chiave AI e il modello scelto per l'utente."""
    execute(
        "UPDATE users SET anthropic_key = ?, ai_model = ? WHERE id = ?",
        (anthropic_key, ai_model, user_id),
    )


# --------------------------------------------------------------------------- #
# Courses / Sections / Lessons                                                 #
# --------------------------------------------------------------------------- #
def create_course(title: str, icon: str = "📘", description: str = "", position: int = 0) -> int:
    return insert(
        "INSERT INTO courses (title, icon, description, position, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (title, icon, description, position, time.time()),
    )


def list_courses() -> list[dict]:
    return fetchall("SELECT * FROM courses ORDER BY position, id")


def update_course(course_id: int, **fields: Any) -> None:
    _update_row("courses", course_id, fields)


def delete_course(course_id: int) -> None:
    _delete_row("courses", course_id)


def create_section(course_id: int, title: str, position: int = 0) -> int:
    return insert(
        "INSERT INTO sections (course_id, title, position) VALUES (?, ?, ?)",
        (course_id, title, position),
    )


def list_sections(course_id: int) -> list[dict]:
    return fetchall(
        "SELECT * FROM sections WHERE course_id = ? ORDER BY position, id", (course_id,)
    )


def update_section(section_id: int, **fields: Any) -> None:
    _update_row("sections", section_id, fields)


def delete_section(section_id: int) -> None:
    _delete_row("sections", section_id)


def create_lesson(section_id: int, title: str, content: list | None = None, position: int = 0) -> int:
    return insert(
        "INSERT INTO lessons (section_id, title, position, content_json) VALUES (?, ?, ?, ?)",
        (section_id, title, position, json.dumps(content or [], ensure_ascii=False)),
    )


def list_lessons(section_id: int) -> list[dict]:
    return fetchall(
        "SELECT id, section_id, title, position FROM lessons "
        "WHERE section_id = ? ORDER BY position, id",
        (section_id,),
    )


def get_lesson(lesson_id: int) -> dict | None:
    lesson = fetchone("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    if lesson is None:
        return None
    lesson["content"] = json.loads(lesson.pop("content_json") or "[]")
    return lesson


def update_lesson(lesson_id: int, **fields: Any) -> None:
    if "content" in fields:
        fields["content_json"] = json.dumps(fields.pop("content"), ensure_ascii=False)
    _update_row("lessons", lesson_id, fields)


def delete_lesson(lesson_id: int) -> None:
    _delete_row("lessons", lesson_id)


# --------------------------------------------------------------------------- #
# Notes (per utente, per lezione)                                             #
# --------------------------------------------------------------------------- #
def get_note(user_id: int, lesson_id: int) -> list:
    row = fetchone(
        "SELECT blocks_json FROM notes WHERE user_id = ? AND lesson_id = ?",
        (user_id, lesson_id),
    )
    return json.loads(row["blocks_json"]) if row else []


def save_note(user_id: int, lesson_id: int, blocks: list) -> None:
    execute(
        "INSERT INTO notes (user_id, lesson_id, blocks_json, updated_at) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(user_id, lesson_id) DO UPDATE SET "
        "blocks_json = excluded.blocks_json, updated_at = excluded.updated_at",
        (user_id, lesson_id, json.dumps(blocks, ensure_ascii=False), time.time()),
    )


# --------------------------------------------------------------------------- #
# Helper generici                                                             #
# --------------------------------------------------------------------------- #
_ALLOWED_COLUMNS = {
    "courses": {"title", "icon", "description", "position"},
    "sections": {"title", "position", "course_id"},
    "lessons": {"title", "position", "content_json", "section_id"},
}


def _update_row(table: str, row_id: int, fields: dict) -> None:
    allowed = _ALLOWED_COLUMNS.get(table, set())
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    execute(f"UPDATE {table} SET {cols} WHERE id = ?", (*fields.values(), row_id))


def _delete_row(table: str, row_id: int) -> None:
    execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))

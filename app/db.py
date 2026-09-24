"""Livello dati di StudyHelp.

Fase 1: backend SQLite (funziona subito, in locale).
Lo schema e le query sono pensati per essere portati su Postgres/Supabase
con modifiche minime (stesse tabelle, stesse colonne).

Modello:
    users     -> account con ruolo e stato di approvazione
    courses   -> corsi (struttura globale, gestita dall'owner/admin)
    sections  -> sezioni dentro un corso
    lessons   -> lezioni dentro una sezione; content_json = materiale didattico
    notes     -> appunti personali di un utente su una lezione (blocks_json)

Tutti i contenuti "a blocchi" (materiale lezione e appunti) sono liste JSON,
così si modificano facilmente senza cambiare lo schema del database.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "studyhelp.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'student',   -- owner | admin | student
    status        TEXT NOT NULL DEFAULT 'pending',   -- pending | approved | blocked
    created_at    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    icon        TEXT DEFAULT '📘',
    description TEXT DEFAULT '',
    position    INTEGER NOT NULL DEFAULT 0,
    created_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS sections (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title     TEXT NOT NULL,
    position  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS lessons (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id   INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    position     INTEGER NOT NULL DEFAULT 0,
    content_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id   INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    blocks_json TEXT NOT NULL DEFAULT '[]',
    updated_at  REAL NOT NULL,
    UNIQUE(user_id, lesson_id)
);
"""


def init_db() -> None:
    conn = _connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
    _seed_from_json_if_empty()


# --------------------------------------------------------------------------- #
# Seeding: importa i corsi JSON esistenti la prima volta (così il materiale    #
# di "Securities and Investment" c'è già ed è poi modificabile dall'app).      #
# --------------------------------------------------------------------------- #
def _seed_from_json_if_empty() -> None:
    conn = _connect()
    try:
        n = conn.execute("SELECT COUNT(*) AS c FROM courses").fetchone()["c"]
        if n > 0:
            return
    finally:
        conn.close()

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
    conn = _connect()
    try:
        return conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    finally:
        conn.close()


def create_user(email: str, password_hash: str, role: str, status: str) -> int:
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, role, status, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (email.lower().strip(), password_hash, role, status, time.time()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_users() -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def set_user_status(user_id: int, status: str) -> None:
    conn = _connect()
    try:
        conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
        conn.commit()
    finally:
        conn.close()


def set_user_role(user_id: int, role: str) -> None:
    conn = _connect()
    try:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Courses / Sections / Lessons                                                 #
# --------------------------------------------------------------------------- #
def create_course(title: str, icon: str = "📘", description: str = "", position: int = 0) -> int:
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO courses (title, icon, description, position, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, icon, description, position, time.time()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_courses() -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM courses ORDER BY position, id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_course(course_id: int, **fields: Any) -> None:
    _update_row("courses", course_id, fields)


def delete_course(course_id: int) -> None:
    _delete_row("courses", course_id)


def create_section(course_id: int, title: str, position: int = 0) -> int:
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO sections (course_id, title, position) VALUES (?, ?, ?)",
            (course_id, title, position),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_sections(course_id: int) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM sections WHERE course_id = ? ORDER BY position, id",
            (course_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_section(section_id: int, **fields: Any) -> None:
    _update_row("sections", section_id, fields)


def delete_section(section_id: int) -> None:
    _delete_row("sections", section_id)


def create_lesson(section_id: int, title: str, content: list | None = None, position: int = 0) -> int:
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO lessons (section_id, title, position, content_json) "
            "VALUES (?, ?, ?, ?)",
            (section_id, title, position, json.dumps(content or [], ensure_ascii=False)),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_lessons(section_id: int) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, section_id, title, position FROM lessons "
            "WHERE section_id = ? ORDER BY position, id",
            (section_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_lesson(lesson_id: int) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
        if not row:
            return None
        lesson = dict(row)
        lesson["content"] = json.loads(lesson.pop("content_json") or "[]")
        return lesson
    finally:
        conn.close()


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
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT blocks_json FROM notes WHERE user_id = ? AND lesson_id = ?",
            (user_id, lesson_id),
        ).fetchone()
        return json.loads(row["blocks_json"]) if row else []
    finally:
        conn.close()


def save_note(user_id: int, lesson_id: int, blocks: list) -> None:
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO notes (user_id, lesson_id, blocks_json, updated_at) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, lesson_id) DO UPDATE SET "
            "blocks_json = excluded.blocks_json, updated_at = excluded.updated_at",
            (user_id, lesson_id, json.dumps(blocks, ensure_ascii=False), time.time()),
        )
        conn.commit()
    finally:
        conn.close()


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
    conn = _connect()
    try:
        conn.execute(f"UPDATE {table} SET {cols} WHERE id = ?", (*fields.values(), row_id))
        conn.commit()
    finally:
        conn.close()


def _delete_row(table: str, row_id: int) -> None:
    conn = _connect()
    try:
        conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
        conn.commit()
    finally:
        conn.close()

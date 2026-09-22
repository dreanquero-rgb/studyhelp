"""Caricamento dei contenuti (corsi e lezioni) dai file JSON in /content.

Struttura attesa:

    content/
        courses.json                     -> elenco dei corsi + ordine delle lezioni
        <course_id>/
            <lesson_id>.json             -> una lezione

Tutto è "data-driven": per aggiungere una lezione basta creare un file JSON,
senza toccare il codice dell'app.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Radice dei contenuti, relativa alla root del progetto.
CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_courses() -> list[dict]:
    """Ritorna l'elenco dei corsi definiti in content/courses.json.

    Ogni corso ha almeno: id, title. Opzionali: description, icon, lessons.
    """
    index_path = CONTENT_DIR / "courses.json"
    if not index_path.exists():
        return []
    courses = _read_json(index_path)
    return courses if isinstance(courses, list) else []


def load_lesson(course_id: str, lesson_id: str) -> dict | None:
    """Carica una singola lezione dal file content/<course_id>/<lesson_id>.json."""
    lesson_path = CONTENT_DIR / course_id / f"{lesson_id}.json"
    if not lesson_path.exists():
        return None
    return _read_json(lesson_path)


def get_course(course_id: str) -> dict | None:
    for course in load_courses():
        if course.get("id") == course_id:
            return course
    return None


def list_lessons(course: dict) -> list[dict]:
    """Ritorna i metadati (id + title) delle lezioni di un corso, nell'ordine dato.

    Se il file di una lezione manca viene ignorato, così l'indice può elencare
    lezioni "in arrivo" senza rompere l'app.
    """
    lessons: list[dict] = []
    for lesson_id in course.get("lessons", []):
        data = load_lesson(course["id"], lesson_id)
        if data is None:
            continue
        lessons.append(
            {
                "id": lesson_id,
                "title": data.get("title", lesson_id),
                "summary": data.get("summary", ""),
            }
        )
    return lessons

"""Course content loaded from files in /content (managed via Claude Code).

Structure:

    content/
        courses.json                 -> list of courses, each with sections+lessons
        <course_id>/
            <lesson_id>.json         -> a lesson (title + blocks)

courses.json example:

    [
      {
        "id": "securities-and-investment",
        "title": "Securities and Investment",
        "icon": "📈",
        "description": "...",
        "sections": [
          {"id": "module-1", "title": "Module 1", "lessons": ["lesson-01"]}
        ]
      }
    ]

Content is read directly from files at runtime, so editing a file (and pushing)
updates the site — no in-app content management needed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"


def _read(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_courses() -> list[dict]:
    index = CONTENT_DIR / "courses.json"
    if not index.exists():
        return []
    courses = _read(index)
    return courses if isinstance(courses, list) else []


def get_course(course_id: str) -> dict | None:
    for course in load_courses():
        if course.get("id") == course_id:
            return course
    return None


def get_section(course: dict, section_id: str) -> dict | None:
    for section in course.get("sections", []):
        if section.get("id") == section_id:
            return section
    return None


def load_lesson(course_id: str, lesson_id: str) -> dict | None:
    path = CONTENT_DIR / course_id / f"{lesson_id}.json"
    if not path.exists():
        return None
    return _read(path)


def lesson_key(course_id: str, lesson_id: str) -> str:
    """Stable key used to store this lesson's notes in the database."""
    return f"{course_id}/{lesson_id}"

"""Study page: browse courses/sections/lessons (from files), material + notes."""

from __future__ import annotations

import streamlit as st

from . import content
from .blocks import render_block
from .ui_notes import render_notes


def study_page() -> None:
    courses = content.load_courses()
    if not courses:
        st.title("📚 Study")
        st.info("No courses yet.")
        return

    course = st.selectbox(
        "Course", options=courses, format_func=lambda c: f"{c.get('icon', '📘')} {c['title']}"
    )
    sections = course.get("sections", [])
    if not sections:
        st.title(f"{course.get('icon', '📘')} {course['title']}")
        st.info("This course has no sections yet.")
        return

    col1, col2 = st.columns(2)
    section = col1.selectbox("Section", options=sections, format_func=lambda s: s["title"])
    lesson_ids = section.get("lessons", [])
    if not lesson_ids:
        st.title(f"{course.get('icon', '📘')} {course['title']}")
        st.info("This section has no lessons yet.")
        return

    lesson_id = col2.selectbox(
        "Lesson",
        options=lesson_ids,
        format_func=lambda lid: (content.load_lesson(course["id"], lid) or {}).get("title", lid),
    )

    lesson = content.load_lesson(course["id"], lesson_id)
    if lesson is None:
        st.error("Lesson file not found.")
        return

    key = content.lesson_key(course["id"], lesson_id)
    st.title(lesson.get("title", lesson_id))
    st.divider()

    tab_material, tab_notes = st.tabs(["📖 Material", "🗒️ Notes"])

    with tab_material:
        blocks = lesson.get("blocks", [])
        if not blocks:
            st.info("This lesson has no material yet.")
        for idx, block in enumerate(blocks):
            render_block(block, key=f"study_{key}_b{idx}")
            st.write("")

    with tab_notes:
        render_notes(key)

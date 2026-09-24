"""Study page: browse courses/sections/lessons, material + notes."""

from __future__ import annotations

import streamlit as st

from . import db
from .blocks import render_block
from .ui_notes import render_notes


def study_page(user: dict) -> None:
    courses = db.list_courses()
    if not courses:
        st.title("📚 Study")
        st.info("No courses yet. An admin can create them in **Manage content**.")
        return

    # --- Selectors: course -> section -> lesson ---
    course = st.selectbox(
        "Course", options=courses, format_func=lambda c: f"{c['icon']} {c['title']}"
    )
    sections = db.list_sections(course["id"])
    if not sections:
        st.title(f"{course['icon']} {course['title']}")
        st.info("This course has no sections yet.")
        return

    col1, col2 = st.columns(2)
    section = col1.selectbox("Section", options=sections, format_func=lambda s: s["title"])
    lessons = db.list_lessons(section["id"])
    if not lessons:
        st.title(f"{course['icon']} {course['title']}")
        st.info("This section has no lessons yet.")
        return
    lesson_meta = col2.selectbox("Lesson", options=lessons, format_func=lambda l: l["title"])

    lesson = db.get_lesson(lesson_meta["id"])
    st.session_state["progress"]["visited"].add(f"{course['id']}/{lesson['id']}")

    st.title(lesson["title"])
    st.divider()

    tab_material, tab_notes = st.tabs(["📖 Material", "🗒️ Notes"])

    with tab_material:
        blocks = lesson.get("content", [])
        if not blocks:
            st.info("This lesson has no material yet. Add it in **Manage content**.")
        for idx, block in enumerate(blocks):
            render_block(block, key=f"study_{lesson['id']}_b{idx}")
            st.write("")

    with tab_notes:
        render_notes(user, lesson["id"])

"""Content management (owner/admin): CRUD for courses, sections and lessons."""

from __future__ import annotations

import json

import streamlit as st

from . import db


def _course_editor() -> None:
    st.subheader("📚 Courses")
    for c in db.list_courses():
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 5, 1])
            icon = col1.text_input("Icon", value=c["icon"], key=f"cico_{c['id']}", label_visibility="collapsed")
            title = col2.text_input("Title", value=c["title"], key=f"ctit_{c['id']}", label_visibility="collapsed")
            if col3.button("💾", key=f"csave_{c['id']}", help="Save"):
                db.update_course(c["id"], title=title, icon=icon)
                st.toast("Course updated")
                st.rerun()
            desc = st.text_area("Description", value=c["description"], key=f"cdesc_{c['id']}")
            cold1, cold2 = st.columns([1, 1])
            if cold1.button("💾 Save description", key=f"cdsave_{c['id']}"):
                db.update_course(c["id"], description=desc)
                st.toast("Description saved")
            if cold2.button("🗑 Delete course", key=f"cdel_{c['id']}"):
                db.delete_course(c["id"])
                st.rerun()

    with st.form("new_course"):
        st.write("**New course**")
        col1, col2 = st.columns([1, 5])
        icon = col1.text_input("Icon", value="📘")
        title = col2.text_input("Course title")
        if st.form_submit_button("➕ Create course") and title.strip():
            db.create_course(title.strip(), icon=icon or "📘", position=len(db.list_courses()))
            st.rerun()


def _section_lesson_editor() -> None:
    courses = db.list_courses()
    if not courses:
        return
    st.subheader("🗂️ Sections and lessons")
    course = st.selectbox(
        "Course to edit",
        options=courses,
        format_func=lambda c: f"{c['icon']} {c['title']}",
    )

    sections = db.list_sections(course["id"])
    for s in sections:
        with st.container(border=True):
            col1, col2, col3 = st.columns([5, 1, 1])
            title = col1.text_input("Section", value=s["title"], key=f"stit_{s['id']}", label_visibility="collapsed")
            if col2.button("💾", key=f"ssave_{s['id']}", help="Rename section"):
                db.update_section(s["id"], title=title)
                st.rerun()
            if col3.button("🗑", key=f"sdel_{s['id']}", help="Delete section"):
                db.delete_section(s["id"])
                st.rerun()

            for les in db.list_lessons(s["id"]):
                lcol1, lcol2, lcol3 = st.columns([5, 1, 1])
                ltitle = lcol1.text_input(
                    "Lesson", value=les["title"], key=f"ltit_{les['id']}", label_visibility="collapsed"
                )
                if lcol2.button("💾", key=f"lsave_{les['id']}", help="Rename lesson"):
                    db.update_lesson(les["id"], title=ltitle)
                    st.rerun()
                if lcol3.button("🗑", key=f"ldel_{les['id']}", help="Delete lesson"):
                    db.delete_lesson(les["id"])
                    st.rerun()
                _lesson_content_editor(les["id"])

            with st.form(f"new_lesson_{s['id']}"):
                new_title = st.text_input("New lesson", key=f"nl_{s['id']}")
                if st.form_submit_button("➕ Add lesson") and new_title.strip():
                    db.create_lesson(s["id"], new_title.strip(), position=len(db.list_lessons(s["id"])))
                    st.rerun()

    with st.form(f"new_section_{course['id']}"):
        new_sec = st.text_input("New section")
        if st.form_submit_button("➕ Add section") and new_sec.strip():
            db.create_section(course["id"], new_sec.strip(), position=len(sections))
            st.rerun()


def _lesson_content_editor(lesson_id: int) -> None:
    """Editor for the lesson teaching material (blocks as JSON)."""
    with st.expander("📝 Edit lesson material (advanced JSON)"):
        lesson = db.get_lesson(lesson_id)
        current = json.dumps(lesson["content"], ensure_ascii=False, indent=2)
        st.caption(
            "Supported blocks: objectives, markdown, key_terms, flashcards, "
            "quiz, calculator, summary. See the README for the format."
        )
        edited = st.text_area("Blocks (JSON)", value=current, height=300, key=f"lc_{lesson_id}")
        if st.button("💾 Save material", key=f"lcsave_{lesson_id}"):
            try:
                blocks = json.loads(edited)
                if not isinstance(blocks, list):
                    raise ValueError("Content must be a list of blocks.")
                db.update_lesson(lesson_id, content=blocks)
                st.success("Material saved.")
            except (json.JSONDecodeError, ValueError) as exc:
                st.error(f"Invalid JSON: {exc}")


def manage_page() -> None:
    st.title("✏️ Manage content")
    tab1, tab2 = st.tabs(["Courses", "Sections & Lessons"])
    with tab1:
        _course_editor()
    with tab2:
        _section_lesson_editor()

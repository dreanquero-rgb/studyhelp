"""Gestione contenuti (owner/admin): CRUD di corsi, sezioni e lezioni."""

from __future__ import annotations

import json

import streamlit as st

from . import db


def _course_editor() -> None:
    st.subheader("📚 Corsi")
    for c in db.list_courses():
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 5, 1])
            icon = col1.text_input("Icona", value=c["icon"], key=f"cico_{c['id']}", label_visibility="collapsed")
            title = col2.text_input("Titolo", value=c["title"], key=f"ctit_{c['id']}", label_visibility="collapsed")
            if col3.button("💾", key=f"csave_{c['id']}", help="Salva"):
                db.update_course(c["id"], title=title, icon=icon)
                st.toast("Corso aggiornato")
                st.rerun()
            desc = st.text_area("Descrizione", value=c["description"], key=f"cdesc_{c['id']}")
            cold1, cold2 = st.columns([1, 1])
            if cold1.button("💾 Salva descrizione", key=f"cdsave_{c['id']}"):
                db.update_course(c["id"], description=desc)
                st.toast("Descrizione salvata")
            if cold2.button("🗑 Elimina corso", key=f"cdel_{c['id']}"):
                db.delete_course(c["id"])
                st.rerun()

    with st.form("new_course"):
        st.write("**Nuovo corso**")
        col1, col2 = st.columns([1, 5])
        icon = col1.text_input("Icona", value="📘")
        title = col2.text_input("Titolo del corso")
        if st.form_submit_button("➕ Crea corso") and title.strip():
            db.create_course(title.strip(), icon=icon or "📘", position=len(db.list_courses()))
            st.rerun()


def _section_lesson_editor() -> None:
    courses = db.list_courses()
    if not courses:
        return
    st.subheader("🗂️ Sezioni e lezioni")
    course = st.selectbox(
        "Corso da modificare",
        options=courses,
        format_func=lambda c: f"{c['icon']} {c['title']}",
    )

    sections = db.list_sections(course["id"])
    for s in sections:
        with st.container(border=True):
            col1, col2, col3 = st.columns([5, 1, 1])
            title = col1.text_input("Sezione", value=s["title"], key=f"stit_{s['id']}", label_visibility="collapsed")
            if col2.button("💾", key=f"ssave_{s['id']}", help="Rinomina sezione"):
                db.update_section(s["id"], title=title)
                st.rerun()
            if col3.button("🗑", key=f"sdel_{s['id']}", help="Elimina sezione"):
                db.delete_section(s["id"])
                st.rerun()

            for les in db.list_lessons(s["id"]):
                lcol1, lcol2, lcol3 = st.columns([5, 1, 1])
                ltitle = lcol1.text_input(
                    "Lezione", value=les["title"], key=f"ltit_{les['id']}", label_visibility="collapsed"
                )
                if lcol2.button("💾", key=f"lsave_{les['id']}", help="Rinomina lezione"):
                    db.update_lesson(les["id"], title=ltitle)
                    st.rerun()
                if lcol3.button("🗑", key=f"ldel_{les['id']}", help="Elimina lezione"):
                    db.delete_lesson(les["id"])
                    st.rerun()
                _lesson_content_editor(les["id"])

            with st.form(f"new_lesson_{s['id']}"):
                new_title = st.text_input("Nuova lezione", key=f"nl_{s['id']}")
                if st.form_submit_button("➕ Aggiungi lezione") and new_title.strip():
                    db.create_lesson(s["id"], new_title.strip(), position=len(db.list_lessons(s["id"])))
                    st.rerun()

    with st.form(f"new_section_{course['id']}"):
        new_sec = st.text_input("Nuova sezione")
        if st.form_submit_button("➕ Aggiungi sezione") and new_sec.strip():
            db.create_section(course["id"], new_sec.strip(), position=len(sections))
            st.rerun()


def _lesson_content_editor(lesson_id: int) -> None:
    """Editor del materiale didattico della lezione (blocchi come JSON)."""
    with st.expander("📝 Modifica materiale della lezione (JSON avanzato)"):
        lesson = db.get_lesson(lesson_id)
        current = json.dumps(lesson["content"], ensure_ascii=False, indent=2)
        st.caption(
            "I blocchi supportati: objectives, markdown, key_terms, flashcards, "
            "quiz, calculator, summary. Vedi il README per il formato."
        )
        edited = st.text_area("Blocchi (JSON)", value=current, height=300, key=f"lc_{lesson_id}")
        if st.button("💾 Salva materiale", key=f"lcsave_{lesson_id}"):
            try:
                blocks = json.loads(edited)
                if not isinstance(blocks, list):
                    raise ValueError("Il contenuto deve essere una lista di blocchi.")
                db.update_lesson(lesson_id, content=blocks)
                st.success("Materiale salvato.")
            except (json.JSONDecodeError, ValueError) as exc:
                st.error(f"JSON non valido: {exc}")


def manage_page() -> None:
    st.title("✏️ Gestisci contenuti")
    tab1, tab2 = st.tabs(["Corsi", "Sezioni & Lezioni"])
    with tab1:
        _course_editor()
    with tab2:
        _section_lesson_editor()

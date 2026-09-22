"""StudyHelp — piattaforma di studio interattiva.

Ogni corso è una sezione; ogni corso contiene lezioni; ogni lezione è una
pagina di studio interattiva (teoria, concetti chiave, flashcard, quiz,
esercizi). I contenuti stanno in /content come file JSON, quindi aggiungere
materiale non richiede di toccare il codice.

Avvio locale:   streamlit run streamlit_app.py
"""

from __future__ import annotations

import streamlit as st

from app.blocks import render_block
from app.loader import get_course, list_lessons, load_courses, load_lesson

st.set_page_config(
    page_title="StudyHelp",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_state() -> None:
    if "progress" not in st.session_state:
        st.session_state["progress"] = {"visited": set(), "quiz_scores": {}}


def sidebar_navigation(courses: list[dict]) -> tuple[str, str] | tuple[None, None]:
    """Disegna la navigazione e ritorna (course_id, lesson_id) selezionati."""
    st.sidebar.title("🎓 StudyHelp")
    st.sidebar.caption("La tua piattaforma di studio interattiva")

    if not courses:
        st.sidebar.warning("Nessun corso disponibile.")
        return None, None

    course_labels = {c["id"]: f"{c.get('icon', '📘')}  {c['title']}" for c in courses}
    course_id = st.sidebar.selectbox(
        "Corso",
        options=[c["id"] for c in courses],
        format_func=lambda cid: course_labels[cid],
    )

    course = get_course(course_id)
    lessons = list_lessons(course) if course else []
    if not lessons:
        st.sidebar.info("Questo corso non ha ancora lezioni caricate.")
        return course_id, None

    lesson_id = st.sidebar.radio(
        "Lezioni",
        options=[ls["id"] for ls in lessons],
        format_func=lambda lid: next(ls["title"] for ls in lessons if ls["id"] == lid),
    )
    return course_id, lesson_id


def render_progress_sidebar(course: dict, lessons: list[dict]) -> None:
    st.sidebar.divider()
    visited = st.session_state["progress"]["visited"]
    total = len(lessons)
    done = sum(1 for ls in lessons if f"{course['id']}/{ls['id']}" in visited)
    st.sidebar.markdown("**Avanzamento del corso**")
    st.sidebar.progress(done / total if total else 0.0)
    st.sidebar.caption(f"{done} / {total} lezioni aperte")


def render_lesson(course_id: str, lesson_id: str) -> None:
    lesson = load_lesson(course_id, lesson_id)
    if lesson is None:
        st.error("Lezione non trovata.")
        return

    # Segna la lezione come visitata.
    st.session_state["progress"]["visited"].add(f"{course_id}/{lesson_id}")

    st.title(lesson.get("title", lesson_id))
    if lesson.get("summary"):
        st.markdown(f"*{lesson['summary']}*")
    st.divider()

    blocks = lesson.get("blocks", [])
    for i, block in enumerate(blocks):
        key = f"{course_id}__{lesson_id}__b{i}"
        render_block(block, key)
        st.write("")  # spaziatura tra blocchi


def main() -> None:
    init_state()
    courses = load_courses()
    course_id, lesson_id = sidebar_navigation(courses)

    if not course_id:
        st.title("🎓 StudyHelp")
        st.write("Aggiungi un corso in `content/courses.json` per iniziare.")
        return

    course = get_course(course_id)
    lessons = list_lessons(course) if course else []
    if course:
        render_progress_sidebar(course, lessons)

    if not lesson_id:
        st.title(f"{course.get('icon', '📘')} {course.get('title', course_id)}")
        if course.get("description"):
            st.markdown(course["description"])
        st.info("Seleziona una lezione dal menu a sinistra per iniziare a studiare.")
        return

    render_lesson(course_id, lesson_id)


if __name__ == "__main__":
    main()

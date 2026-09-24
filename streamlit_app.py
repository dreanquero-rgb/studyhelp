"""StudyHelp — personal interactive study site.

- Single user: no login.
- Course content lives in files under /content (managed via Claude Code).
- Personal notes (text + runnable Python code) are saved to the database so
  your work is never lost.

Run locally:   streamlit run streamlit_app.py
"""

from __future__ import annotations

import streamlit as st

from app import config, db
from app.ui_study import study_page

st.set_page_config(page_title="StudyHelp", page_icon="🎓", layout="wide")


def _init_db_or_explain() -> None:
    try:
        db.init_db()
    except Exception as exc:  # noqa: BLE001
        st.error("❌ Could not connect to the database (Supabase).")
        st.code(f"{type(exc).__name__}: {exc}", language="text")
        st.markdown(
            "Check the `db_url` value in the app **Secrets** (use the Supabase "
            "**pooler** URI and the plain password, no `[ ]` brackets)."
        )
        st.stop()


_init_db_or_explain()

st.session_state.setdefault("progress", {"visited": set(), "quiz_scores": {}})

# Sidebar
st.sidebar.title("🎓 StudyHelp")
st.sidebar.caption("Your interactive study site")
backend = "🟢 Supabase (Postgres)" if config.using_postgres() else "🟡 SQLite (local)"
st.sidebar.caption(f"Notes saved to: {backend}")

study_page()

"""StudyHelp — piattaforma di studio interattiva multi-utente.

- Ogni utente accede con un account personale (il primo registrato è l'OWNER).
- Gli account nuovi restano "in attesa" finché l'owner non li approva.
- Corsi / sezioni / lezioni sono gestibili dall'app (owner/admin).
- Ogni utente ha i propri appunti per lezione, con blocchi testo / codice
  Python eseguibile / AI (con la propria chiave).

Avvio locale:   streamlit run streamlit_app.py
"""

from __future__ import annotations

import streamlit as st

from app import auth, db
from app.ai import DEFAULT_MODEL, MODELS
from app.ui_admin import admin_page
from app.ui_auth import login_register_screen, pending_screen
from app.ui_manage import manage_page
from app.ui_study import study_page

st.set_page_config(page_title="StudyHelp", page_icon="🎓", layout="wide")

db.init_db()


def init_state() -> None:
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("ai_key", "")
    st.session_state.setdefault("ai_model", DEFAULT_MODEL)
    st.session_state.setdefault("progress", {"visited": set(), "quiz_scores": {}})
    st.session_state.setdefault("page", "study")


def sidebar_ai_settings() -> None:
    with st.sidebar.expander("🤖 Impostazioni AI", expanded=False):
        st.caption(
            "Inserisci la TUA chiave API di Anthropic per usare l'AI nelle note. "
            "La chiave resta solo in questa sessione, non viene salvata."
        )
        st.session_state["ai_key"] = st.text_input(
            "Chiave API Anthropic",
            value=st.session_state.get("ai_key", ""),
            type="password",
            placeholder="sk-ant-...",
        )
        st.session_state["ai_model"] = st.selectbox(
            "Modello",
            options=list(MODELS.keys()),
            format_func=lambda m: MODELS[m],
            index=list(MODELS.keys()).index(st.session_state.get("ai_model", DEFAULT_MODEL)),
        )
        st.link_button("Ottieni una chiave API", "https://console.anthropic.com/settings/keys")


def sidebar_nav(user: dict) -> None:
    st.sidebar.title("🎓 StudyHelp")
    st.sidebar.write(f"👤 **{user['email']}**")
    st.sidebar.caption(f"Ruolo: {user['role']}")

    pages = {"study": "📚 Studia"}
    if auth.is_admin(user):
        pages["manage"] = "✏️ Gestisci contenuti"
        pages["admin"] = "👥 Utenti"

    choice = st.sidebar.radio(
        "Menu",
        options=list(pages.keys()),
        format_func=lambda k: pages[k],
        key="page",
    )

    st.sidebar.divider()
    sidebar_ai_settings()
    st.sidebar.divider()
    if st.sidebar.button("Esci", use_container_width=True):
        st.session_state["user"] = None
        st.rerun()


def main() -> None:
    init_state()
    user = st.session_state.get("user")

    # Non autenticato -> schermata login/registrazione.
    if not user:
        login_register_screen()
        return

    # Autenticato ma non ancora approvato.
    if user.get("status") != "approved":
        pending_screen(user)
        return

    sidebar_nav(user)
    page = st.session_state.get("page", "study")

    if page == "manage" and auth.is_admin(user):
        manage_page()
    elif page == "admin" and auth.is_admin(user):
        admin_page(user)
    else:
        study_page(user)


if __name__ == "__main__":
    main()

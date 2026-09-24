"""StudyHelp — interactive multi-user study platform.

- Every user signs in with a personal account (the first to register is the OWNER).
- New accounts stay "pending" until the owner approves them.
- Courses / sections / lessons are managed from the app (owner/admin).
- Each user has their own notes per lesson, with text / runnable Python code /
  AI blocks (using their own API key, saved to their account).

Run locally:   streamlit run streamlit_app.py
"""

from __future__ import annotations

import streamlit as st

from app import auth, config, db
from app.ai import DEFAULT_MODEL, MODELS
from app.ui_admin import admin_page
from app.ui_auth import login_register_screen, pending_screen
from app.ui_manage import manage_page
from app.ui_study import study_page

st.set_page_config(page_title="StudyHelp", page_icon="🎓", layout="wide")


def _init_db_or_explain() -> None:
    """Initialize the database, showing the real error if something goes wrong."""
    try:
        db.init_db()
    except Exception as exc:  # noqa: BLE001
        st.error("❌ Could not connect to the Supabase database.")
        st.code(f"{type(exc).__name__}: {exc}", language="text")
        st.markdown(
            "**Most common causes:**\n"
            "- Wrong password, or the `[ ]` brackets left in by mistake "
            "(it must be just the password).\n"
            "- Password with special characters not URL-encoded (`@ : / # ? %`).\n"
            "- Using the *Direct connection* URI instead of the **pooler** "
            "(`...pooler.supabase.com:6543`).\n\n"
            "Fix the `db_url` value in the app **Secrets** and reboot."
        )
        st.stop()


_init_db_or_explain()


def init_state() -> None:
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("ai_key", "")
    st.session_state.setdefault("ai_workspace", "")
    st.session_state.setdefault("ai_model", DEFAULT_MODEL)
    st.session_state.setdefault("ai_loaded", False)
    st.session_state.setdefault("progress", {"visited": set(), "quiz_scores": {}})
    st.session_state.setdefault("page", "study")


def load_ai_settings_once(user: dict) -> None:
    """After login, load the saved API key/model from the user's account once."""
    if not st.session_state["ai_loaded"]:
        st.session_state["ai_key"] = user.get("anthropic_key", "") or ""
        st.session_state["ai_workspace"] = user.get("anthropic_workspace", "") or ""
        st.session_state["ai_model"] = user.get("ai_model") or DEFAULT_MODEL
        st.session_state["ai_loaded"] = True


def sidebar_ai_settings(user: dict) -> None:
    with st.sidebar.expander("🤖 AI settings", expanded=False):
        st.caption(
            "Enter your OWN Anthropic API key to use AI in your notes. "
            "It is saved to your account, so you only enter it once."
        )
        key_val = st.text_input(
            "Anthropic API key",
            value=st.session_state.get("ai_key", ""),
            type="password",
            placeholder="sk-ant-...",
        )
        ws_val = st.text_input(
            "Workspace ID (optional)",
            value=st.session_state.get("ai_workspace", ""),
            placeholder="only if your key requires it",
            help="Needed only if the API says the key is not scoped to a workspace. "
            "Find it in the Anthropic Console under the workspace settings.",
        )
        model_val = st.selectbox(
            "Model",
            options=list(MODELS.keys()),
            format_func=lambda m: MODELS[m],
            index=list(MODELS.keys()).index(st.session_state.get("ai_model", DEFAULT_MODEL)),
        )
        st.session_state["ai_key"] = key_val
        st.session_state["ai_workspace"] = ws_val
        st.session_state["ai_model"] = model_val

        # Persist to the user's account when something changed.
        changed = (
            key_val != (user.get("anthropic_key") or "")
            or ws_val != (user.get("anthropic_workspace") or "")
            or model_val != (user.get("ai_model") or DEFAULT_MODEL)
        )
        if changed:
            db.set_user_ai(user["id"], key_val, model_val, ws_val)
            user["anthropic_key"] = key_val
            user["anthropic_workspace"] = ws_val
            user["ai_model"] = model_val
            st.caption("✅ Saved to your account.")

        st.link_button("Get an API key", "https://console.anthropic.com/settings/keys")


def sidebar_nav(user: dict) -> None:
    st.sidebar.title("🎓 StudyHelp")
    st.sidebar.write(f"👤 **{user['email']}**")
    st.sidebar.caption(f"Role: {user['role']}")

    pages = {"study": "📚 Study"}
    if auth.is_admin(user):
        pages["manage"] = "✏️ Manage content"
        pages["admin"] = "👥 Users"

    st.sidebar.radio(
        "Menu",
        options=list(pages.keys()),
        format_func=lambda k: pages[k],
        key="page",
    )

    st.sidebar.divider()
    sidebar_ai_settings(user)

    if auth.is_admin(user):
        backend = "🟢 Supabase (Postgres)" if config.using_postgres() else "🟡 SQLite (local)"
        st.sidebar.caption(f"Database: {backend}")

    st.sidebar.divider()
    if st.sidebar.button("Sign out", use_container_width=True):
        st.session_state["user"] = None
        st.session_state["ai_loaded"] = False
        st.session_state["ai_key"] = ""
        st.session_state["ai_workspace"] = ""
        st.rerun()


def main() -> None:
    init_state()
    user = st.session_state.get("user")

    # Not authenticated -> login/register screen.
    if not user:
        login_register_screen()
        return

    # Authenticated but not yet approved.
    if user.get("status") != "approved":
        pending_screen(user)
        return

    load_ai_settings_once(user)
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

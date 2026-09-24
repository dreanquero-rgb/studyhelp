"""Authentication screens: login / register and the "pending approval" screen."""

from __future__ import annotations

import streamlit as st

from . import auth, db


def login_register_screen() -> None:
    st.title("🎓 StudyHelp")
    st.caption("Your interactive study platform")

    first_user = db.count_users() == 0
    if first_user:
        st.info(
            "👋 Welcome! No account exists yet: **the first person to register "
            "becomes the administrator (owner)** of the platform."
        )

    tab_login, tab_register = st.tabs(["Sign in", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            user, msg = auth.authenticate(email, password)
            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error(msg)

    with tab_register:
        with st.form("register_form"):
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password (min 8 characters)", type="password", key="reg_pw")
            password2 = st.text_input("Confirm password", type="password", key="reg_pw2")
            submitted = st.form_submit_button("Create account", use_container_width=True)
        if submitted:
            if password != password2:
                st.error("The two passwords do not match.")
            else:
                ok, msg = auth.register(email, password)
                (st.success if ok else st.error)(msg)


def pending_screen(user: dict) -> None:
    st.title("⏳ Account awaiting approval")
    st.write(
        f"Hi **{user['email']}**, your account has been created but must be "
        "approved by the administrator before you can access the content."
    )
    st.info("Try signing in again later, or ask the administrator to approve you.")
    if st.button("Sign out"):
        st.session_state["user"] = None
        st.rerun()

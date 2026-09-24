"""Schermate di autenticazione: login / registrazione e "in attesa"."""

from __future__ import annotations

import streamlit as st

from . import auth, db


def login_register_screen() -> None:
    st.title("🎓 StudyHelp")
    st.caption("La tua piattaforma di studio interattiva")

    first_user = db.count_users() == 0
    if first_user:
        st.info(
            "👋 Benvenuta/o! Nessun account esiste ancora: **il primo che si "
            "registra diventa l'amministratore (owner)** della piattaforma."
        )

    tab_login, tab_register = st.tabs(["Accedi", "Registrati"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Accedi", use_container_width=True)
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
            password = st.text_input("Password (min 8 caratteri)", type="password", key="reg_pw")
            password2 = st.text_input("Conferma password", type="password", key="reg_pw2")
            submitted = st.form_submit_button("Crea account", use_container_width=True)
        if submitted:
            if password != password2:
                st.error("Le due password non coincidono.")
            else:
                ok, msg = auth.register(email, password)
                (st.success if ok else st.error)(msg)


def pending_screen(user: dict) -> None:
    st.title("⏳ Account in attesa di approvazione")
    st.write(
        f"Ciao **{user['email']}**, il tuo account è stato creato ma deve essere "
        "approvato dall'amministratore prima di poter accedere ai contenuti."
    )
    st.info("Riprova ad accedere più tardi, oppure chiedi all'amministratore di approvarti.")
    if st.button("Esci"):
        st.session_state["user"] = None
        st.rerun()

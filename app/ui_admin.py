"""Pannello amministratore: approvazione utenti e gestione ruoli."""

from __future__ import annotations

import streamlit as st

from . import db

_STATUS_LABEL = {"pending": "⏳ In attesa", "approved": "✅ Approvato", "blocked": "🚫 Bloccato"}


def admin_page(current_user: dict) -> None:
    st.title("👥 Gestione utenti")
    st.caption("Approva chi può accedere alla piattaforma ed eseguire codice/AI.")

    users = db.list_users()
    pending = [u for u in users if u["status"] == "pending"]
    if pending:
        st.subheader(f"In attesa di approvazione ({len(pending)})")
        for u in pending:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{u['email']}**")
            if col2.button("✅ Approva", key=f"appr_{u['id']}", use_container_width=True):
                db.set_user_status(u["id"], "approved")
                st.rerun()
            if col3.button("🚫 Rifiuta", key=f"rej_{u['id']}", use_container_width=True):
                db.set_user_status(u["id"], "blocked")
                st.rerun()
        st.divider()

    st.subheader("Tutti gli utenti")
    for u in users:
        is_self = u["id"] == current_user["id"]
        col1, col2, col3, col4 = st.columns([3, 1.4, 1.3, 1.3])
        col1.write(f"**{u['email']}**" + (" _(tu)_" if is_self else ""))
        col2.write(_STATUS_LABEL.get(u["status"], u["status"]))
        col3.write(f"`{u['role']}`")

        # L'owner non può essere modificato/declassato dagli altri.
        if u["role"] == "owner" or is_self:
            col4.caption("—")
            continue

        with col4.popover("Azioni"):
            if u["status"] != "approved" and st.button("Approva", key=f"a_{u['id']}"):
                db.set_user_status(u["id"], "approved")
                st.rerun()
            if u["status"] != "blocked" and st.button("Blocca", key=f"b_{u['id']}"):
                db.set_user_status(u["id"], "blocked")
                st.rerun()
            if u["role"] == "student" and st.button("Rendi admin", key=f"ma_{u['id']}"):
                db.set_user_role(u["id"], "admin")
                st.rerun()
            if u["role"] == "admin" and st.button("Rimuovi admin", key=f"ra_{u['id']}"):
                db.set_user_role(u["id"], "student")
                st.rerun()

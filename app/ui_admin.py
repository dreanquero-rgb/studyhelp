"""Admin panel: user approval and role management."""

from __future__ import annotations

import streamlit as st

from . import db

_STATUS_LABEL = {"pending": "⏳ Pending", "approved": "✅ Approved", "blocked": "🚫 Blocked"}


def admin_page(current_user: dict) -> None:
    st.title("👥 User management")
    st.caption("Approve who can access the platform and run code / AI.")

    users = db.list_users()
    pending = [u for u in users if u["status"] == "pending"]
    if pending:
        st.subheader(f"Awaiting approval ({len(pending)})")
        for u in pending:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{u['email']}**")
            if col2.button("✅ Approve", key=f"appr_{u['id']}", use_container_width=True):
                db.set_user_status(u["id"], "approved")
                st.rerun()
            if col3.button("🚫 Reject", key=f"rej_{u['id']}", use_container_width=True):
                db.set_user_status(u["id"], "blocked")
                st.rerun()
        st.divider()

    st.subheader("All users")
    for u in users:
        is_self = u["id"] == current_user["id"]
        col1, col2, col3, col4 = st.columns([3, 1.4, 1.3, 1.3])
        col1.write(f"**{u['email']}**" + (" _(you)_" if is_self else ""))
        col2.write(_STATUS_LABEL.get(u["status"], u["status"]))
        col3.write(f"`{u['role']}`")

        # The owner cannot be modified/demoted by others.
        if u["role"] == "owner" or is_self:
            col4.caption("—")
            continue

        with col4.popover("Actions"):
            if u["status"] != "approved" and st.button("Approve", key=f"a_{u['id']}"):
                db.set_user_status(u["id"], "approved")
                st.rerun()
            if u["status"] != "blocked" and st.button("Block", key=f"b_{u['id']}"):
                db.set_user_status(u["id"], "blocked")
                st.rerun()
            if u["role"] == "student" and st.button("Make admin", key=f"ma_{u['id']}"):
                db.set_user_role(u["id"], "admin")
                st.rerun()
            if u["role"] == "admin" and st.button("Remove admin", key=f"ra_{u['id']}"):
                db.set_user_role(u["id"], "student")
                st.rerun()

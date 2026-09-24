"""Configurazione runtime: da dove leggere la connessione al database.

Priorità (prima trovata vince):
1. Variabile d'ambiente SUPABASE_DB_URL o DATABASE_URL
2. Streamlit secrets:  [supabase] db_url = "..."   oppure   SUPABASE_DB_URL = "..."
3. Nessuna -> si usa SQLite locale (sviluppo).

La stringa di connessione Supabase è un SEGRETO: non va mai messa nel codice
né committata. In locale sta in .streamlit/secrets.toml (ignorato da git);
online si imposta nei "Secrets" di Streamlit Community Cloud.
"""

from __future__ import annotations

import os


def get_db_url() -> str | None:
    for env in ("SUPABASE_DB_URL", "DATABASE_URL"):
        value = os.environ.get(env)
        if value:
            return value

    try:
        import streamlit as st

        # [supabase] db_url = "..."
        if "supabase" in st.secrets and st.secrets["supabase"].get("db_url"):
            return st.secrets["supabase"]["db_url"]
        # SUPABASE_DB_URL = "..." (chiave piatta)
        if st.secrets.get("SUPABASE_DB_URL"):
            return st.secrets["SUPABASE_DB_URL"]
    except Exception:
        # st.secrets non disponibile fuori dal runtime Streamlit: nessun problema.
        pass

    return None


def using_postgres() -> bool:
    return get_db_url() is not None

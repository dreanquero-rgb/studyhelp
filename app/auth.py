"""Autenticazione: registrazione, login, ruoli e approvazione.

Regole:
- Il PRIMO utente che si registra diventa automaticamente 'owner' e 'approved'
  (sei tu). Tutti gli altri partono 'pending' finché l'owner non li approva.
- Le password sono salvate con hash PBKDF2-HMAC-SHA256 + salt casuale
  (nessuna dipendenza esterna).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re

from . import db

_ITERATIONS = 200_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def register(email: str, password: str) -> tuple[bool, str]:
    """Registra un nuovo utente. Ritorna (successo, messaggio)."""
    email = email.lower().strip()
    if not _EMAIL_RE.match(email):
        return False, "Inserisci un indirizzo email valido."
    if len(password) < 8:
        return False, "La password deve avere almeno 8 caratteri."
    if db.get_user_by_email(email):
        return False, "Esiste già un account con questa email."

    first_user = db.count_users() == 0
    role = "owner" if first_user else "student"
    status = "approved" if first_user else "pending"
    db.create_user(email, hash_password(password), role, status)

    if first_user:
        return True, "Account creato come OWNER (amministratore). Ora puoi accedere."
    return True, "Account creato! In attesa di approvazione da parte dell'amministratore."


def authenticate(email: str, password: str) -> tuple[dict | None, str]:
    """Verifica le credenziali. Ritorna (utente, messaggio)."""
    user = db.get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return None, "Email o password non corretti."
    if user["status"] == "blocked":
        return None, "Questo account è stato bloccato."
    # 'pending' può autenticarsi ma vedrà la schermata "in attesa".
    return user, "Accesso effettuato."


def is_admin(user: dict | None) -> bool:
    return bool(user) and user.get("role") in ("owner", "admin")


def can_run_code(user: dict | None) -> bool:
    """Solo utenti approvati possono eseguire codice/AI."""
    return bool(user) and user.get("status") == "approved"

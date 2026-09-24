"""Integrazione AI (Claude) — ogni utente usa la PROPRIA chiave API.

La chiave viene inserita dall'utente nell'app e tenuta solo in sessione
(non salvata nel database), così i costi restano a carico di chi la usa.
"""

from __future__ import annotations

import anthropic

# Modelli selezionabili dall'utente (id API -> etichetta).
MODELS = {
    "claude-opus-5": "Claude Opus 5 — il più capace",
    "claude-sonnet-5": "Claude Sonnet 5 — equilibrato, più economico",
    "claude-haiku-4-5": "Claude Haiku 4.5 — veloce ed economico",
}
DEFAULT_MODEL = "claude-opus-5"

SYSTEM_PROMPT = (
    "You are a study assistant embedded directly in a university student's notes. "
    "The student attends Bayes Business School and studies finance and related "
    "subjects. Explain clearly and accurately, use worked examples where useful, "
    "and keep answers focused and well-structured in Markdown. If the student "
    "provides context from their notes, ground your answer in it."
)


def ask(api_key: str, prompt: str, model: str = DEFAULT_MODEL, context: str = "") -> tuple[str | None, str | None]:
    """Chiede a Claude. Ritorna (risposta, errore); uno dei due è None."""
    if not api_key:
        return None, "Inserisci la tua chiave API di Anthropic nelle impostazioni AI."

    user_content = prompt
    if context.strip():
        user_content = f"Context from my notes:\n{context}\n\n---\n\nRequest:\n{prompt}"

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        return text.strip() or "(nessuna risposta)", None
    except anthropic.AuthenticationError:
        return None, "Chiave API non valida. Controllala nelle impostazioni AI."
    except anthropic.RateLimitError:
        return None, "Limite di richieste raggiunto. Riprova tra poco."
    except anthropic.APIStatusError as exc:
        return None, f"Errore API ({exc.status_code}): {getattr(exc, 'message', str(exc))}"
    except Exception as exc:  # noqa: BLE001 - mostriamo un messaggio leggibile
        return None, f"Errore imprevisto: {exc}"

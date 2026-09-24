"""AI integration (Claude) — each user brings their OWN API key.

The key is entered in the app and kept only in the session (never stored in the
database), so costs stay with whoever uses the key.
"""

from __future__ import annotations

import anthropic

# Models the user can pick (API id -> label).
MODELS = {
    "claude-opus-5": "Claude Opus 5 — most capable",
    "claude-sonnet-5": "Claude Sonnet 5 — balanced, cheaper",
    "claude-haiku-4-5": "Claude Haiku 4.5 — fast and economical",
}
DEFAULT_MODEL = "claude-opus-5"

SYSTEM_PROMPT = (
    "You are a study assistant embedded directly in a university student's notes. "
    "The student attends Bayes Business School and studies finance and related "
    "subjects. Explain clearly and accurately, use worked examples where useful, "
    "and keep answers focused and well-structured in Markdown. If the student "
    "provides context from their notes, ground your answer in it."
)


def ask(
    api_key: str,
    prompt: str,
    model: str = DEFAULT_MODEL,
    context: str = "",
    workspace_id: str = "",
) -> tuple[str | None, str | None]:
    """Ask Claude. Returns (answer, error); exactly one is None."""
    if not api_key:
        return None, "Add your Anthropic API key in the AI settings first."

    user_content = prompt
    if context.strip():
        user_content = f"Context from my notes:\n{context}\n\n---\n\nRequest:\n{prompt}"

    # Some org-level keys require the workspace to be named explicitly.
    extra_headers = {"anthropic-workspace-id": workspace_id.strip()} if workspace_id.strip() else None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
            extra_headers=extra_headers,
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        return text.strip() or "(no answer)", None
    except anthropic.AuthenticationError:
        return None, "Invalid API key. Check it in the AI settings (sidebar)."
    except anthropic.RateLimitError:
        return None, "Rate limit reached. Please try again shortly."
    except anthropic.APIConnectionError as exc:
        cause = getattr(exc, "__cause__", None)
        detail = f" ({cause})" if cause else ""
        return None, (
            "Could not reach the Anthropic API"
            f"{detail}. Check that your API key is correct and that the app has "
            "internet access, then try again."
        )
    except anthropic.APIStatusError as exc:
        return None, f"API error ({exc.status_code}): {getattr(exc, 'message', str(exc))}"
    except Exception as exc:  # noqa: BLE001 - show a readable message
        return None, f"Unexpected error: {type(exc).__name__}: {exc}"

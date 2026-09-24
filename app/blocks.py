"""Renderer dei blocchi di una lezione.

Una lezione è una lista di "blocchi". Ogni blocco ha un campo "type" che decide
come viene disegnato. Aggiungere un nuovo tipo di contenuto = aggiungere una
funzione qui e registrarla in RENDERERS.

Tipi supportati:
    markdown     -> testo/teoria in Markdown
    objectives   -> elenco degli obiettivi di apprendimento
    key_terms    -> glossario termine/definizione
    flashcards   -> flashcard interattive (una alla volta, si girano)
    quiz         -> quiz a risposta multipla con punteggio e spiegazioni
    calculator   -> calcolatore finanziario interattivo
    summary      -> riepilogo finale
"""

from __future__ import annotations

import streamlit as st

from .calculators import render_calculator


def _markdown(block: dict, key: str) -> None:
    if block.get("title"):
        st.subheader(block["title"])
    st.markdown(block.get("content", ""))


def _objectives(block: dict, key: str) -> None:
    st.subheader(block.get("title", "🎯 Learning objectives"))
    for item in block.get("items", []):
        st.markdown(f"- {item}")


def _key_terms(block: dict, key: str) -> None:
    st.subheader(block.get("title", "📚 Key concepts"))
    for item in block.get("items", []):
        with st.expander(item.get("term", "")):
            st.markdown(item.get("definition", ""))


def _flashcards(block: dict, key: str) -> None:
    st.subheader(block.get("title", "🃏 Flashcards"))
    cards = block.get("cards", [])
    if not cards:
        return

    idx_key = f"{key}_idx"
    flip_key = f"{key}_flip"
    st.session_state.setdefault(idx_key, 0)
    st.session_state.setdefault(flip_key, False)

    idx = st.session_state[idx_key] % len(cards)
    card = cards[idx]
    showing_back = st.session_state[flip_key]

    face = card.get("back") if showing_back else card.get("front", "")
    label = "Answer" if showing_back else "Question"
    st.markdown(
        f"""
        <div style="border:1px solid #e2e8f0;border-radius:12px;padding:28px;
                    text-align:center;background:#f8fafc;min-height:120px;
                    display:flex;flex-direction:column;justify-content:center;">
            <div style="font-size:0.8rem;text-transform:uppercase;letter-spacing:.05em;
                        color:#64748b;margin-bottom:8px;">{label}</div>
            <div style="font-size:1.15rem;color:#0f172a;">{face}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"Card {idx + 1} of {len(cards)}")
    col1, col2, col3 = st.columns(3)
    if col1.button("◀ Previous", key=f"{key}_prev", use_container_width=True):
        st.session_state[idx_key] = (idx - 1) % len(cards)
        st.session_state[flip_key] = False
        st.rerun()
    if col2.button("🔄 Flip", key=f"{key}_flipbtn", use_container_width=True):
        st.session_state[flip_key] = not showing_back
        st.rerun()
    if col3.button("Next ▶", key=f"{key}_next", use_container_width=True):
        st.session_state[idx_key] = (idx + 1) % len(cards)
        st.session_state[flip_key] = False
        st.rerun()


def _quiz(block: dict, key: str) -> None:
    st.subheader(block.get("title", "✅ Quiz"))
    questions = block.get("questions", [])
    if not questions:
        return

    submitted_key = f"{key}_submitted"
    st.session_state.setdefault(submitted_key, False)

    with st.form(key=f"{key}_form"):
        choices: list[int | None] = []
        for i, q in enumerate(questions):
            options = q.get("options", [])
            answer = st.radio(
                f"**{i + 1}. {q.get('q', '')}**",
                options=list(range(len(options))),
                format_func=lambda x, opts=options: opts[x],
                index=None,
                key=f"{key}_q{i}",
            )
            choices.append(answer)
        submitted = st.form_submit_button("Check answers", use_container_width=True)

    if submitted:
        st.session_state[submitted_key] = True

    if st.session_state[submitted_key]:
        score = 0
        for i, q in enumerate(questions):
            correct = q.get("answer")
            chosen = st.session_state.get(f"{key}_q{i}")
            options = q.get("options", [])
            if chosen == correct:
                score += 1
                st.success(f"**{i + 1}.** Correct ✅ — {options[correct]}")
            else:
                chosen_txt = options[chosen] if chosen is not None else "_no answer_"
                correct_txt = options[correct] if correct is not None else ""
                st.error(f"**{i + 1}.** Your answer: {chosen_txt} — Correct: **{correct_txt}**")
            if q.get("explanation"):
                st.caption(f"💡 {q['explanation']}")

        total = len(questions)
        pct = score / total * 100 if total else 0
        st.markdown(f"### Score: {score}/{total} ({pct:.0f}%)")
        # Salva il miglior punteggio del quiz per la barra dei progressi.
        progress = st.session_state.setdefault("progress", {"visited": set(), "quiz_scores": {}})
        best = progress.setdefault("quiz_scores", {})
        best[key] = max(best.get(key, 0), pct)


def _summary(block: dict, key: str) -> None:
    st.subheader(block.get("title", "📝 Summary"))
    st.info(block.get("content", ""))


RENDERERS = {
    "markdown": _markdown,
    "objectives": _objectives,
    "key_terms": _key_terms,
    "flashcards": _flashcards,
    "quiz": _quiz,
    "summary": _summary,
}


def render_block(block: dict, key: str) -> None:
    btype = block.get("type")
    if btype == "calculator":
        render_calculator(block.get("kind", ""), key)
        return
    renderer = RENDERERS.get(btype)
    if renderer is None:
        st.warning(f"Unknown block type: '{btype}'")
        return
    renderer(block, key)

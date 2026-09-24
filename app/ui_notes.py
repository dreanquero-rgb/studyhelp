"""Personal notes editor (per user, per lesson).

Each note is a sequence of blocks:
    - text : text / Markdown
    - code : runnable Python code (charts and statistics included)
    - ai   : a request to the AI (using the user's own API key)
"""

from __future__ import annotations

import uuid

import streamlit as st

from . import ai, db
from .exec_sandbox import run_code

_BLOCK_LABELS = {"text": "📝 Text", "code": "🐍 Python code", "ai": "🤖 AI"}


def _wc_key(user_id: int, lesson_id: int) -> str:
    return f"nb_{user_id}_{lesson_id}"


def _load(user_id: int, lesson_id: int) -> list[dict]:
    key = _wc_key(user_id, lesson_id)
    if key not in st.session_state:
        blocks = db.get_note(user_id, lesson_id)
        for b in blocks:
            b.setdefault("id", uuid.uuid4().hex[:8])
        st.session_state[key] = blocks
    return st.session_state[key]


def _sync_from_widgets(blocks: list[dict]) -> None:
    """Copy the widget text back into the working list."""
    for b in blocks:
        wkey = f"ntext_{b['id']}"
        if wkey in st.session_state:
            b["content"] = st.session_state[wkey]


def _persist(user_id: int, lesson_id: int, blocks: list[dict]) -> None:
    db.save_note(user_id, lesson_id, blocks)


def render_notes(user: dict, lesson_id: int) -> None:
    user_id = user["id"]
    blocks = _load(user_id, lesson_id)

    st.markdown("### 🗒️ My notes")
    st.caption(
        "Only you can see these notes. To use AI: click **➕ AI**, type your question "
        "in the block that appears and press **✨ Generate answer**. "
        "(Set your key in the sidebar → 🤖 AI settings.)"
    )

    # --- Toolbar: add blocks + save ---
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.4])
    if c1.button("➕ Text", use_container_width=True):
        _sync_from_widgets(blocks)
        blocks.append({"id": uuid.uuid4().hex[:8], "type": "text", "content": ""})
        _persist(user_id, lesson_id, blocks)
        st.rerun()
    if c2.button("➕ Code", use_container_width=True):
        _sync_from_widgets(blocks)
        blocks.append({"id": uuid.uuid4().hex[:8], "type": "code", "content": "# write your Python code here\n"})
        _persist(user_id, lesson_id, blocks)
        st.rerun()
    if c3.button("➕ AI", use_container_width=True):
        _sync_from_widgets(blocks)
        blocks.append({"id": uuid.uuid4().hex[:8], "type": "ai", "content": ""})
        _persist(user_id, lesson_id, blocks)
        st.rerun()
    if c4.button("💾 Save notes", use_container_width=True, type="primary"):
        _sync_from_widgets(blocks)
        _persist(user_id, lesson_id, blocks)
        st.toast("Notes saved ✅")

    if not blocks:
        st.info("No blocks yet. Use the buttons above to start.")
        return

    for i, block in enumerate(blocks):
        _render_block(user, lesson_id, blocks, i)


def _render_block(user: dict, lesson_id: int, blocks: list[dict], i: int) -> None:
    block = blocks[i]
    bid = block["id"]
    with st.container(border=True):
        head1, head2, head3, head4 = st.columns([6, 1, 1, 1])
        head1.markdown(f"**{_BLOCK_LABELS.get(block['type'], block['type'])}**")
        if head2.button("▲", key=f"up_{bid}", help="Move up") and i > 0:
            _sync_from_widgets(blocks)
            blocks[i - 1], blocks[i] = blocks[i], blocks[i - 1]
            _persist(user["id"], lesson_id, blocks)
            st.rerun()
        if head3.button("▼", key=f"dn_{bid}", help="Move down") and i < len(blocks) - 1:
            _sync_from_widgets(blocks)
            blocks[i + 1], blocks[i] = blocks[i], blocks[i + 1]
            _persist(user["id"], lesson_id, blocks)
            st.rerun()
        if head4.button("🗑", key=f"del_{bid}", help="Delete block"):
            _sync_from_widgets(blocks)
            blocks.pop(i)
            _persist(user["id"], lesson_id, blocks)
            st.rerun()

        if block["type"] == "text":
            _render_text(block)
        elif block["type"] == "code":
            _render_code(user, block)
        elif block["type"] == "ai":
            _render_ai(user, lesson_id, blocks, block)


def _render_text(block: dict) -> None:
    st.text_area(
        "Text (Markdown)",
        value=block.get("content", ""),
        key=f"ntext_{block['id']}",
        height=140,
        label_visibility="collapsed",
    )
    if block.get("content", "").strip():
        with st.expander("Preview"):
            st.markdown(block["content"])


def _render_code(user: dict, block: dict) -> None:
    st.text_area(
        "Python code",
        value=block.get("content", ""),
        key=f"ntext_{block['id']}",
        height=180,
        label_visibility="collapsed",
    )
    if st.button("▶ Run", key=f"run_{block['id']}"):
        block["content"] = st.session_state.get(f"ntext_{block['id']}", block.get("content", ""))
        with st.spinner("Running..."):
            st.session_state[f"out_{block['id']}"] = run_code(block["content"])

    result = st.session_state.get(f"out_{block['id']}")
    if result:
        if result["stdout"]:
            st.code(result["stdout"], language="text")
        for img in result["images"]:
            st.image(img)
        if result["stderr"]:
            st.error(result["stderr"])


def _render_ai(user: dict, lesson_id: int, blocks: list[dict], block: dict) -> None:
    st.text_area(
        "Ask the AI",
        value=block.get("content", ""),
        key=f"ntext_{block['id']}",
        height=100,
        placeholder="e.g. explain the difference between primary and secondary markets with an example",
        label_visibility="collapsed",
    )
    api_key = st.session_state.get("ai_key", "")
    model = st.session_state.get("ai_model", ai.DEFAULT_MODEL)

    if st.button("✨ Generate answer", key=f"gen_{block['id']}", type="primary"):
        prompt = st.session_state.get(f"ntext_{block['id']}", "")
        block["content"] = prompt
        if not api_key:
            st.session_state[f"aiout_{block['id']}"] = {
                "answer": None,
                "err": "⚠️ Missing API key. Open the sidebar → **🤖 AI settings**, paste your "
                "key (sk-ant-...) and press Enter, then click «Generate answer» again.",
            }
        elif not prompt.strip():
            st.session_state[f"aiout_{block['id']}"] = {
                "answer": None,
                "err": "Type a question above first, then click «Generate answer».",
            }
        else:
            # Context: the text blocks of the note, for more relevant answers.
            context = "\n\n".join(b.get("content", "") for b in blocks if b["type"] == "text")
            with st.spinner("The AI is thinking..."):
                answer, err = ai.ask(api_key, prompt, model=model, context=context)
            st.session_state[f"aiout_{block['id']}"] = {"answer": answer, "err": err}

    out = st.session_state.get(f"aiout_{block['id']}")
    if out:
        if out["err"]:
            st.error(out["err"])
        else:
            st.markdown(out["answer"])
            if st.button("📌 Save answer as a note", key=f"pin_{block['id']}"):
                _sync_from_widgets(blocks)
                blocks.append(
                    {"id": uuid.uuid4().hex[:8], "type": "text", "content": out["answer"]}
                )
                db.save_note(user["id"], lesson_id, blocks)
                st.rerun()

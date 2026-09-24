"""Personal notes editor (per lesson), with automatic saving.

Each note is a sequence of blocks:
    - text : text / Markdown
    - code : runnable Python code (charts and statistics included)

Notes are auto-saved to the database on every change, so work is never lost.
"""

from __future__ import annotations

import json
import uuid

import streamlit as st

from . import db
from .exec_sandbox import run_code

_BLOCK_LABELS = {"text": "📝 Text", "code": "🐍 Python code"}


def _wc_key(lesson_key: str) -> str:
    return f"nb_{lesson_key}"


def _snap_key(lesson_key: str) -> str:
    return f"nbsnap_{lesson_key}"


def _load(lesson_key: str) -> list[dict]:
    key = _wc_key(lesson_key)
    if key not in st.session_state:
        blocks = db.get_note(lesson_key)
        for b in blocks:
            b.setdefault("id", uuid.uuid4().hex[:8])
        st.session_state[key] = blocks
        st.session_state[_snap_key(lesson_key)] = json.dumps(blocks, ensure_ascii=False)
    return st.session_state[key]


def _sync_from_widgets(blocks: list[dict]) -> None:
    for b in blocks:
        wkey = f"ntext_{b['id']}"
        if wkey in st.session_state:
            b["content"] = st.session_state[wkey]


def _autosave(lesson_key: str, blocks: list[dict]) -> None:
    """Save to the database only if something actually changed."""
    snapshot = json.dumps(blocks, ensure_ascii=False)
    if snapshot != st.session_state.get(_snap_key(lesson_key)):
        db.save_note(lesson_key, blocks)
        st.session_state[_snap_key(lesson_key)] = snapshot


def render_notes(lesson_key: str) -> None:
    blocks = _load(lesson_key)

    st.markdown("### 🗒️ My notes")
    st.caption("Your notes are saved automatically. Add text or runnable Python code.")

    c1, c2 = st.columns(2)
    if c1.button("➕ Text", use_container_width=True):
        _sync_from_widgets(blocks)
        blocks.append({"id": uuid.uuid4().hex[:8], "type": "text", "content": ""})
        _autosave(lesson_key, blocks)
        st.rerun()
    if c2.button("➕ Code", use_container_width=True):
        _sync_from_widgets(blocks)
        blocks.append({"id": uuid.uuid4().hex[:8], "type": "code", "content": "# write your Python code here\n"})
        _autosave(lesson_key, blocks)
        st.rerun()

    if not blocks:
        st.info("No notes yet. Use the buttons above to start.")
        return

    for i in range(len(blocks)):
        _render_block(lesson_key, blocks, i)

    # Persist any text edits made this run.
    _sync_from_widgets(blocks)
    _autosave(lesson_key, blocks)


def _render_block(lesson_key: str, blocks: list[dict], i: int) -> None:
    block = blocks[i]
    bid = block["id"]
    with st.container(border=True):
        head1, head2, head3, head4 = st.columns([6, 1, 1, 1])
        head1.markdown(f"**{_BLOCK_LABELS.get(block['type'], block['type'])}**")
        if head2.button("▲", key=f"up_{bid}", help="Move up") and i > 0:
            _sync_from_widgets(blocks)
            blocks[i - 1], blocks[i] = blocks[i], blocks[i - 1]
            _autosave(lesson_key, blocks)
            st.rerun()
        if head3.button("▼", key=f"dn_{bid}", help="Move down") and i < len(blocks) - 1:
            _sync_from_widgets(blocks)
            blocks[i + 1], blocks[i] = blocks[i], blocks[i + 1]
            _autosave(lesson_key, blocks)
            st.rerun()
        if head4.button("🗑", key=f"del_{bid}", help="Delete block"):
            _sync_from_widgets(blocks)
            blocks.pop(i)
            _autosave(lesson_key, blocks)
            st.rerun()

        if block["type"] == "text":
            _render_text(block)
        elif block["type"] == "code":
            _render_code(block)


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


def _render_code(block: dict) -> None:
    st.text_area(
        "Python code",
        value=block.get("content", ""),
        key=f"ntext_{block['id']}",
        height=180,
        label_visibility="collapsed",
    )
    if st.button("▶ Run", key=f"run_{block['id']}", type="primary"):
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

# 🎓 StudyHelp

A personal, interactive study site built with **Streamlit**. Free, no login, no AI keys.

- **Single user, no login** — just open it and study.
- **Course content lives in files** under `content/` (managed via Claude Code).
- **Personal notes** (text + runnable Python code) are saved to a database so
  your work is never lost.
- **Interactive lessons**: theory, key concepts, flashcards, quizzes, finance
  calculators and runnable code exercises.

---

## ▶️ Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Locally, with no database configured, notes are stored in a local SQLite file
(`data/studyhelp.db`).

## ☁️ Online (Streamlit Community Cloud + Supabase)

The app is deployed on Streamlit Community Cloud. Notes are saved to **Supabase**
(Postgres) so they survive restarts. The connection string is set in the app
**Secrets** (never committed):

```toml
[supabase]
db_url = "postgresql://postgres.<ref>:<PASSWORD>@aws-0-<region>.pooler.supabase.com:6543/postgres"
```

The admin/sidebar shows whether notes are being saved to Supabase or local SQLite.

---

## ➕ Adding content (via files)

Content is plain JSON in `content/`, edited and committed via Claude Code.

**`content/courses.json`** — the list of courses, each with sections and lessons:

```json
[
  {
    "id": "securities-and-investment",
    "title": "Securities and Investment",
    "icon": "📈",
    "description": "…",
    "sections": [
      { "id": "module-1", "title": "Module 1", "lessons": ["lesson-01"] }
    ]
  }
]
```

**`content/<course_id>/<lesson_id>.json`** — a lesson is a list of blocks:

| `type`          | Purpose |
|-----------------|---------|
| `objectives`    | Learning objectives (list) |
| `markdown`      | Theory in Markdown (tables and formulas) |
| `key_terms`     | Glossary term → definition |
| `flashcards`    | Flip-through flashcards |
| `quiz`          | Multiple-choice quiz with scoring |
| `calculator`    | Finance calculator (`present_value`, `compound_interest`, `holding_period_return`, `bond_price`) |
| `code_exercise` | A runnable Python exercise (fields: `title`, `prompt`, `starter`) |
| `summary`       | Final recap |

> Notes are keyed by `course_id/lesson_id`. Keep lesson ids stable so notes stay
> attached to the right lesson.

---

## 🗂️ Project structure

```
studyhelp/
├── streamlit_app.py        # entry point (no login)
├── app/
│   ├── content.py          # loads courses/lessons from files
│   ├── db.py               # notes persistence (Supabase/Postgres or local SQLite)
│   ├── config.py           # reads the DB connection from secrets/env
│   ├── exec_sandbox.py     # isolated Python execution (charts + stats)
│   ├── blocks.py           # lesson block renderers
│   ├── calculators.py      # finance calculators
│   ├── ui_study.py         # study page (material + notes)
│   └── ui_notes.py         # notes editor (text + runnable code, auto-saved)
├── content/                # course content (JSON, managed via Claude Code)
├── requirements.txt
└── .streamlit/config.toml
```

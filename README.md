# 🎓 StudyHelp

Piattaforma di studio interattiva costruita con **Streamlit**.

Ogni **corso** è una sezione; ogni corso contiene **lezioni**; ogni lezione è
una pagina di studio interattiva con teoria, concetti chiave, **flashcard**,
**quiz** ed **esercizi/calcolatori** interattivi.

Il primo corso incluso è **Securities and Investment**.

---

## ▶️ Avvio in locale

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Poi apri il link che compare nel terminale (di solito `http://localhost:8501`).

---

## ☁️ Metterla online (gratis) — Streamlit Community Cloud

1. Assicurati che questo repo sia su GitHub (lo è: `dreanquero-rgb/studyhelp`).
2. Vai su **https://share.streamlit.io** e accedi con il tuo account GitHub.
3. Clicca **"Create app" → "Deploy a public app from GitHub"**.
4. Seleziona:
   - **Repository:** `dreanquero-rgb/studyhelp`
   - **Branch:** il branch su cui vive il codice
   - **Main file path:** `streamlit_app.py`
5. **Deploy**. In un paio di minuti avrai un URL pubblico da condividere.

Ogni volta che aggiorniamo il repo, l'app online si aggiorna da sola.

---

## ➕ Aggiungere contenuti (senza toccare il codice)

Tutti i contenuti sono file JSON in `content/`.

### Aggiungere un corso

Modifica `content/courses.json`:

```json
{
  "id": "corporate-finance",
  "title": "Corporate Finance",
  "icon": "💰",
  "description": "Descrizione del corso.",
  "lessons": ["lesson-01"]
}
```

### Aggiungere una lezione

Crea `content/<id-corso>/<id-lezione>.json`. Una lezione è una lista di
**blocchi**; questi i tipi disponibili:

| `type`        | A cosa serve                                   |
|---------------|------------------------------------------------|
| `objectives`  | Obiettivi di apprendimento (elenco)            |
| `markdown`    | Teoria in Markdown (tabelle e formule incluse) |
| `key_terms`   | Glossario termine → definizione                |
| `flashcards`  | Flashcard interattive (si girano)              |
| `quiz`        | Quiz a risposta multipla con punteggio         |
| `calculator`  | Calcolatore finanziario interattivo            |
| `summary`     | Riepilogo finale                               |

Esempio minimo:

```json
{
  "id": "lesson-02",
  "title": "Titolo della lezione",
  "summary": "Sottotitolo breve.",
  "blocks": [
    {"type": "markdown", "title": "Sezione", "content": "Testo in **Markdown**."},
    {"type": "flashcards", "cards": [{"front": "Domanda?", "back": "Risposta."}]},
    {"type": "quiz", "questions": [
      {"q": "Domanda?", "options": ["A", "B"], "answer": 1, "explanation": "Perché B."}
    ]}
  ]
}
```

Ricordati di aggiungere l'`id` della nuova lezione nell'array `lessons` del corso.

### Calcolatori disponibili (`type: "calculator"`)

- `present_value` — valore attuale
- `compound_interest` — interesse composto
- `holding_period_return` — rendimento di periodo
- `bond_price` — prezzo di un bond

Nuovi calcolatori si aggiungono in `app/calculators.py`.

---

## 🗂️ Struttura del progetto

```
studyhelp/
├── streamlit_app.py          # app principale (entry point)
├── app/
│   ├── loader.py             # caricamento corsi/lezioni
│   ├── blocks.py             # rendering dei blocchi
│   └── calculators.py        # calcolatori finanziari
├── content/
│   ├── courses.json          # elenco dei corsi
│   └── securities-and-investment/
│       └── lesson-01.json
├── requirements.txt
└── .streamlit/config.toml    # tema
```

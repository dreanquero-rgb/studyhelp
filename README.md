# 🎓 StudyHelp

Piattaforma di studio interattiva **multi-utente** costruita con **Streamlit**.

Ogni utente accede con un account personale, studia i corsi (teoria + concetti
chiave + flashcard + quiz + calcolatori) e tiene i **propri appunti** per ogni
lezione, con blocchi di **testo**, **codice Python eseguibile** (grafici e
statistica) e **AI** (usando la propria chiave API).

---

## 👤 Account, ruoli e accesso

- Il **primo utente** che si registra diventa automaticamente **owner**
  (amministratore) ed è già approvato.
- Ogni account successivo parte **"in attesa"**: può accedere ai contenuti solo
  dopo che l'owner lo **approva** (menu **Utenti**). Sei tu a decidere chi entra.
- Ruoli: `owner` / `admin` (gestiscono contenuti e utenti) e `student`.

> Le password sono salvate con hash PBKDF2 + salt. Il login persiste nella
> sessione del browser (un refresh completo richiede di riaccedere — è un limite
> noto dell'MVP, migliorabile con i cookie in seguito).

---

## ✨ Cosa si può fare

| Funzione | Chi |
|---|---|
| Creare / rinominare / eliminare **corsi, sezioni, lezioni** | owner/admin |
| Modificare il **materiale** di una lezione (blocchi JSON) | owner/admin |
| Scrivere **appunti personali** per lezione | tutti gli approvati |
| Blocchi appunti: **testo**, **codice Python** (con grafici/statistica), **AI** | tutti gli approvati |
| Approvare / bloccare utenti, assegnare ruoli | owner/admin |

### 🐍 Esecuzione del codice
Il codice Python degli appunti gira in un **sottoprocesso isolato**: ambiente
ripulito (nessun accesso ai segreti dell'app), timeout, limiti di CPU/memoria e
cattura di stampe e grafici `matplotlib`. Sono disponibili `numpy`, `pandas`,
`scipy`, `matplotlib`. L'accesso è riservato agli account approvati dall'owner.

### 🤖 AI nelle note
Ogni utente inserisce la **propria** chiave API di Anthropic (menu laterale
*Impostazioni AI*); resta solo in sessione e non viene salvata. I costi sono a
carico di chi usa la chiave.

---

## ▶️ Avvio in locale

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Apri `http://localhost:8501` e registra il primo account (diventerai owner).

---

## ☁️ Metterla online

### Ora (subito): Streamlit Community Cloud
1. Su **https://share.streamlit.io** accedi con GitHub.
2. **Create app** → repository `dreanquero-rgb/studyhelp`, main file `streamlit_app.py`.
3. **Deploy** → ottieni l'URL pubblico.

> ⚠️ Su Streamlit Community Cloud il disco è **effimero**: il database SQLite
> locale può azzerarsi ai riavvii. Va benissimo per provare tutto; per l'uso
> reale multi-utente con dati permanenti serve **Supabase** (passo successivo).

### Passo successivo: Supabase (Postgres, gratis)
Il livello dati (`app/db.py`) è già strutturato per Postgres. Quando avrai un
progetto Supabase, colleghiamo il database così gli account e gli appunti
restano salvati in modo permanente e condiviso tra i dispositivi.

---

## 🗂️ Struttura del progetto

```
studyhelp/
├── streamlit_app.py         # entry point: login + routing per ruolo
├── app/
│   ├── db.py                # livello dati (SQLite ora, pronto per Postgres/Supabase)
│   ├── auth.py              # registrazione, login, ruoli, approvazione
│   ├── exec_sandbox.py      # esecuzione isolata del codice Python
│   ├── ai.py                # integrazione Claude (chiave per-utente)
│   ├── blocks.py            # rendering materiale lezione
│   ├── calculators.py       # calcolatori finanziari
│   ├── ui_auth.py           # schermate login / attesa
│   ├── ui_study.py          # studio: materiale + appunti
│   ├── ui_notes.py          # editor appunti (testo/codice/AI)
│   ├── ui_manage.py         # gestione corsi/sezioni/lezioni
│   └── ui_admin.py          # gestione utenti
├── content/                 # materiale iniziale (importato nel DB al primo avvio)
├── requirements.txt
└── .streamlit/config.toml
```

Il primo avvio importa i corsi da `content/` nel database; da lì tutto è
modificabile dall'app.

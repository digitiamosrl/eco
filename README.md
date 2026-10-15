# eco

POC interna Digitiamo: un panel di personas sintetiche, costruite su dati reali, valuta contenuti prima della pubblicazione e segnala reazioni, obiezioni e passaggi fraintesi.

**Consegna:** mercoledì 9 dicembre 2026 · 8 mercoledì da 4 ore.

## Scope della POC

| Caso d'uso | Input | Output |
| --- | --- | --- |
| Pre-test di post | Post LinkedIn: testo + immagine, 2–5 varianti | Ranking, distribuzione delle risposte, obiezioni, citazioni |
| Test di prototipo | 2–3 flussi catturati con Playwright | Criticità e punti di abbandono per schermata |

**Segmento unico:** decision maker di PMI italiane.

**Prova di valore:** il panel classifica post Digitiamo già pubblicati e la classifica si confronta con l'engagement reale. Sul prototipo, le criticità rilevate si confrontano con feedback reali già raccolti.

**Fuori scope:** navigazione libera degli agenti, video, focus group simulati, chat libera, multi-cliente.

## Team

| Persona | Area | Cartelle |
| --- | --- | --- |
| Salvo | AI e backend | `backend/`, `data/`, `prompts/` |
| Fabio | Design e frontend | `frontend/`, `design/` |

Il contratto tra le due parti è in `shared/schemas/`: si modifica solo insieme.

## Stack

- **Backend:** Python 3.12, FastAPI, SQLite
- **AI:** Claude API (modello leggero per le personas, modello più capace per il report), output in JSON strutturato, prompt caching
- **Cattura prototipo:** Playwright, 2–3 sessioni da script
- **Frontend:** React + Vite + TypeScript

## Struttura

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # endpoint FastAPI
│   │   ├── personas/     # campionamento e generazione delle personas
│   │   ├── engine/       # esecuzione dei test e aggregazione
│   │   ├── capture/      # sessioni Playwright sul prototipo
│   │   └── report/       # score e sintesi
│   └── tests/
├── prompts/              # prompt versionati, uno per file
├── data/
│   ├── raw/              # dati sorgente, NON versionati
│   ├── processed/        # dati anonimizzati
│   └── context/          # scheda di contesto di mercato
├── shared/schemas/       # JSON Schema: Persona, Stimulus, Response, Report
├── frontend/
├── design/               # wireframe e UI kit
└── docs/
```

## Avvio

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env        # inserire ANTHROPIC_API_KEY
uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

## Dati

- `data/raw/` è in `.gitignore`: CRM, note di discovery ed export LinkedIn non entrano nel repository.
- Tutto ciò che va in `data/processed/` è anonimizzato: niente nomi, email, aziende identificabili.
- Fonti: ISTAT (imprese per settore, dimensione, regione), CRM interno, analytics della pagina LinkedIn Digitiamo.

## Documentazione

Il documento di progetto completo (benchmark, casi d'uso futuri, stack, rischi) è nel doc *Concept Testing*.

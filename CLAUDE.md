# CLAUDE.md

Istruzioni per Claude Code su questo repository. Leggi anche `README.md`.

## Il progetto

POC interna Digitiamo: personas sintetiche costruite su dati reali valutano post LinkedIn (testo + immagine) e flussi di un prototipo. Scadenza fissa: 9 dicembre 2026, con circa 4 ore a settimana per persona. **Ogni scelta privilegia la cosa più semplice che funziona.** Se una richiesta allarga lo scope (vedi README), fallo notare prima di implementare.

## Principi non negoziabili

Sono il fattore differenziante del progetto: non sostituirli con scorciatoie.

1. **Le personas si campionano, non si inventano.** Gli attributi strutturali (settore, dimensione d'impresa, area, ruolo) si estraggono dalle distribuzioni in `data/processed/istat/` con un campionamento riproducibile (seed fisso). Non chiedere mai all'LLM di "inventare" un panel da una descrizione testuale. L'LLM genera solo la biografia, vincolata agli attributi campionati e ancorata a citazioni reali da `data/processed/`.
2. **La calibrazione fa parte del flusso.** Il modulo `backend/app/report/calibration.py` confronta il ranking del panel con gli esiti reali (engagement LinkedIn) e calcola il fidelity score. Ogni report espone il fidelity score disponibile, o dichiara esplicitamente che manca.

## Chi lavora dove

- **Salvo, AI e backend:** `backend/`, `prompts/`, `data/`
- **Fabio, design e frontend:** `frontend/`, `design/`
- **Insieme:** `shared/schemas/`. Non modificare gli schemi senza segnalarlo: sono il contratto tra frontend e backend.

## Comandi

```bash
# backend
cd backend && uvicorn app.main:app --reload
cd backend && pytest
cd backend && ruff check . && ruff format .

# frontend
cd frontend && npm run dev
cd frontend && npm run lint && npm run typecheck && npm test
```

## Convenzioni

- Codice, nomi di variabili e commit in inglese. Testi della UI, prompt e output delle personas in italiano.
- Python: type hints ovunque, Pydantic per i modelli, generati da o allineati a `shared/schemas/`.
- TypeScript strict. Tipi derivati da `shared/schemas/`, mai ridefiniti a mano.
- Commit piccoli, messaggi in stile Conventional Commits (`feat:`, `fix:`, `chore:`).

## AI

- I prompt stanno in `prompts/`, un file per prompt, mai inline nel codice.
- Modelli e parametri da variabili d'ambiente (`PERSONA_MODEL`, `REPORT_MODEL`), mai hardcoded.
- Le personas rispondono sempre in JSON validato contro `shared/schemas/response.schema.json`. Se la validazione fallisce, un solo retry, poi errore esplicito.
- Usa il prompt caching su profilo della persona e stimolo, che si ripetono per tutte le domande.
- Non introdurre cache semantica: renderebbe le personas omogenee.
- Le personas non devono conoscere l'obiettivo del test. Le prime reazioni si chiedono a freddo.
- Le chiamate alle personas di un panel sono indipendenti e in parallelo, con un limite di concorrenza configurabile.

## Playwright

- Massimo 2–3 sessioni di cattura per prototipo, una per flusso, definite in `backend/app/capture/flows/`.
- Per ogni schermata salva screenshot e struttura semplificata della pagina. Le personas lavorano sulle catture, mai su un browser.

## Dati e privacy

- Non leggere né committare `data/raw/`.
- Nessun dato personale identificabile in `data/processed/`, nei prompt, nei test o nei log.
- I test non chiamano l'API reale: usa fixture in `backend/tests/fixtures/`.

## Frontend

- Tre schermate: Panel, Test, Report. Niente altro senza accordo.
- Finché un endpoint non è pronto, usa mock basati sugli schemi condivisi.
- Il report mostra sempre che i risultati sono simulati, insieme alla distribuzione delle risposte e non solo alla media.

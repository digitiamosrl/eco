# Piano: API con fixture (B1 + B2)

Branch `feat/api-fixtures`. Obiettivo: tutte le rotte del contratto rispondono con dati fissi nella forma giusta, così Fabio si collega al posto dei mock. Scadenza 4 novembre. Nessuna chiamata a modelli, nessun dato reale.

Provvisorio finché Fabio non conferma il punto 1 del contratto (status in inglese, `stimuli` dentro `Test`, nessuna cancellazione).

## Fuori da questo piano

`report-prototype` (punto 4), upload multipart e `GET /files` (punti 2 e 6), SQLite, runner reale, Playwright, qualsiasi chiamata AI. Non toccare `frontend/`, `design/`, `prompts/`, `data/`.

## Regole

- Test prima (RED), poi implementazione (GREEN), poi `ruff`. Commit piccoli in stile Conventional Commits, in inglese, uno per task.
- Codice e nomi in inglese; messaggi di errore all'utente in italiano.
- Gli schemi in `shared/schemas/` sono il contratto: i modelli Pydantic si allineano a loro, non il contrario. Non modificare gli schemi esistenti.
- Modelli immutabili: `model_config = ConfigDict(frozen=True)` dove ha senso, e `model_copy(update=...)` invece di mutare.
- Non fare push. Lascia il branch in locale.

## Task

### T1. Schemi `Test` e `Flow`

Crea in `shared/schemas/`:

- `test.schema.json`: `id` (string), `kind` (enum `post`, `prototype`), `status` (enum `queued`, `running`, `done`, `error`), `created_at` (string, format `date-time`), `done_count` (integer ≥ 0), `total_count` (integer ≥ 0), `stimuli` (array di `$ref` a `stimulus.schema.json`), `error` (string, facoltativo). Richiesti tutti tranne `error`. `additionalProperties: false`.
- `flow.schema.json`: `id`, `name` (string), `screen_count` (integer ≥ 1), `captured_at` (date-time). Tutti richiesti.

Stesso stile degli schemi esistenti (draft 2020-12, `$id` = nome file).

### T2. Modelli Pydantic e fixture

- `backend/app/models.py`: `Persona`, `Stimulus`, `Response`, `Test`, `Flow`, `Report` (solo item dei post, come `report.schema.json`), con tipi `Literal` per gli enum. Nomi e campi identici agli schemi.
- `backend/app/fixtures/`: `personas.json` (almeno 6 personas diverse, stesso formato di `frontend/src/mocks/index.ts`), `flows.json` (2 flussi: `onboarding` e `preventivo`), `report_post.json` (copia di `mockReport` del frontend).
- Test `backend/tests/test_schemas.py`: ogni file di fixture e ogni oggetto restituito dall'API valida contro lo schema JSON corrispondente. I `$ref` tra schemi si risolvono con `referencing.Registry` caricando tutti i file di `shared/schemas/`. Aggiungi una funzione di supporto in `backend/tests/conftest.py` (`validate(name, data)`).

### T3. Rotte di lettura

In `backend/app/api/`, un file per risorsa, registrati in `main.py`:

- `GET /personas` restituisce `Persona[]` dalle fixture.
- `GET /flows` restituisce `Flow[]` dalle fixture.

Test per ciascuna: status 200, forma valida contro lo schema.

### T4. Test: creazione, stato, elenco

Store in memoria in `backend/app/store.py` (un dizionario di `Test`; commento `shortcut: in-memory, passare a SQLite con il runner reale (B3)`).

- `POST /tests`, JSON. Post: `{"kind": "post", "variants": [{"label": "A", "text": "..."}]}`, da 2 a 5 varianti. Prototipo: `{"kind": "prototype", "flow_ids": ["onboarding"]}`, almeno un id, tutti presenti in `flows.json`. Risponde 201 con il `Test` in `queued`. `total_count` = numero personas × numero stimoli (varianti, oppure schermate dei flussi scelti; per i flussi usa `screen_count`). `stimuli`: per i post `kind=post` con `id` = `variante-<label minuscola>`; per il prototipo una voce `prototype_screen` per schermata, con `flow_id` e `screen_index`.
- Un solo test alla volta: se ce n'è uno in `queued` o `running`, risponde 409 con `{"detail": "Un test è già in corso"}`.
- Task in background (`BackgroundTasks`): passa a `running`, incrementa `done_count` fino a `total_count`, poi `done`. Durata totale da `FIXTURE_DELAY_SECONDS` in `config.py` (default 3, in test 0).
- `GET /tests` restituisce l'elenco, dal più recente. `GET /tests/{id}` restituisce il test, 404 con `{"detail": "Test non trovato"}`.

Test: creazione valida per post e prototipo, 409 sul secondo test, 404, transizione fino a `done` con ritardo 0, validazione schema.

### T5. Report e errori

- `GET /tests/{id}/report`: 404 se il test non esiste, 409 con `{"detail": "Il test non è ancora completato"}` se non è `done`. Per i test `post`: clona l'item di `report_post.json` per ogni stimolo del test (`stimulus_id` e `responses[].stimulus_id` sostituiti, `rank` in ordine, `test_id` del test). Per i test `prototype`: 501 con `{"detail": "Report del prototipo non ancora disponibile"}`.
- Handler per `RequestValidationError` in `main.py`: risponde 422 con `{"detail": "<stringa in italiano>"}` (es. `Richiesta non valida: variants`), mai la lista di errori di FastAPI.

Test: 404, 409, 501, report valido contro `report.schema.json`, formato del 422.

### T6. Chiusura

- `cd backend && pytest && ruff check . && ruff format .` tutti verdi.
- Aggiungi in `docs/` una sezione breve in fondo a `piano-api-fixture.md`: stato (cosa funziona, cosa è stub) e come avviare (`uvicorn`, `curl` di esempio per `POST /tests`).

## Verifica finale

Avvia `uvicorn`, crea un test post con 2 varianti via `curl`, interroga `GET /tests/{id}` finché `done`, poi `GET /tests/{id}/report`. Riporta l'output reale.

## Stato finale

**Funziona**

- `GET /health`, `GET /personas` (6 personas), `GET /flows` (`onboarding`, `preventivo`).
- `POST /tests` per post (2–5 varianti) e prototipo (flussi noti), `GET /tests`, `GET /tests/{id}`.
- `GET /tests/{id}/report` per i post, con report valido contro `report.schema.json`.
- Errori: 404 `Test non trovato`, 409 `Un test è già in corso` e `Il test non è ancora completato`, 501 per il report del prototipo, 422 `Richiesta non valida: <campo>`.
- Test: 24 in `backend/tests` (pytest), copertura di `app/` al 100%. `ruff check` e `ruff format --check` puliti.

**Stub**

- Store in memoria: i test spariscono al riavvio di `uvicorn`.
- Esecuzione simulata: il task in background avanza `done_count` in `FIXTURE_DELAY_SECONDS` (default 3 s). Nessuna persona reale, nessuna chiamata a modelli.
- Il report dei post è sempre lo stesso item di `report_post.json`, clonato per ogni stimolo.
- Non ancora: report del prototipo, upload multipart, `GET /files`, SQLite, runner reale, Playwright.

**Scelte dove il piano era ambiguo**

1. Flusso sconosciuto in `flow_ids`: 422 con `Flusso non trovato: <id>`.
2. Ordine dei controlli sul report: 404, poi 409, poi 501.
3. Oltre al piano: rifiutate varianti con etichetta duplicata (senza distinzione di maiuscole) e `flow_ids` duplicati, perché produrrebbero id di stimolo duplicati.
4. Id degli stimoli prototipo: `<flow_id>-<indice>` con indice da 0, per esempio `onboarding-0`.
5. Body malformato o senza `kind`: 422 `Richiesta non valida: corpo`.
6. `validate` in `backend/tests/conftest.py` è una fixture pytest, non una funzione importabile.
7. Il formato `date-time` non viene verificato da jsonschema senza `rfc3339-validator`, che non è in `requirements.txt`. Verificato: `not-a-date` passa la validazione. I test controllano solo che il valore sia una stringa.
8. Le fixture stanno in `backend/app/fixtures/`, come da piano. `backend/tests/fixtures/` resta vuota.
9. La rotta del report è in `backend/app/api/reports.py`, separata da `tests.py`.

**Come avviare**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Esempi (con il server su `http://127.0.0.1:8000`):

```bash
curl -s -X POST http://127.0.0.1:8000/tests \
  -H 'Content-Type: application/json' \
  -d '{"kind":"post","variants":[{"label":"A","text":"Testo A"},{"label":"B","text":"Testo B"}]}'

curl -s http://127.0.0.1:8000/tests/<id>            # status queued -> running -> done
curl -s http://127.0.0.1:8000/tests/<id>/report     # solo a test done
```

## Aggiornamento: flusso post (branch `feat/post-pipeline`)

Per i post il backend ora è vero, con un risponditore finto al posto del modello. Dettagli in `docs/piano-backend-post.md`, sezione "Stato finale".

- Store in SQLite (`DATABASE_PATH`), non più in memoria: i test sopravvivono al riavvio, quelli rimasti attivi passano a `error`.
- `POST /tests` per i post accetta multipart con immagini (`variants[i][image]`), e `GET /files/{name}` le serve.
- Il report dei post viene calcolato dalle risposte salvate, non più clonato dalla fixture.
- Il prototipo resta com'era: task finto con `FIXTURE_DELAY_SECONDS` e report `501`.

Avvio e prova rapida:

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload
curl -s -F kind=post -F 'variants[0][label]=A' -F 'variants[0][text]=Testo A' \
  -F 'variants[1][label]=B' -F 'variants[1][text]=Testo B' http://127.0.0.1:8000/tests
curl -s http://127.0.0.1:8000/tests/<id>            # done quando done_count = total_count
curl -s http://127.0.0.1:8000/tests/<id>/report
```

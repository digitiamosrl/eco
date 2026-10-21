# Piano: backend completo per il flusso post LinkedIn

Branch `feat/post-pipeline`, partendo da `feat/api-fixtures` (PR 3 non ancora in `main`). Scopo: dal `POST /tests` multipart al report, tutto funzionante con un risponditore finto al posto del modello. La parte AI (provider, prompt, personas reali) si aggancia dopo tramite un'interfaccia, senza toccare il resto.

## Fuori scope

Prototipo (flussi, Playwright, `report-prototype`: lascia com'è, non rimuovere né estendere), "diverge", qualsiasi chiamata a modelli o rete, `frontend/`, `design/`, `prompts/`, `data/`, schemi esistenti.

## Regole

- Test prima (RED), poi implementazione (GREEN), poi `ruff`. **Commit frequenti**: uno per ogni coppia test+implementazione, Conventional Commits in inglese. **Mai trailer `Co-Authored-By`** né altre righe di attribuzione.
- Codice in inglese, messaggi all'utente in italiano, errori `{"detail": "<stringa>"}`.
- Oggetti immutabili (`model_copy(update=...)`, niente mutazione in place).
- Nessun test chiama rete o API reali. Niente push.
- Ogni scorciatoia con limite noto: commento `shortcut: <limite>, <quando cambiare>`.

## Task

### P1. Persistenza SQLite

Sostituisci `store.py` in-memory con SQLite (`sqlite3` della stdlib, `DATABASE_PATH` da `config.py`).

- Tabelle: `tests` (come `Test`, `stimuli` in JSON), `responses` (`test_id`, `persona_id`, `stimulus_id`, JSON della `Response`).
- Una connessione per operazione (o per richiesta), così è sicuro con task in background. Crea le tabelle all'avvio dell'app (lifespan).
- La guardia "un test alla volta" diventa atomica: l'inserimento di un test `queued` fallisce se ne esiste uno `queued`/`running`, nella stessa transazione. Resta il 409.
- Un test rimasto `running` al riavvio passa a `error` con `"Il server è stato riavviato durante il test"` (all'avvio).
- Nei test usa un database temporaneo (`tmp_path`), mai il file di sviluppo. Le rotte esistenti continuano a passare.

### P2. `POST /tests` multipart per i post, e `GET /files`

Segui il formato di `docs/piano-backend-per-frontend.md`: `multipart/form-data` con `kind=post`, `variants[0][label]`, `variants[0][text]`, `variants[0][image]` (file facoltativo), da 2 a 5 varianti. FastAPI non legge nativamente `variants[0][label]`: usa `await request.form()` e raggruppa le chiavi con una regex, in una funzione piccola e testata.

- Aggiungi `python-multipart` a `requirements.txt` e installalo nel venv.
- Il corpo JSON del prototipo resta accettato com'è (stessa rotta, scelto da `Content-Type`).
- Validazione, 422 in italiano: 2–5 varianti, `label` e `text` non vuoti, etichette uniche, immagine solo `image/png`, `image/jpeg` o `image/webp`, massimo 5 MB (costante in `config.py`), controllo sul tipo reale dal contenuto (magic bytes), non solo sull'estensione o sull'header.
- Le immagini si salvano in `UPLOAD_DIR` (default `data/uploads/`, aggiungilo a `.gitignore`) con nome `<uuid><ext>` generato dal server, mai dal nome del client. `Stimulus.image_url` = `/files/<nome>`.
- `GET /files/{name}`: serve solo file di `UPLOAD_DIR`; rifiuta con 404 qualsiasi nome con `/`, `..` o che non esista (niente path traversal; test dedicato).

### P3. Interfaccia del risponditore e runner

- `backend/app/engine/responder.py`: `Protocol` `Responder` con `async respond(persona: Persona, stimulus: Stimulus) -> Response`.
- `FakeResponder`: deterministico (seed da `persona.id` + `stimulus.id`), restituisce `Response` valide con score 1–5, `thought` e `said` in italiano, `objections` a volte non vuote. Nessuna rete.
- `LlmResponder`: stub che solleva `NotImplementedError("Provider AI non ancora configurato")`. Scelta da `RESPONDER=fake|llm` in `config.py` (default `fake`).
- `backend/app/engine/runner.py`: dato un test, esegue persona × stimolo con `asyncio.Semaphore(PANEL_CONCURRENCY)`; ogni risposta si valida contro `response.schema.json` (se non valida: un solo retry, poi errore esplicito); salva la risposta e incrementa `done_count` nel DB; a fine corsa `done`. Se una chiamata fallisce dopo il retry: il test passa a `error` con un messaggio in italiano (senza dettagli interni), le chiamate rimaste si fermano.
- Il runner sostituisce il task finto di `POST /tests` per i post. Per il prototipo lascia il task finto com'è. Rimuovi `FIXTURE_DELAY_SECONDS` solo se resta inutilizzato.

Test: avanzamento fino a `done`, concorrenza massima rispettata (responder che conta le chiamate simultanee), retry su risposta non valida, `error` su fallimento, `done_count`/`total_count` corretti.

### P4. Report dai dati veri

- `backend/app/report/aggregate.py` (puro, senza I/O): da `Response[]` per stimolo calcola `mean_score` (arrotondato a 2 decimali), `score_distribution` con tutte le chiavi `"1"`–`"5"`, `rank` (media decrescente, parità: ordine delle varianti), `objections` (le più frequenti, massimo 5, senza duplicati).
- `backend/app/report/summarize.py`: `Protocol` `Summarizer` con `said_summary`, `thought_summary` per stimolo e `summary` complessivo. `FakeSummarizer` compone testo semplice dai dati (es. media e obiezione più frequente). `LlmSummarizer` stub come sopra, scelto da `SUMMARIZER=fake|llm`.
- `GET /tests/{id}/report` per i post costruisce il `Report` dalle risposte salvate. Resta 404/409. Elimina l'uso di `report_post.json` e il codice che clonava la fixture; tieni il file solo se serve ancora ai test, altrimenti cancellalo.
- `simulated: true` sempre.

Test: aggregazione su dati noti (ranking, distribuzione, parità), report valido contro `report.schema.json`, test end-to-end `POST` multipart → polling → `done` → report coerente.

### P5. Pulizia e chiusura

- `GET /personas`: lascia le fixture (le personas reali arrivano da A2) con un commento `shortcut: fixture, sostituire con il panel generato (A2)`.
- Valida la configurazione all'avvio solo dove serve (es. `RESPONDER=llm` senza `PERSONA_MODEL` → errore chiaro).
- Aggiorna `docs/piano-api-fixture.md` (sezione stato) e questo file con "Stato finale": cosa funziona, cosa è stub, deviazioni.
- `cd backend && pytest && ruff check . && ruff format .` verdi.

## Verifica finale

Avvia `uvicorn`; con `curl -F` crea un test con 2 varianti, una con immagine; poll `GET /tests/{id}` fino a `done`; `GET /tests/{id}/report`; apri `GET` dell'`image_url`. Prova anche un file non immagine (422) e `GET /files/..%2Fconfig.py` (404). Riporta l'output reale.

## Stato finale

**Funziona** (verificato con `uvicorn` e `curl`, output reale in fondo)

- Persistenza SQLite (`DATABASE_PATH`, default `eco.sqlite`), tabelle `tests` e `responses`, creazione tabelle nel lifespan. Il vincolo "un test alla volta" è una transazione `BEGIN IMMEDIATE`. I test usano un database temporaneo.
- `POST /tests` JSON (post e prototipo) e multipart per i post, con immagini PNG/JPEG/WebP riconosciute dai magic bytes, massimo 5 MB, nome file generato dal server (`data/uploads/`, gitignored). Un 409 cancella le immagini appena scritte.
- `GET /files/{name}`: solo file diretti di `UPLOAD_DIR`; nome con `/`, `..` o inesistente risponde 404.
- Runner dei post (`app/engine/runner.py`): concorrenza da `PANEL_CONCURRENCY`, risposta validata contro `response.schema.json` con un solo retry, `done_count` aggiornato per ogni risposta, `done` a fine corsa. Al primo errore le chiamate rimaste non partono e il test passa a `error` con un messaggio italiano senza dettagli interni (il dettaglio va nel log del server).
- Report dei post costruito dalle risposte salvate: `aggregate.py` (puro) per media, distribuzione, rank, obiezioni, `summarize.py` (FakeSummarizer), `builder.py`. `simulated: true` sempre.
- Validazione all'avvio: `RESPONDER=llm` senza `PERSONA_MODEL` e `SUMMARIZER=llm` senza `REPORT_MODEL` falliscono con un messaggio chiaro.
- Test: 72 passati, copertura di `app/` al 99%. `ruff check` e `ruff format` puliti.

**Stub**

- `LlmResponder` e `LlmSummarizer` sollevano `NotImplementedError("Provider AI non ancora configurato")`. Il runner lo trasforma in `error` con il messaggio generico.
- `FakeResponder` è deterministico (seed da persona + stimolo): nessuna persona reale.
- `GET /personas` resta sulle fixture (commento `shortcut`).
- Prototipo: task finto con `FIXTURE_DELAY_SECONDS` invariato, report ancora `501`.
- Non ancora: report del prototipo, Playwright, provider AI, prompt in `prompts/`.

**Deviazioni dal piano e scelte dove era ambiguo**

1. Al riavvio passano a `error` anche i test in `queued`, non solo quelli in `running`. Un `queued` orfano bloccherebbe ogni nuovo test con 409 per sempre.
2. `GET /files/..%2Fconfig.py` risponde 404 con il corpo di default di FastAPI (`{"detail":"Not Found"}`), non con `File non trovato`: la richiesta non arriva alla rotta.
3. `FakeSummarizer` e `LlmSummarizer` sono `async` come il `Responder`, così il provider AI non cambia il protocollo.
4. Il database di sviluppo è `backend/eco.sqlite` (ignorato da git). I test usano un file temporaneo per ogni test.
5. `report_post.json` non è più usato dalle rotte, ma `tests/test_schemas.py` lo valida: il file resta.
6. `python-multipart` è fissato a `0.0.32` in `requirements.txt`.
7. I test asincroni usano il plugin `anyio` che arriva con starlette, senza `pytest-asyncio`.
8. Le immagini vengono scritte dopo la validazione e prima dell'inserimento del test. Se il 409 scatta, vengono cancellate.
9. Il formato `date-time` non è verificato (come nel piano precedente).

**Verifica finale** (uvicorn su porta 8765, `curl` reali, database di sviluppo)

- `POST /tests` multipart con 2 varianti, B con PNG: `HTTP 201`, `status: queued`, `total_count: 12`, `image_url: /files/<uuid>.png`.
- Polling di `GET /tests/{id}`: `done 12 12`.
- `GET /tests/{id}/report`: `simulated: true`, ranking e distribuzione coerenti con le risposte salvate.
- `GET` dell'`image_url`: `HTTP 200 image/png`, 74 byte, come il file caricato.
- File non immagine con estensione `.png`: `HTTP 422 {"detail":"Formato immagine non valido: usa PNG, JPEG o WebP"}`.
- `GET /files/..%2Fconfig.py`: `HTTP 404`.

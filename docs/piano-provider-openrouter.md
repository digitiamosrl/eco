# Piano: provider AI via OpenRouter

Branch `feat/openrouter-provider`, da `feat/post-pipeline` (PR 4 non ancora in `main`). Scopo: sostituire gli stub `LlmResponder` e `LlmSummarizer` con chiamate reali a OpenRouter, senza cambiare runner, report o API.

## Decisione

Non si può usare l'API Anthropic (solo abbonamento). Si usa **OpenRouter** (chiave già disponibile), con `httpx`, già in `requirements.txt`: nessuna nuova dipendenza. Si rimuove `anthropic` da `requirements.txt` perché non usata. Chiamate a `POST https://openrouter.ai/api/v1/chat/completions`, formato OpenAI chat completions.

## Cosa dicono i docs di OpenRouter (verificato)

- `response_format: {"type": "json_schema", "json_schema": {"name", "strict", "schema"}}`. Il supporto è **per endpoint**, non per modello. Con `provider: {"require_parameters": true}` OpenRouter scarta gli endpoint che non lo supportano. L'applicazione dello schema varia per provider: va sempre rivalidato lato nostro.
- Prompt caching di Claude via OpenRouter: `cache_control` sui blocchi; minimo 4096 token per Haiku 4.5, 512 per i modelli più nuovi. **Per la POC non serve:** ogni coppia persona × stimolo si chiama una volta e i post sono brevi (sotto il minimo). Non implementare il caching ora: `shortcut: nessun prompt caching, post brevi e una chiamata per coppia; riconsiderare con più domande per persona`.

## Fuori scope

Generazione delle personas (A2), dati, prototipo, frontend, schemi, modifiche a runner/report/API oltre al necessario. Nessun test chiama la rete.

## Regole

- Test prima (RED/GREEN), poi `ruff`. Commit frequenti, uno per coppia test+implementazione, Conventional Commits in inglese. **Mai `Co-Authored-By`** né altra attribuzione. Niente push.
- Codice in inglese, testi per l'utente e prompt in italiano. Prompt in `prompts/`, mai inline. Modelli e parametri da variabili d'ambiente.
- Nessuna chiave nei log, nei test o nei messaggi di errore. Errori all'utente in italiano e senza dettagli interni.
- Scorciatoie con limite noto: commento `shortcut: <limite>, <quando cambiare>`.

## Task

### Q1. Configurazione e client

- `config.py`: aggiungi `openrouter_api_key`, `openrouter_base_url` (default `https://openrouter.ai/api/v1`), `llm_timeout_seconds` (default 60). `persona_model` e `report_model` sono già presenti: devono contenere gli id modello di OpenRouter. Aggiorna `.env.example` (`OPENROUTER_API_KEY=`, esempi di id commentati, senza inventare id: lascia vuoto o un segnaposto `<id-modello-openrouter>`).
- La validazione all'avvio esistente (`RESPONDER=llm` senza modello) richiede anche `OPENROUTER_API_KEY`, con errore chiaro.
- `backend/app/engine/llm_client.py`: funzione `async chat_json(client: httpx.AsyncClient, *, model, messages, schema_name, schema) -> dict`. Invia `response_format` json_schema con `strict: true` e `provider: {"require_parameters": true}`, header `Authorization`. Estrae il JSON da `choices[0].message.content` (se è racchiuso in un blocco ```json, lo scarta). Su 429 e 5xx riprova una volta con breve attesa; su altri errori o JSON non parsabile solleva un'eccezione `LlmError` con messaggio in italiano senza dettagli interni (nessuna chiave, nessun corpo di risposta).
- Test con `httpx.MockTransport`: richiesta ben formata (header, model, response_format, require_parameters), risposta ok, JSON in blocco ```json, 429 poi ok, 500 persistente, JSON non valido, chiave mai presente negli errori.

### Q2. `LlmResponder`

- Carica `prompts/persona_response.md`, sostituisce `{persona}` (profilo della persona) e `{stimulus}` (testo del post). Il prompt chiede `persona_id` e `stimulus_id` nell'output: **non farli generare al modello**. Rimuovi dal prompt la riga che li elenca e riempili nel codice; lo schema inviato al modello è quello di `response.schema.json` senza `persona_id` e `stimulus_id`, costruito a runtime. Aggiorna il commento di bozza del prompt di conseguenza.
- Se lo stimolo ha `image_url` (`/files/<nome>`), leggi il file da `UPLOAD_DIR` (solo nomi validi, niente path traversal) e invialo come blocco `image_url` con data URL base64 nel messaggio utente. Se il file manca: `LlmError`.
- Il modello usato è `PERSONA_MODEL`. La risposta si valida con il percorso già esistente nel runner (schema + un retry); non duplicare la validazione.
- Un `httpx.AsyncClient` condiviso, creato una volta (lifespan o lazy), con `llm_timeout_seconds`.
- Test con `MockTransport`: prompt composto bene, ids riempiti dal codice, immagine inclusa come data URL, nome file non valido rifiutato, risposta valida attraversa il runner end-to-end.

### Q3. `LlmSummarizer`

- Nuovo `prompts/report_summary.md` (italiano): riceve, per una variante, le risposte (`thought`, `said`, `score`, `objections`) e produce JSON `{said_summary, thought_summary}`; il `thought_summary` evidenzia dove diverge dal detto. Un secondo prompt breve `prompts/report_overview.md` per il `summary` complessivo (ranking e conclusioni, specificando che i risultati sono simulati).
- Usa `REPORT_MODEL`. Output validato contro uno schema piccolo definito nel codice (due stringhe non vuote; una per il riepilogo complessivo).
- Test con `MockTransport`, incluso il caso risposta non valida → `LlmError`.

### Q4. Verifica con la chiave reale (la esegue l'utente, non tu)

Crea `backend/scripts/smoke_llm.py`: carica `.env`, prende 3 personas dalle fixture e un post breve di esempio (testo, senza immagine), esegue 12 chiamate `LlmResponder` con la concorrenza configurata, stampa: quante risposte valide al primo tentativo, quante dopo il retry, quante fallite, latenza media, un esempio di `thought`/`said`, e il `usage` dei token se presente nelle risposte. Non gira nei test né in `pytest`. Documenta in `docs/piano-provider-openrouter.md` come lanciarlo. **Non lanciarlo tu** (nessuna chiave disponibile).

### Q5. Chiusura

- `cd backend && pytest && ruff check . && ruff format .` verdi.
- Aggiorna `CLAUDE.md`: sezione AI — niente più riferimento a "Claude API" e al prompt caching come regola (resta "non introdurre cache semantica"); modelli via OpenRouter, ids da `PERSONA_MODEL`/`REPORT_MODEL`. Aggiorna `README.md` (stack, avvio con `OPENROUTER_API_KEY`).
- Compila la sezione "Stato finale" di questo file: cosa funziona, cosa è stub, deviazioni.

## Stato finale

**Funziona (con test, tutti con `MockTransport`):**
- Configurazione: `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `LLM_TIMEOUT_SECONDS`. All'avvio, `RESPONDER=llm` o `SUMMARIZER=llm` senza chiave o senza modello si fermano con errore chiaro.
- `chat_json` in `backend/app/engine/llm_client.py`: `response_format` json_schema strict, `require_parameters`, estrazione da blocco ```json, un retry su 429 e 5xx, errori come `LlmError` in italiano senza chiave né corpo di risposta.
- `LlmResponder`: prompt da `prompts/persona_response.md` con ids riempiti dal codice, immagine `/files/<nome>` come data URL, nome file validato da `find_upload`, risposta passata alla validazione del runner.
- `LlmSummarizer`: `prompts/report_summary.md` per variante, `prompts/report_overview.md` per il riepilogo complessivo (dichiara che i risultati sono simulati). Output validato con schema piccolo nel codice.
- Errore del summarizer nel report: HTTP 503 con messaggio in italiano.

**Stub:** nessuno in responder e summarizer. Restano `FakeResponder` e `FakeSummarizer`, il default (`RESPONDER=fake`, `SUMMARIZER=fake`).

**Non verificato con la rete:** lo schema con `strict: true` e i campi opzionali (`misunderstood`, `would_abandon`), e `require_parameters` su modelli reali. Va chiarito con `scripts/smoke_llm.py` e la chiave reale, da eseguire dall'utente.

**Deviazioni dal piano:**
1. Responder: un output che passa lo schema ma non costruisce `Response` (es. `score` fuori range) diventa `LlmError` subito, senza il retry del runner. Il retry del runner copre solo le risposte restituite e non valide.
2. Summarizer: `said_summary` e `thought_summary` di una variante vengono dalla stessa chiamata, memorizzata nell'istanza (un'istanza per report). Il piano parlava di una chiamata per variante: così è una sola. Il riepilogo complessivo non chiama il modello se il ranking è vuoto.
3. `reports.py`: aggiunto il mapping `LlmError` → 503 (non previsto dal piano), per non restituire un 500 non gestito.
4. `chat_json`: errori di rete e timeout diventano `LlmError` senza retry (il piano prevedeva il retry solo su 429 e 5xx). 401 e 403 danno un messaggio dedicato alla chiave.
5. Client HTTP: singleton lazy a livello di modulo (`shared_client()`), non chiuso esplicitamente. Shortcut documentato nel codice.
6. Smoke script: "12 chiamate" sono 3 personas × 4 ripetizioni dello stesso post breve. Il "valido" usa `_is_valid` del runner. Il `usage` viene letto con un event hook del client, perché `chat_json` restituisce solo il JSON.
7. Dipendenza `anthropic` rimossa da `requirements.txt`. Il venv locale la ha ancora installata: non è stata disinstallata.
8. `backend/.env.example`: `PERSONA_MODEL` e `REPORT_MODEL` ora vuoti (prima c'erano id Anthropic, non validi per OpenRouter).
9. Lo script `smoke_llm.py` non è stato eseguito (come richiesto). È stata verificata solo la funzione di report su dati sintetici.

## Verifica con la chiave reale (Q4)

Eseguita dall'utente, non dai test. Lo script `backend/scripts/smoke_llm.py` fa 12 chiamate (3 personas × 4 ripetizioni di un post breve, senza immagine) con la concorrenza di `PANEL_CONCURRENCY` e stampa: risposte valide al primo tentativo, dopo retry, fallite, latenza media, un esempio di `thought`/`said` e i token (se OpenRouter restituisce `usage`).

Come lanciarlo, da `backend/` con `.venv` attivo e nel `.env`:

```bash
OPENROUTER_API_KEY=<chiave>
PERSONA_MODEL=<id-modello-openrouter>
python -m scripts.smoke_llm
```

Non è incluso in `pytest`. Se mancano chiave o modello, esce con un messaggio senza stampare valori.

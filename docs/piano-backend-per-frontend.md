# Cosa serve al frontend dal backend

Proposta di Fabio per Salvo, da chiudere insieme il 21 ottobre. Copre solo ciò che le tre schermate (Panel, Test, Report) devono leggere e inviare. Come il backend genera personas, chiama i modelli e aggrega i risultati resta una scelta di Salvo.

Vedi anche `docs/piano-frontend.md` e i wireframe in `design/wireframes.html`.

## Endpoint

| Metodo | Percorso | Serve a | Restituisce |
| --- | --- | --- | --- |
| `GET` | `/personas` | Schermata Panel | `Persona[]` |
| `GET` | `/flows` | Test prototipo: scelta dei flussi | `Flow[]` |
| `POST` | `/tests` | Avvio di un test | `Test` |
| `GET` | `/tests` | Report: elenco dei test passati | `Test[]` |
| `GET` | `/tests/{id}` | Test in corso: polling ogni 2–3 s | `Test` |
| `GET` | `/tests/{id}/report` | Schermata Report | `Report` |
| `GET` | `/files/...` | Immagini dei post e screenshot del prototipo | file statici |

In sviluppo il frontend chiama `/api/...` e Vite lo inoltra a `localhost:8000` senza il prefisso, quindi non serve CORS.

Errori: il formato standard di FastAPI, `{"detail": "..."}`, con un messaggio in italiano mostrabile all'utente.

## Avvio di un test: `POST /tests`

**Post**: `multipart/form-data`, perché ci sono immagini:

```
kind = post
variants[0][label] = A
variants[0][text]  = ...
variants[0][image] = <file>   (facoltativa)
... da 2 a 5 varianti
```

**Prototipo**: JSON:

```json
{ "kind": "prototype", "flow_ids": ["onboarding", "preventivo"] }
```

Il backend risponde subito con il `Test` in stato `queued` e lavora in background. Il frontend non resta in attesa della risposta finché il test non finisce.

## Schemi nuovi in `shared/schemas/`

Bozza, da scrivere come JSON Schema una volta concordata.

**Test**

```
id            string
kind          "post" | "prototype"
status        "queued" | "running" | "done" | "error"
created_at    string (ISO 8601)
done_count    integer   risposte ricevute
total_count   integer   personas × stimoli
error         string?   solo se status = error, in italiano
```

Il frontend usa `done_count / total_count` per la barra di avanzamento e passa al report quando lo stato è `done`.

**Flow**

```
id            string
name          string
screen_count  integer
captured_at   string (ISO 8601)
```

**Report del prototipo**

Oggi `report.schema.json` descrive solo il ranking dei post. Proposta: gli `items` del prototipo sono le schermate:

```
flow_id          string
screen_index     integer
title            string
screenshot_url   string
abandon_rate     number 0–1
issues           string[]     criticità con conteggio
said_summary     string
thought_summary  string
responses        Response[]
```

Da decidere: un solo schema Report con due tipi di item distinti da `kind`, oppure due schemi separati. Per il frontend vanno bene entrambi; due schemi separati sono più semplici da leggere.

## Già concordato o in bozza

- `Response` con `thought` (pensiero privato, generato per primo) e `said` (cosa direbbe in pubblico). Il prompt in bozza è in `prompts/persona_response.md`.
- `Report` per i post: ranking, distribuzione, obiezioni, sintesi di cosa dicono e cosa pensano, tutte le risposte.
- `simulated: true` sempre presente nel report.

## Aperti

1. Panel fisso o con dimensione scelta dall'utente? Se fisso, `GET /personas` basta.
2. Etichetta "diverge" sulle risposte in cui pensiero e parole non coincidono: un campo in `Response` oppure calcolata nel report?
3. Più test contemporaneamente o uno alla volta? Uno alla volta è più semplice e per la POC basta.
4. **Etichetta della variante nel report.** Gli item del report hanno solo `stimulus_id`; il frontend lo mostra come "Variante {stimulus_id}". Per i post: usare la lettera (A, B, …) come id dello stimolo, oppure aggiungere `variant_label` agli item del report.
5. **Formato multipart.** FastAPI non trasforma da solo `variants[0][label]` in una lista: serve leggere `request.form()` a mano. Alternativa più semplice: campi ripetuti `labels`, `texts`, `images`. Il frontend si adatta a quello che sceglie Salvo.
6. **Schema Test rigido.** `test.schema.json` ha `additionalProperties: false`: il backend non può aggiungere campi senza aggiornare lo schema.

## Calendario

La proposta principale: **endpoint finti prima, veri dopo.** Se gli endpoint rispondono presto con dati fissi ma nella forma giusta, il frontend si collega subito e il 25 novembre non resta tutta l'integrazione da fare.

| Entro | Backend | Frontend lo usa per |
| --- | --- | --- |
| 21 ott | Schemi chiusi in `shared/schemas/` | Rigenerare i tipi, aggiornare i mock |
| 4 nov | Tutti gli endpoint con dati fissi (fixture), `POST /tests` che passa a `done` dopo qualche secondo | Collegare le schermate al posto dei mock |
| 18 nov | `GET /personas` e `POST /tests` per i post su dati reali | Prima prova vera del flusso post |
| 25 nov | Prototipo: `GET /flows`, screenshot, report per schermata | Completare il flusso prototipo |
| 2 dic | Tutto su dati reali | Prova completa con post Digitiamo già pubblicati |

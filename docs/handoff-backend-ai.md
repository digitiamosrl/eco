# Handoff backend e AI: da confermare con Fabio

Da: Salvo · Per: Fabio · Data: 21 ottobre 2026
Risponde a `docs/piano-backend-per-frontend.md`. Se confermi i punti 1–5, parto con lo sviluppo.

## 1. Decisioni da confermare

Ogni punto ha la mia proposta. Basta una spunta, oppure scrivi cosa cambiare.

- [ ] **Report prototipo:** due schemi separati (`report-post`, `report-prototype`), non uno unico con `kind`. Più semplici da leggere e da validare.
- [ ] **"Diverge":** non è un campo di `Response`. Lo calcola il report (confronto tra `thought` e `said`) ed espone un elenco di risposte divergenti per ogni item.
- [ ] **Panel fisso:** dimensione decisa dal backend, nessun parametro dall'utente. Per la POC basta `GET /personas`.
- [ ] **Un test alla volta:** se ne parte un secondo mentre uno è `running`, `POST /tests` risponde 409 con `{"detail": "Un test è già in corso"}`.
- [ ] **Endpoint e formato:** confermo la tabella e gli errori `{"detail": "..."}` in italiano del tuo piano, senza modifiche. `POST /tests` è multipart per i post e JSON per il prototipo.

## 2. Cosa ti consegno e quando

Le date sono le tue, le confermo.

| Entro | Consegna | Cosa cambia per te |
| --- | --- | --- |
| 21 ott | Schemi chiusi in `shared/schemas/`: `Test`, `Flow`, `report-prototype` | `npm run gen:types`, mock aggiornati |
| 4 nov | Tutti gli endpoint con fixture, `POST /tests` passa a `done` dopo qualche secondo | Colleghi le schermate al posto dei mock |
| 18 nov | `GET /personas` e `POST /tests` post su dati reali | Prima prova vera del flusso post |
| 25 nov | Prototipo: `GET /flows`, screenshot, report per schermata | Completi il flusso prototipo |
| 2 dic | Tutto su dati reali, validazione sui post Digitiamo già pubblicati | Prova completa |

## 3. Piano backend

1. **B1, schemi** (21 ott): `Test`, `Flow`, `report-prototype`, Pydantic allineati.
2. **B2, endpoint con fixture** (4 nov): API completa su dati fissi, SQLite, task in background.
3. **B3, runner reale** (18 nov): concorrenza `PANEL_CONCURRENCY`, avanzamento `done_count/total_count`, errori in italiano.
4. **B4, cattura Playwright** (25 nov): 2–3 flussi in `capture/flows/`, screenshot e struttura semplificata.

## 4. Piano AI

1. **A1, dati** (4 nov): ISTAT, CRM anonimizzato, analytics LinkedIn in `data/processed/`, più la scheda di contesto.
2. **A2, personas** (11 nov): attributi campionati dai dati, biografia generata dal modello leggero.
3. **A3, risposta persona** (18 nov): prompt `thought` → `said`, validazione contro lo schema con un retry, prompt caching.
4. **A4, report** (25 nov): ranking e distribuzione deterministici, sintesi con il modello capace.
5. **A5, analisi prototipo** (25 nov): abbandono e criticità per schermata.
6. **A6, prova di valore** (2 dic): ranking dei post pubblicati contro l'engagement reale.

## 5. Cosa mi serve da te

- [ ] La documentazione che hai detto di aggiungere in repo (contesto Digitiamo, tono, brand), così la leggo prima di scrivere i prompt.
- [ ] Merge o review della PR 1 (flusso post su mock), per partire dallo stesso `main`.
- [ ] Un riferimento per i test legali o di contenuto, se i post di prova richiedono approvazioni.

## 6. Rischi e punti aperti

- **Dati:** accesso a CRM e analytics LinkedIn e loro anonimizzazione sono il percorso critico dell'AI. Li sblocco io, ma slittano tutto se arrivano tardi.
- **Riuso:** verifico se il codice di MiroFish è riutilizzabile (licenza e cosa serve davvero) prima di scrivere da zero.
- **Tempo:** circa 4h a settimana a testa. Se A1 slitta, A2 e A3 usano personas di esempio finché i dati non arrivano.
- **Sync:** nella call è stato scritto "mercoledì 22 ottobre", ma il 22 è un giovedì. Intendevamo mercoledì 21?

## 7. Non faccio senza accordo

Modifiche agli schemi dopo la chiusura, cache semantica, navigazione libera degli agenti, nuovi endpoint oltre la tabella.

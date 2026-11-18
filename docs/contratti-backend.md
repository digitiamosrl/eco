# Contratti backend: cosa manca

Per: Salvo · Aggiornato al 10 novembre 2026 · Consegna 9 dicembre

Frontend e design system sono su `main` e sono pronti per tutti i punti qui sotto. Ogni punto indica cosa cambia nel contratto (`shared/schemas/`) e cosa vede l'utente finché il backend non lo implementa. Gli schemi sono già aggiornati. I campi nuovi sono facoltativi, così il backend di oggi continua a validare.

| # | Cosa | Contratto | Senza backend, oggi |
| --- | --- | --- | --- |
| 1 | ✅ Test con un solo post e allegato PDF | [handoff](handoff-post-singolo-e-import-prototipo.md) §1 | Il test con 1 post o con un PDF riceve un 422 |
| 2 | ✅ Azioni nel feed (`action`, `reaction`) | [handoff](handoff-post-singolo-e-import-prototipo.md) §1 | La card "La prima cosa che farebbero" dice che i dati non sono disponibili |
| 3 | ✅ Import del prototipo da Figma o da artifact | [handoff](handoff-post-singolo-e-import-prototipo.md) §2 | L'import riceve un 404 e il test di prototipo non parte |
| 4 | ✅ Divergenza calcolata dal report | sotto | Il frontend confronta i testi di detto e pensato |
| 5 | ✅ Fidelity score nel report (manca il dato) | sotto | Compare "calibrazione non ancora disponibile" |
| 6 | ✅ Report del prototipo | sotto | Compare "non ancora disponibile" |
| 7 | ✅ Personas: attributi come campi, biografia, ripiego | [contratto-personas.md](contratto-personas.md) | Panel e risposte funzionano come oggi |

Priorità consigliata: 4 e 5 sono piccoli e chiudono i principi del CLAUDE.md. Poi 1–2, che riusano la pipeline dei post. Il 3 è il più grosso.

## 4. Divergenza

È la decisione della PR #2: la divergenza la calcola il report, non la risposta.

`report.schema.json` → ogni item ha `divergent_persona_ids: string[]`, con gli id delle personas la cui risposta a quello stimolo diverge tra `said` e `thought`.
- Il calcolo spetta al backend, che può usare il modello del report oppure una regola. L'importante è che sia lo stesso per tutti.
- Va sempre presente, anche vuoto (`[]`). Se il campo manca, il frontend torna al confronto dei testi (`frontend/src/lib/diverge.ts`).

## 5. Fidelity score

È il principio 2 del CLAUDE.md: la calibrazione fa parte del flusso.

`report.schema.json` → `fidelity: { score, basis }`, facoltativo:

| Campo | Tipo | Significato |
| --- | --- | --- |
| `score` | numero tra -1 e 1 | Tau-b di Kendall tra il ranking del panel e l'engagement reale dei post Digitiamo già pubblicati. `kendall_tau_b` esiste già in `backend/scripts/compare_metrics.py` |
| `basis` | stringa in italiano | Su cosa è calcolato, per esempio «12 post Digitiamo pubblicati, ott 2025–set 2026» |

- Se la calibrazione non c'è ancora, il campo si omette e il frontend mostra lo stato "non disponibile".
- Va calcolato una volta, in `backend/app/report/calibration.py`, e riusato in ogni report. Non va ricalcolato per ogni test.
- Il report legge `data/processed/calibration.json` (`{score, basis}`). Finché il file non esiste, il campo si omette. Per produrlo servono l'engagement reale dei post pubblicati e un run del panel su quegli stessi post.
- Lo produce `python -m scripts.calibrate` (da `backend/`), leggendo `data/processed/published_posts.json`, versionato: solo testi pubblici e conteggi aggregati. Formato in `PublishedPost` dentro `backend/scripts/calibrate.py`.

## Da decidere insieme

- **Report del prototipo** (punto 6). Lo pensiamo insieme quando decidiamo cosa misurare per ogni schermata.

Deciso: il segmento è il pubblico della pagina LinkedIn di Digitiamo, PMI e grandi aziende, come lo campiona già il pool. Il testo di Panel, README e scheda di contesto è aggiornato. Il campionamento resta com'è.

## Come si usa l'import del prototipo (punto 3)

- **Figma:** serve `FIGMA_TOKEN` nel `.env` (token personale, sola lettura). Il file va condiviso con «chiunque abbia il link». Il link deve contenere `page-id` (Condividi › Copia link al prototipo): si scarica solo quella pagina, perché un file intero può pesare centinaia di MB. Senza `page-id` risponde 422. Parte dai punti di partenza del prototipo (o dal nodo del link) e segue il primo collegamento di ogni schermata, fino a 10 punti di partenza e 8 schermate per percorso (nel test se ne scelgono al massimo 3).
- **Artifact:** serve Chromium (`playwright install chromium`). Per ogni percorso si preme l'i-esimo pulsante della prima schermata e poi il primo che cambia la pagina, fino a 6 schermate. Al massimo 3 percorsi.
- **Test:** `POST /tests` con `prototype_id` e `paths` passa dalle personas come i post. `flow_ids` resta valido per i flussi già catturati. Il report del prototipo risponde ancora 501 (punto 6).
- Limite noto: un percorso è una catena, non esplora i rami. Si sceglie il primo collegamento non visitato.

## 6. Report del prototipo

Stesso endpoint e stesso schema dei post (`GET /tests/{id}/report`, `report.schema.json`): niente schema separato. Due campi facoltativi in più per ogni item, presenti solo se lo stimolo è una schermata (`kind: "prototype_screen"`):

| Campo | Tipo | Significato |
| --- | --- | --- |
| `abandon_count` | intero ≥ 0 | Quante personas lascerebbero perdere a questa schermata (`would_abandon`). Ogni schermata è valutata a freddo, quindi i conteggi non sono un imbuto |
| `misunderstood` | `string[]` | I passaggi fraintesi più frequenti, al massimo 5 |

- Con le schermate, `rank` 1 è il **punto più critico**: più abbandoni e, a parità, punteggio medio più basso. L'ordine del flusso resta quello di `test.stimuli` (`flow_id`, `screen_index`, `image_url`, `page_structure` come nome).
- `summary`, `said_summary` e `thought_summary` parlano di schermate, abbandoni e passaggi fraintesi.
- `fidelity` è sempre assente: la calibrazione è sui post pubblicati e per i prototipi non c'è. Il frontend mostra lo stato "non disponibile".
- I test di prototipo sui flussi a fixture (`flow_ids`) non passano dal panel: il loro report ha item senza risposte.

## 8. Compito nel test di prototipo

`POST /tests` per un prototipo importato richiede `task` (stringa, massimo 300 caratteri): cosa sta cercando di fare chi usa il prototipo, per esempio «chiedere un preventivo per il gestionale». Senza `task`, o con solo spazi, risponde 422. Ogni schermata lo riceve in `Stimulus.task` (campo nuovo e facoltativo in `stimulus.schema.json`) e il prompt della persona lo usa per giudicare la schermata.

- Motivo: nella prova del 18 novembre, senza compito, 30 personas su 30 abbandonavano alla prima schermata dicendo «non è un tool che uso». Giudicavano se l'app le riguarda, non se è usabile.
- Le personas sanno cosa vogliono fare, non cosa misura il test: il principio del CLAUDE.md resta valido.
- I flussi a fixture (`flow_ids`) non lo richiedono.

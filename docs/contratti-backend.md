# Contratti backend: cosa manca

Per: Salvo · Aggiornato al 10 novembre 2026 · Consegna 9 dicembre

Frontend e design system sono su `main` e sono pronti per tutti i punti qui sotto. Ogni punto indica cosa cambia nel contratto (`shared/schemas/`) e cosa vede l'utente finché il backend non lo implementa. Gli schemi sono già aggiornati. I campi nuovi sono facoltativi, così il backend di oggi continua a validare.

| # | Cosa | Contratto | Senza backend, oggi |
| --- | --- | --- | --- |
| 1 | Test con un solo post e allegato PDF | [handoff](handoff-post-singolo-e-import-prototipo.md) §1 | Il test con 1 post o con un PDF riceve un 422 |
| 2 | Azioni nel feed (`action`, `reaction`) | [handoff](handoff-post-singolo-e-import-prototipo.md) §1 | La card "La prima cosa che farebbero" dice che i dati non sono disponibili |
| 3 | Import del prototipo da Figma o da artifact | [handoff](handoff-post-singolo-e-import-prototipo.md) §2 | L'import riceve un 404 e il test di prototipo non parte |
| 4 | Divergenza calcolata dal report | sotto | Il frontend confronta i testi di detto e pensato |
| 5 | Fidelity score nel report | sotto | Compare "calibrazione non ancora disponibile" |
| 6 | Report del prototipo | TBD, da pensare insieme | Compare "non ancora disponibile" |
| 7 | Personas: attributi come campi, biografia, ripiego | [contratto-personas.md](contratto-personas.md) | Panel e risposte funzionano come oggi |

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

## Da decidere insieme

- **Report del prototipo** (punto 6). Lo pensiamo insieme quando decidiamo cosa misurare per ogni schermata.

Deciso: il segmento è il pubblico della pagina LinkedIn di Digitiamo, PMI e grandi aziende, come lo campiona già il pool. Il testo di Panel, README e scheda di contesto è aggiornato. Il campionamento resta com'è.

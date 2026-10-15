# Piano design e frontend

Area di Serena: `frontend/`, `design/`. Consegna: mercoledì 9 dicembre 2026, 8 mercoledì da 4 ore.

## Da decidere con Salvo (entro il 21 ottobre)

Gli schemi in `shared/schemas/` sono una bozza. Prima di costruirci sopra:

1. **Report del prototipo.** Lo schema copre solo il ranking dei post. Servono criticità e tasso di abbandono per schermata.
2. **Oggetto Test.** Manca: id, stato (`in_corso`, `completato`, `errore`), panel, stimoli.
3. **Panel.** Lista di personas o parametri di campionamento (dimensione, quote)?
4. **Endpoint.** Proposta minima, con polling perché un test può durare minuti:
   - `POST /tests` lancia un test
   - `GET /tests/{id}` stato
   - `GET /tests/{id}/report` risultato
   - `GET /personas` panel
   - `GET /flows` flussi del prototipo catturati
5. **Immagini dei post.** Upload multipart o URL?

## Le tre schermate

| Schermata | Post | Prototipo |
| --- | --- | --- |
| Panel | Personas: ruolo, settore, dimensione, regione. Sola lettura | Uguale |
| Test | 2–5 varianti, ognuna testo + immagine | Scelta tra i 2–3 flussi catturati |
| Report | Ranking, distribuzione per variante, obiezioni, citazioni | Screenshot per schermata con criticità e abbandono |

Il report mostra sempre che i risultati sono simulati e la distribuzione, non solo la media.

## Scelte tecniche

- CSS semplice con variabili (token del brand Digitiamo), nessuna libreria di componenti.
- Distribuzione con barre in CSS, nessuna libreria di grafici.
- Niente router: tre schermate.
- Mock basati sugli schemi finché gli endpoint non sono pronti.

## Calendario

| Data | Obiettivo |
| --- | --- |
| 21 ott | Schemi ed endpoint chiusi con Salvo. Wireframe low-fi delle 3 schermate in `design/` |
| 28 ott | UI kit minimo: colori, tipografia, bottone, card, barra di distribuzione. Revisione wireframe |
| 4 nov | Test post: form varianti testo + immagine, validazione 2–5, su mock |
| 11 nov | Report post: ranking, distribuzione, obiezioni, citazioni, avviso "simulato" |
| 18 nov | Panel e modalità prototipo in Test e Report |
| 25 nov | Integrazione con gli endpoint reali; stati di caricamento, errore e test lunghi |
| 2 dic | Prova completa con post Digitiamo già pubblicati, correzioni, accessibilità di base |
| 9 dic | Margine e demo |

**Rischio principale:** se il 25 novembre gli endpoint non sono pronti, la demo resta sui mock. Per questo il contratto si chiude il 21 ottobre.

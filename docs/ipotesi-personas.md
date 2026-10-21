# Ipotesi e punti aperti sul pool di personas

Il pool (`data/processed/personas.json`) si genera con `python -m scripts.generate_personas`
(da `backend/`) a partire da `data/processed/linkedin_audience.json`, cioè dagli export Analytics
della pagina LinkedIn: follower e visitatori, pesati allo stesso modo.

## Ipotesi, non dati (da sostituire)

- **Atteggiamento verso l'AI e uso di LinkedIn.** L'export non li contiene. Le distribuzioni sono
  dichiarate a mano in `HYPOTHESES` (`backend/app/personas/audience.py`) per evitare personas tutte
  uguali. Solo un'indicazione: i commenti mediani sono 0, quindi prevalgono i lettori passivi.
  **Da sostituire con dati reali** (sondaggio, CRM) appena ci sono.
- **Nessuna distribuzione congiunta.** LinkedIn dà una distribuzione per attributo: seniority,
  dimensione, funzione, settore e regione sono accoppiati a caso. Una sola regola di coerenza:
  titolari e soci non guidano grandi aziende.
- **Dimensione aziendale.** Soglie europee; il bucket 201-500 sta a cavallo di 250 e va in "grande".
- **Solo Italia.** Le località estere (circa 15% del pubblico) sono escluse.
- **Descrizioni.** Le scrive `PERSONA_MODEL`: con i modelli gratuiti restano refusi occasionali.

## Da decidere con Fabio

- Il README parla di "decision maker di PMI"; il pubblico reale è per il 40% in grandi aziende e per
  il 73% senza ruolo di responsabilità. Il pool riproduce il pubblico, non il segmento del README.
- Aggiunto `grande` a `company_size` in `shared/schemas/persona.schema.json` (contratto condiviso).
- Fidelity score nel report (PR #6): serve un campo nello schema, da decidere insieme.

## Non verificato

- Il report con `google/gemma-4-31b-it:free` (limitato dal provider). Il confronto tra modelli ha
  prodotto dati solo per Minimax: gli altri sono bloccati da limite giornaliero o policy dei dati.
- Il pool non è stato confrontato con l'engagement reale (prova di valore, A6): servono testo e
  immagine dei post pubblicati, l'export ha solo titolo e link.

# Prompt: wireframe e tre direzioni grafiche di eco

Da incollare in una sessione di design (Claude Code con una skill di design, Claude Design o simili) aperta su questo repo.

---

Stai progettando **eco**, una piattaforma interna di Digitiamo. Leggi prima `README.md`, `CLAUDE.md`, `docs/piano-frontend.md` e il wireframe low-fi in `design/wireframes.html`, che è il punto di partenza.

## Cosa fa la piattaforma

eco fa valutare contenuti a un panel di **personas sintetiche**, cioè profili di decision maker di PMI italiane costruiti su dati reali (ISTAT, CRM anonimizzato, analytics LinkedIn). Lo scopo è capire come reagirà il pubblico prima di pubblicare un contenuto o rilasciare un prototipo. Le reazioni sono simulate e servono a confrontare alternative, non a prevedere numeri.

Ha due casi d'uso:

1. **Pre-test di post LinkedIn:** l'utente carica da 2 a 5 varianti di un post (testo più immagine facoltativa). Ottiene il ranking delle varianti, la distribuzione dei voti, le obiezioni principali e le citazioni delle personas.
2. **Test di prototipo:** l'utente sceglie uno dei 2–3 flussi già catturati in automatico, cioè sequenze di screenshot. Ottiene, per ogni schermata, le criticità, i passaggi fraintesi e la percentuale di abbandono.

## Le schermate

**1. Panel.** Mostra chi compone il panel: 30 personas con ruolo, settore, dimensione aziendale, regione e una riga di profilo. In alto c'è la composizione del panel (quote per dimensione, area e settore).

**2. Test.** Ha due modalità, Post e Prototipo.
- Post: un editor per 2–5 varianti, ognuna con testo e immagine, più "Aggiungi variante". Il pulsante "Avvia test con 30 personas" riporta la durata stimata.
- Prototipo: la scelta tra i flussi catturati, ognuno con nome, numero di schermate e data di cattura.
- Test in corso: l'avanzamento ("56 risposte su 90"), la nota che si può chiudere la pagina e gli stati di errore e di nuovo tentativo.

**3. Report.**
- Post: la sintesi in una frase, poi le varianti in ordine di ranking. Ogni variante mostra la **distribuzione dei voti da 1 a 5 accanto alla media, mai la media da sola**, le obiezioni con la loro frequenza, la sintesi di "Cosa dicono" e quella di "Cosa pensano". Chiude la tabella delle risposte: persona, voto, cosa ha detto, cosa ha pensato. Si può filtrare per le risposte in cui detto e pensato divergono.
- Prototipo: una fila di screenshot del flusso con l'abbandono di ogni schermata, e il punto critico in evidenza. Il dettaglio della schermata riporta criticità, passaggi fraintesi e cosa dicono e pensano le personas.
- Sempre visibile: l'avviso "Risultati simulati. Reazioni di personas sintetiche, non di persone reali."
- Sempre visibile: il **fidelity score**, cioè quanto il ranking del panel ha rispecchiato l'engagement reale sui post già pubblicati. Quando manca, il report lo dichiara esplicitamente ("Calibrazione non ancora disponibile").

**Proposta da esplorare: generare personas sulle proprie esigenze.** Oggi il panel è fisso. Disegna, come variante separata della schermata Panel e con l'etichetta "proposta", un flusso in cui l'utente descrive il pubblico che gli serve, per esempio "CFO di aziende manifatturiere lombarde da 20 a 100 dipendenti". La descrizione non genera personas inventate: diventa un insieme di filtri (settore, dimensione, area, ruolo) che l'utente vede e corregge, e il panel si campiona dai dati reali con quei filtri. Prima di confermare l'utente vede l'anteprima del panel campionato, con le quote e alcune personas di esempio, e quanto quel pubblico è coperto dai dati reali. Il resto della piattaforma non deve dipendere da questa proposta.

## Il concetto chiave da rendere visibile

Ogni risposta ha due livelli: **cosa la persona dice in pubblico** e **cosa pensa davvero**. È il valore distintivo della piattaforma, e il design deve far leggere la differenza tra i due livelli a colpo d'occhio, senza spiegazioni.

## Cosa consegnare

1. **Wireframe aggiornato** in `design/wireframes.html`: stessa struttura di oggi, più la variante Panel con la proposta di generazione.
2. **Tre direzioni grafiche** in `design/direzioni/a.html`, `b.html` e `c.html`. Ognuna mostra il **Report post** (la schermata più densa) e il **Test post**, con gli **stessi contenuti e gli stessi dati** perché il confronto sia sulla grafica e non sul testo. Usa i dati di `frontend/src/mocks/index.ts`.
   - **A, Editoriale:** il report come un documento da leggere. Tipografia protagonista, molto bianco, colore usato solo per i dati.
   - **B, Strumento di analisi:** il report come un pannello di lavoro. Più denso, griglia stretta, tabelle e filtri in primo piano, numeri allineati.
   - **C, Brand Digitiamo:** palette viola e blu del brand book, Montserrat e Poppins, tono caldo e riconoscibile come prodotto Digitiamo.
3. Una **pagina di confronto** (`design/direzioni/index.html`) che mette le tre direzioni affiancate. Per ognuna indica in due righe per chi funziona meglio e il rischio principale.

## Vincoli

- Testi della UI in italiano.
- Desktop prima di tutto, ma nessuna rottura a 375 px.
- Contrasto AA, distribuzioni leggibili anche senza colore.
- Niente librerie di componenti né di grafici: le barre della distribuzione sono in CSS, come nel frontend.
- I colori vanno definiti come variabili CSS, così la direzione scelta passa in `frontend/src/styles/tokens.css` senza riscrivere nulla.

# Brief: design system di eco (direzione A, "Candy")

Da incollare in Claude Design, allegando questi file:

1. `design/direzioni/a-roulette-candy.html`, la tavola scelta: è la fonte di verità per valori e componenti.
2. `design/direzioni/a-roulette-candy-1440.png` e `a-roulette-candy-375.png`, le catture a desktop e telefono.
3. `design/assets/logo-digitiamo-blue.svg` e `logo-digitiamo-white.svg`, il logo ufficiale.

---

## Cosa costruire

Un design system per **eco**, la piattaforma interna di Digitiamo che fa valutare i post LinkedIn a un panel di personas sintetiche, cioè decision maker di PMI italiane. Il punto di partenza è la tavola allegata, già scelta. Non va reinventata: va resa sistematica, estesa agli stati che mancano e documentata.

Deve contenere tre cose:
- **Token:** colori, tipografia, raggi, ombre e spaziature, con nomi e valori. Saranno copiati in `frontend/src/styles/tokens.css` come variabili CSS.
- **Componenti:** ognuno con le sue varianti, i suoi stati e quando usarlo.
- **Le tre schermate (Panel, Test, Report)** ricomposte con i componenti, compresi gli stati di caricamento, errore e vuoto.

Vincoli del frontend:
- Il frontend è React, scritto in CSS semplice con variabili.
- **Niente librerie di componenti né di grafici:** le barre della distribuzione sono in CSS.
- Tutti i testi dell'interfaccia sono in italiano.

## Il carattere

Lo stile è "Friendly Geometric Candy": forme tonde, colori pieni e oggetti che sembrano premibili. È un'interpretazione calda del brand Digitiamo, il cui tono è "caldo e informale, senza essere ironico", per uno strumento interno che il team deve usare volentieri.

Il rischio da evitare è che diventi infantile. I dati vengono prima della decorazione. **Niente mascotte, niente emoji come icone, niente gradienti.**

## Token (valori già usati nella tavola)

### Colore

| Token | Valore | Ruolo |
|---|---|---|
| `--ink` | #070011 | Testo principale (Brand Book 30) |
| `--night` | #1C073A | Titoli (Brand Book 50) |
| `--violet` | #3E00EA | Colore del logo: azioni, detto, vincitore (Brand Book 70) |
| `--peri` | #717FFE | Barre secondarie, focus (Brand Book 80) |
| `--lilac` | #EBEEFC | Superfici tenui, pensato (Brand Book 90) |
| `--mist` | #F4F5FA | Sfondo pagina, campi (Brand Book 95) |
| `--white` | #FFFFFF | Card |
| `--violet-press` | #2700A3 | Ombra piena sotto gli elementi viola |
| `--line` | #DCE0F8 | Bordi |
| `--line-press` | #C9CEF3 | Ombra piena sotto gli elementi chiari |
| `--muted` | #514A66 | Testo secondario (contrasto 8:1 su bianco) |
| `--warm` | #FF7A3D | Accento caldo, solo per segnali piccoli |
| `--warm-soft` | #FFEBDF | Fondo del pensato quando diverge e delle obiezioni |
| `--warm-ink` | #A3360A | Testo caldo (contrasto 5,6:1 su `--warm-soft`) |
| `--warm-press` | #E25A1C | Ombra piena sotto gli elementi caldi |

**La regola del caldo:** l'arancio è riservato a **ciò che non si dice**, cioè il pensato che diverge dal detto e le obiezioni. Non va mai usato per azioni o decorazioni.

### Tipografia

- **Titoli:** Baloo 2, pesi 600, 700 e 800.
- **Testo:** Nunito, pesi 500–800, con il corsivo 600 per il pensato.
- **Scala usata nella tavola:** 72 (media), 48 (h1), 30–32 (h2 e sintesi), 24, 22, 20, 18, 16 (corpo), 15, 14, 13 e 12 (etichette in maiuscolo con spaziatura 0,06–0,08em).
- **Minimi:** 14px per il testo, 12px per le etichette.

**Da decidere:** il Brand Book prescrive Montserrat e Poppins. La tavola A usa due font tondi per coerenza con lo stile. Proponi quale delle due coppie tenere e mostra il confronto.

### Forma e rilievo

- **Raggi:** 32 (schermata), 24 (card), 20 (blocchi interni), 16 (pulsanti e campi), 14 (tab, chip, voto), 999 (pill).
- **Rilievo candy:** un'ombra piena verso il basso, senza sfocatura: `0 4px 0 <colore-press>`. Vale 3px per gli elementi piccoli e 6px per quelli grandi.
- **Pressione:** al click l'elemento scende della stessa altezza e l'ombra si azzera (`translateY(4px)`, `box-shadow: 0 0 0`), in 80ms.
- **Bordi:** 2px pieni. Tratteggiati solo per due cose: ciò che è vuoto o da aggiungere, e lo stato "non disponibile".
- **Spaziature:** sono già sulla scala 4/8: 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 48. Normalizzale in una scala a passi.

## Componenti presenti nella tavola

1. **Pulsante:** primario viola, chiaro e grande ("Avvia test"). Tutti in rilievo e premibili, con il focus visibile tramite un contorno `--peri` da 3px.
2. **Tab di navigazione:** Panel, Test, Report. La tab attiva è in rilievo su `--lilac`.
3. **Selettore a segmenti:** "Post LinkedIn" o "Prototipo".
4. **Card:** standard, vincitrice (bordo e ombra viola) e tratteggiata per "aggiungi".
5. **Variante:** la lettera in un cerchio, il campo testo e lo spazio per l'immagine nel formato LinkedIn 1,91:1.
6. **Contatore a slot:** 5 pallini, pieni quelli usati ("2 di 5").
7. **Panel a pallini:** 30 punti, uno per persona.
8. **Avviso "Risultati simulati"** e **stato del fidelity score** (tratteggiato, con anello puntinato), sempre visibili nel report.
9. **Medaglia di ranking:** #1 viola, #2 lilla.
10. **Blocco punteggio:** la media in grande più la distribuzione 1–5 in barre CSS, con i conteggi scritti sopra. **La distribuzione sta sempre accanto alla media, mai la media da sola.** Per la barra vuota si usa un trattino.
11. **Obiezione:** una pill calda con l'etichetta "Obiezione".
12. **Detto e pensato, il componente firma:**
    - **Detto:** fumetto viola pieno con la coda in basso a sinistra. È la voce pubblica.
    - **Pensato:** nuvoletta lilla in corsivo, con la scia di due bolle. È il pensiero privato.
    - **Pensato che diverge:** la nuvoletta diventa `--warm-soft`, si scosta di 6px, ruota di -0,8° e mostra il tag "Diverge".
    - **Detto vuoto:** fumetto tratteggiato con "non commenterebbe". È un dato, non un errore.
13. **Chip filtro:** Tutte, Solo dove divergono (con un pallino caldo), Per voto.
14. **Riga risposta:** avatar con codice persona, ruolo e descrittori, voto in un riquadro (in rilievo viola se vale 4 o più), detto e pensato.
15. **Etichetta di cornice ed eyebrow:** maiuscolo da 12–13px, `--muted`.

## Da progettare (non c'è nella tavola)

- **Panel:** la composizione del panel (quote per dimensione, area e settore) e la lista delle 30 personas, in sola lettura.
- **Test in corso:** l'avanzamento ("56 risposte su 90"), la nota che si può chiudere la pagina, le risposte non valide ritentate, l'errore con il pulsante "Riprova" e l'errore 409 "Un test è già in corso".
- **Test prototipo:** la scelta tra 2 e 3 flussi catturati, ognuno con nome, numero di schermate e data.
- **Report prototipo:** una fila di screenshot con l'abbandono per schermata, il punto critico in evidenza, e nel dettaglio della schermata criticità e passaggi fraintesi con il detto e il pensato.
- **Stati generali:** caricamento (skeleton), vuoto (nessun test ancora), errore di rete, campo non valido (meno di 2 varianti o testo mancante).
- **Fidelity score disponibile:** lo stato con il numero, accanto a quello "non disponibile" già disegnato.
- **Tema scuro:** decidi se serve. È uno strumento interno: va bene anche solo chiaro, ma la scelta va dichiarata.

## Regole che il sistema deve far rispettare

- I risultati sono **simulati** e il report lo dice sempre.
- La distribuzione accompagna sempre la media.
- Con poche risposte niente percentuali: si scrivono i conteggi ("3 risposte").
- Accessibilità: contrasto AA, distribuzioni leggibili anche senza colore (i conteggi sono scritti), focus visibile, `prefers-reduced-motion` che disattiva la pressione animata.
- A 375px non c'è scorrimento orizzontale. La tabella delle risposte diventa una lista di schede.

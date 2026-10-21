# Spec comune: tre direzioni grafiche di eco

Input unico per le tre direzioni. Ogni direzione lavora solo da qui, senza guardare le altre.

## Il prodotto

eco è una piattaforma interna di Digitiamo, società italiana (Milano e Varese) che porta l'AI nelle aziende. Un panel di **personas sintetiche**, cioè decision maker di PMI italiane campionati da dati reali (ISTAT, CRM anonimizzato, analytics LinkedIn), valuta i contenuti prima della pubblicazione. Il caso d'uso principale è confrontare da 2 a 5 varianti di un post LinkedIn e capire quale funziona e perché.

I risultati sono **simulati**: servono a confrontare varianti, non a prevedere numeri. L'interfaccia deve renderlo chiaro senza sembrare un disclaimer legale.

## Chi la usa e dove

- **Chi:** il marketing e i fondatori di Digitiamo, persone con competenze digitali ma non data scientist. Usano eco poche volte a settimana, prima di pubblicare.
- **Dove:** laptop, a circa 1 m di distanza. Si progetta a 1440×900, ma niente si deve rompere a 375 px.
- **Cosa cercano in 5 secondi:** quale variante vince, di quanto vince, e il motivo principale.

## Il concetto distintivo: "detto" e "pensato"

Ogni risposta ha due livelli: cosa la persona **dice** in pubblico (un commento su LinkedIn) e cosa **pensa** davvero, in privato. Spesso coincidono. Quando divergono, il dato è prezioso: per esempio dice «Esempio chiaro, complimenti.» e pensa «Mi piace, ma se costa come l'ultimo consulente lascio stare.».

Il design deve far leggere questa differenza a colpo d'occhio, senza spiegazioni. Un "detto" vuoto significa "non commenterebbe" ed è un dato, non un campo mancante. È il motivo visivo che nessun altro prodotto ha: costruiscici sopra.

## Schermate da produrre

Un solo file HTML per direzione, con le due schermate una sotto l'altra. Ogni schermata è un riquadro applicativo largo 1440 px, con sopra un'etichetta piccola ("Test · post", "Report · post"). Navigazione dell'app: Panel · Test · Report, più il logo Digitiamo e il nome "eco".

### 1. Test · post (creazione del test)

- Titolo: "Nuovo test". Sottotitolo: "Confronta da 2 a 5 varianti dello stesso post".
- Scelta della modalità: **Post LinkedIn** (attiva) e Prototipo.
- Due varianti compilate, ognuna con un'area di testo e uno spazio per l'immagine. L'immagine è un placeholder onesto: un riquadro con l'etichetta "Immagine del post · trascina o scegli un file".
  - **Variante A:** «La trasformazione digitale non è più un'opzione. Le PMI che adottano l'intelligenza artificiale oggi saranno le leader di domani. Sei pronto a fare il salto? #AI #PMI #Innovazione»
  - **Variante B:** «Un'azienda di valvole di Legnano passava 6 ore a settimana a compilare offerte a mano. Con un agente AI addestrato sui suoi listini ora ne bastano 40 minuti. Nessuna rivoluzione: un processo noioso, tolto di mezzo. Qual è il vostro?»
- "+ Aggiungi variante", con il contatore "2 di 5".
- Azione principale: "Avvia test con 30 personas", con sotto "circa 3 minuti". Accanto, un riassunto del panel: "Decision maker di PMI italiane · 30 personas".

### 2. Report · post (la schermata più importante)

Usa **esattamente** questi dati di prova, senza inventare numeri:

- Avviso sempre visibile: "Risultati simulati. Reazioni di personas sintetiche, non di persone reali. Usali per confrontare varianti, non come previsione."
- Calibrazione sempre visibile: "Fidelity score: calibrazione non ancora disponibile". Serve uno stato dichiarato, non un numero inventato.
- Sintesi: "La variante B convince per concretezza; la A è percepita come troppo generica."
- **#1 Variante B**, media 3,7. Distribuzione dei voti 1–5: 0, 1, 0, 1, 1. Obiezione: "Non dice quanto costa". Cosa dicono: "Lo trovano utile e concreto, qualcuno lo girerebbe al team." Cosa pensano: "Si fidano, ma pensano al costo senza dirlo."
- **#2 Variante A**, media 2,3. Distribuzione: 0, 2, 1, 0, 0. Obiezione: "Troppo generico". Cosa dicono: "Apprezzano il tema e lo definiscono interessante." Cosa pensano: "In privato lo trovano vago: manca un esempio concreto."
- Tabella delle risposte (persona · voto · ha detto · ha pensato), con le personas:
  - p1: Titolare · Manifattura · piccola · Lombardia
  - p2: Direttrice commerciale · Servizi B2B · media · Emilia-Romagna
  - p3: Amministratore · Commercio · micro · Puglia
- Risposte alla variante B:
  - p1, voto 4. Detto: «Esempio chiaro, complimenti.» Pensato: «Mi piace, ma se costa come l'ultimo consulente lascio stare.» **Diverge.**
  - p2, voto 5. Detto: «Lo giro al team.» Pensato: «Finalmente numeri veri. Lo giro al team.»
  - p3, voto 2. Detto: vuoto, cioè non commenterebbe. Pensato: «Roba per aziende più grandi della mia.»
- Risposte alla variante A:
  - p1, voto 2. Detto: «Spunto interessante, grazie.» Pensato: «Bello, ma a me cosa cambia? Non ho tempo.» **Diverge.**
  - p2, voto 3. Detto: «Tema importante.» Pensato: «Il solito post sulla trasformazione digitale.» **Diverge.**
  - p3, voto 2. Detto: vuoto. Pensato: «Non ho capito cosa vendono.»
- Filtro della tabella: Tutte · Solo dove detto e pensato divergono · Per voto.
- Regola: **la distribuzione sta sempre accanto alla media, mai la media da sola**. Il panel ha solo 3 risposte per variante: mostralo con onestà ("3 risposte"), senza trasformarlo in percentuali che sembrano statistiche.

## Brand

Digitiamo ha un brand reale, e le tre direzioni partono dagli stessi asset. La differenza sta nell'interpretazione.

- **Logo** (SVG da incorporare inline, mai riprodotto a mano):
  - `/Users/fabiopia/.claude/skills/synced/1ce1c576-15b4-4013-baca-aa0d480a6e4b_5dbc73e5-425a-4ff5-89a3-36020be041df/pitch/assets/logo-blue.svg`
  - `.../pitch/assets/logo-white.svg`, nella stessa cartella, per i fondi scuri
- **Palette del Brand Book:** #070011 (30), #1C073A (50), #3E00EA (70, il colore del logo), #717FFE (80), #EBEEFC (90), #F4F5FA (95).
- **Font del Brand Book:** Montserrat Bold per i titoli, Poppins per il testo (Google Fonts). Una direzione può sostituirli, ma deve spiegare perché.
- **Tono:** caldo e informale senza essere ironico, concreto, orientato al valore.
- Il viola del logo è del brand: è lecito. Restano vietati i gradienti viola generici, le emoji come icone e le card con bordo sinistro colorato.

## Vincoli

- Un solo file HTML con CSS inline e font da Google Fonts. Niente framework, librerie di componenti o librerie di grafici: le barre della distribuzione sono in CSS.
- Colori definiti come variabili CSS su `:root`, così la direzione scelta passa in `frontend/src/styles/tokens.css`.
- Testo ≥ 14 px, etichette ≥ 12 px, contrasto almeno AA. La distribuzione si deve leggere anche senza colore, per esempio con i valori scritti o con le altezze.
- Tutti i testi in italiano.
- Nessun dato inventato oltre a quelli qui sopra. Niente statistiche decorative.

## Il motivo visivo da cercare

Il prodotto è fatto di **due voci per ogni persona**, quella pubblica e quella privata. È un motivo che appartiene solo a eco: un fuori e un dentro, una superficie e un sottotesto. Ogni direzione deve trovare la propria forma per questo doppio livello, e dire in una riga da dove l'ha presa.

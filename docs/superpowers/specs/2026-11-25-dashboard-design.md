# Dashboard dei test e report per test

Per: Fabio e Salvo · 25 novembre 2026 · Stato: approvato da Fabio, da implementare prima della demo del 9 dicembre

## Perché

Oggi eco ha tre tab: Panel, Test e Report. Il report mostra l'ultimo test finito e non c'è modo di rivedere quelli passati. Inoltre la sintesi del report sta in memoria, quindi dopo un riavvio si rigenera, in 2–3 minuti con Ollama.

L'obiettivo è una home che fa da dashboard dei test fatti, da cui se ne lancia uno nuovo. Ogni test ha il suo report, salvato.

## Decisioni

- **Niente Supabase per ora.** Ognuno usa eco sul suo Mac: Salvo fa la demo dal suo, Fabio fa le prove sul proprio. SQLite (`eco.sqlite`) conserva già test, risposte e prototipi.
- **Account: solo un nome locale.** Si chiede al primo avvio e si salva con il test, senza password. Il login vero e il database condiviso (Supabase) sono un progetto separato, dopo la demo.
- **Dalla dashboard un test si può solo aprire.** Niente duplica e niente elimina.
- **Cambia una regola di CLAUDE.md.** Le schermate non sono più «Panel, Test, Report» ma Dashboard, Panel e la pagina del test, con il report dentro. CLAUDE.md va aggiornato insieme al codice.

## Pagine e navigazione

Indirizzi con `#`, gestiti a mano in `frontend/src/lib/route.ts`, senza dipendenze. Il tasto Indietro funziona e ogni test ha un suo link.

| Indirizzo | Pagina | Contenuto |
| --- | --- | --- |
| `#/` | Dashboard | Titolo, pulsante «Nuovo test», elenco dei test dal più recente |
| `#/panel` | Panel | La schermata di oggi, in sola lettura |
| `#/test/nuovo` | Nuovo test | Il modulo di oggi per post e prototipo. All'avvio porta a `#/test/<id>` |
| `#/test/<id>` | Il test | In corso: avanzamento e risposte live. Completato: il report. In errore: il messaggio e le risposte arrivate prima dell'errore |

Un indirizzo sconosciuto porta alla dashboard.

**Sidebar:**
- il logo in alto;
- due voci, Dashboard e Panel;
- in fondo il nome locale, con «Cambia».

La tab Report sparisce. Su schermi stretti, sotto i 760 px, la sidebar diventa una barra in alto.

**Righe della dashboard:**
- tipo (post o prototipo) con l'icona;
- `title`;
- numero di varianti o di schermate;
- data, nel formato «25 nov, 14:32»;
- `created_by`;
- stato: «In corso · 40%», «Completato» o «Interrotto».

L'intera riga è un link a `#/test/<id>`.

**Stati della dashboard:**
- in caricamento, uno skeleton;
- se il caricamento fallisce, un avviso con «Riprova»;
- senza test, il messaggio «Nessun test ancora» con «Nuovo test».

Se c'è un test in corso, «Nuovo test» resta attivo: il backend accetta un solo test alla volta e il modulo mostra già l'errore che rimanda. Per i test salvati prima di questa modifica, senza `title`, la riga mostra «Senza titolo».

**Primo avvio:** prima di tutto compare una finestra «Come ti chiami?». Il nome si salva in `localStorage` (chiave `eco.name`) e si cambia dalla sidebar. Se `localStorage` non è disponibile, il nome vale per la sessione.

## Backend

**Report salvati**
- Nuova tabella `reports (test_id TEXT PRIMARY KEY, report TEXT NOT NULL, created_at TEXT NOT NULL)` in `app/store.py`.
- A fine test (`prepare_report`) il report generato si scrive in tabella.
- `GET /tests/{id}/report` legge prima la tabella. Se il report manca, lo genera, lo salva e lo restituisce. La cache in memoria `_REPORTS` resta solo per non generare due volte lo stesso report su richieste simultanee.
- `fidelity` non si salva. Si aggiunge a ogni lettura con `load_fidelity()` per i post, così i report vecchi mostrano la calibrazione appena esiste `calibration.json`.
- Se la generazione fallisce, non si salva niente e la richiesta dopo riprova, come oggi.

**`test.schema.json`**, due campi facoltativi da segnalare a Salvo:
- `created_by` (string, max 60): arriva in `POST /tests` come campo JSON o come campo del form. Il backend toglie gli spazi; se è vuoto lo omette.
- `title` (string, max 80): lo calcola il backend alla creazione. Per un prototipo è il suo nome; per un post è la prima riga del testo della prima variante, tagliata a 80 caratteri con «…».

I tipi del frontend si rigenerano con `npm run gen:types`. Gli endpoint esistenti non cambiano.

## Frontend

**Design system:**
- `Sidebar` (`ds/components/navigation/Sidebar.tsx`), al posto di `AppNav`, che resta esportato finché non si toglie;
- `TestRow` (`ds/components/test/TestRow.tsx`), la riga della dashboard;
- tutti e due usano i token esistenti.

**Schermate:**
- `DashboardScreen` (nuova): legge `getTests()`.
- `NewTestScreen`: è il modulo di `TestScreen` di oggi. Quando un test parte, porta a `#/test/<id>`.
- `TestPage` (nuova): legge `getTest(id)` e lo aggiorna come fa oggi `TestScreen`. Finché il test è in corso mostra `TestProgress` e `LiveResults`; quando è completato mostra il report. Avanzamento e risposte live si spostano qui da `TestScreen`.
- `ReportScreen`: riceve il test già caricato invece di cercarlo in `getTests()`, e perde l'EmptyState «Nessun test ancora».
- `App`: sceglie la pagina in base a `useRoute()`.

**Mock:** `getTests` e `getTest` ci sono già. Nuovi `title` e `created_by` nei test finti, e nella dashboard dei mock un paio di test già finiti, così la si vede piena senza lanciare niente.

## Test

- **Backend:**
  - il report si salva a fine test e si rilegge dalla tabella dopo aver svuotato la cache in memoria;
  - `fidelity` aggiornata su un report salvato;
  - `title` per post e prototipo, con il taglio a 80 caratteri;
  - `created_by` vuoto omesso.
- **Frontend:**
  - `route.ts`: indirizzi validi, sconosciuti e `#/test/<id>`;
  - titolo di riserva «Senza titolo»;
  - formato della data.
- **A vista:** dashboard piena e vuota, nuovo test fino al report, ricarica su `#/test/<id>`, tasto Indietro, larghezza da telefono. Gli screenshot vanno a Fabio per l'approvazione prima di aprire la PR.

## Fuori da questo progetto

- Login vero, database condiviso e Supabase: dopo la demo.
- Modifica del panel.
- Duplicare o eliminare un test.
- Riepilogo del risultato nelle righe della dashboard.

# Contratto: come costruiamo le personas

Per: Salvo · 10 novembre 2026 · Si collega a [contratti-backend.md](contratti-backend.md)

La pipeline attuale è già quella giusta. Gli attributi si campionano dall'audience LinkedIn con seed fisso e vincoli di coerenza (`personas/sampler.py`); il modello scrive solo la biografia (`prompts/persona_profile.md`). Questo contratto aggiunge poche cose, alcune prese da MiroFish e alcune richieste dal CLAUDE.md.

## Cosa abbiamo guardato in MiroFish

Il progetto è [666ghj/MiroFish](https://github.com/666ghj/MiroFish), con licenza **AGPL-3.0**. Copiarne il codice ci obbligherebbe a rilasciare eco con la stessa licenza: prendiamo solo le idee.

- **Come costruisce le persona:** estrae entità (persone, organizzazioni) da documenti seed con un grafo GraphRAG su Zep. Per ogni entità un LLM scrive un profilo lungo, circa 2000 caratteri, con MBTI, posizioni e memoria. Età, genere e contatori (follower, karma) sono inventati dall'LLM o con `random`, senza seed.
- **Cosa ne prendiamo:**
  - attributi strutturati e testo separati;
  - nel profilo, le sezioni su cosa convince, cosa irrita e come parla la persona;
  - un ripiego deterministico quando l'LLM fallisce.
- **Cosa non ne prendiamo:**
  - il grafo e la simulazione social, perché noi testiamo stimoli indipendenti;
  - gli attributi inventati e i numeri casuali, perché violano il principio 1;
  - i profili lunghi, perché costano e rendono le voci tutte uguali.

## 1. Attributi della persona come campi, non solo come testo

Oggi `ai_attitude` e `linkedin_use` vengono campionati ma finiscono solo dentro `profile`. Diventano campi di `persona.schema.json`, già aggiornato, con chiavi brevi:

| Campo | Valori | Origine |
| --- | --- | --- |
| `ai_attitude` | `entusiasta` · `curiosa` · `pragmatica` · `scettica` · `indifferente` | La prima parola delle chiavi di `HYPOTHESES["ai_attitude"]` |
| `linkedin_use` | `legge` · `ogni_tanto` · `partecipa` · `solo_contatti` | Le 4 chiavi di `HYPOTHESES["linkedin_use"]`, nello stesso ordine |

- **A cosa servono:** il Panel ne mostra le quote. Il report potrà dire chi ha reagito e chi ha scorso oltre, per uso di LinkedIn. Il prompt di risposta può usarli direttamente, oltre che attraverso la biografia.
- **`linkedin_use` resta centrale.** È l'attributo che pesa di più sull'azione nel feed (`action` del contratto sul post singolo): chi legge in silenzio di solito scorre oltre. Il prompt di risposta deve tenerne conto.
- Restano **ipotesi dichiarate** (`docs/ipotesi-personas.md`) finché non ci sono dati reali.
- Nello schema sono facoltativi per non rompere il pool attuale. Il backend deve sempre compilarli.

## 2. Biografia un po' più utile, sempre corta

`prompts/persona_profile.md` passa da 2–3 frasi a **3–4 frasi**, con due punti in più presi da MiroFish:

- **Cosa la convince e cosa la irrita** in un contenuto di lavoro, per esempio numeri concreti, promesse generiche o post autocelebrativi. Va scritto in modo coerente con `ai_attitude` e con il ruolo.
- **Come parla**: tono e lunghezza tipici di un suo commento. Serve a rendere diverso il "detto" tra una persona e l'altra.

Le regole di oggi non cambiano: niente nomi, niente Digitiamo, dettagli concreti.

## 3. Ripiego deterministico

Se l'LLM fallisce anche il retry, il pool deve comunque completarsi. Si usa un profilo da template costruito solo dagli attributi campionati, e va segnalato nel log. Non si inventano attributi e non si salta la persona: altrimenti le quote non tornano.

## 4. Ancoraggio a citazioni reali: da decidere

Il principio 1 del CLAUDE.md chiede biografie "ancorate a citazioni reali da `data/processed/`". Oggi non succede, perché non abbiamo ancora note CRM anonimizzate. **Salvo:** ci sono dati utilizzabili? Se non ci sono, aggiorniamo il principio prima della consegna e lo diciamo nel report.

## Cosa non cambia

- Il seed è fisso e le quote sono rispettate.
- C'è una sola regola di coerenza: titolari e soci non guidano una grande azienda.
- Le personas non conoscono il test.
- Il pool si rigenera con `scripts.generate_personas` e si serve con `PERSONAS_PATH`.

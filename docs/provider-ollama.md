# Provider AI: Ollama in locale

Aggiornato al 17 novembre 2026. Sostituisce OpenRouter per la POC.

## Perché

- I modelli `:free` di OpenRouter non reggono il panel. `minimax/minimax-m3.1-flash:free` è stato ritirato il 22 ottobre (risponde 404). Su 6 modelli gratuiti con immagini, 2 rispondono in 46–178 s, 2 sono limitati a monte (429) e 2 sono bloccati dalle impostazioni privacy dell'account. Il free tier ha circa 50 richieste al giorno, mentre un test con 2 varianti ne fa 60.
- Decisione: solo strumenti gratuiti. Ollama gira sul Mac, senza limiti di richieste e senza che i dati escano dal computer, prototipi riservati compresi.

Il client non cambia: Ollama espone `/v1/chat/completions` compatibile OpenAI, con `response_format` json_schema e immagini. Si cambiano solo le variabili d'ambiente. Per tornare a OpenRouter basta rimettere le variabili di prima.

## Installazione (una volta)

```bash
brew install ollama
brew services start ollama
ollama pull gemma3:12b
ollama create eco-gemma3-12b -f backend/ollama/Modelfile
```

`eco-gemma3-12b` è `gemma3:12b` con il contesto a 16k token. Il default di Ollama (4096) taglia in silenzio il prompt del report quando le risposte sono 30.

## Variabili in `backend/.env`

```
RESPONDER=llm
SUMMARIZER=llm
OPENROUTER_BASE_URL=http://localhost:11434/v1
OPENROUTER_API_KEY=ollama
PERSONA_MODEL=eco-gemma3-12b
REPORT_MODEL=eco-gemma3-12b
LLM_TIMEOUT_SECONDS=300
PANEL_CONCURRENCY=2
```

- `OPENROUTER_API_KEY` serve solo alla validazione all'avvio: Ollama ignora la chiave.
- Ollama esegue una richiesta alla volta. Più concorrenza non accelera, allunga solo l'attesa in coda, e una richiesta in coda può superare il timeout. Per questo concorrenza 2 e timeout 300 s.
- `.claude/launch.json` (locale, non versionato) passa le stesse variabili al backend avviato dall'app.

## Prestazioni misurate (M1 Pro, 16 GB)

| Cosa | Tempo |
| --- | --- |
| Una risposta persona (post) | circa 21 s, la prima 45–50 s per il caricamento del modello |
| Una risposta persona (schermata con immagine) | circa 27 s |
| Test con 2 varianti × 30 personas | 21 minuti (misurato), più 2 minuti per il report |
| Calibrazione su 15 post × 30 personas | circa 2 ore e mezza, da lanciare quando il Mac non serve |

## Limiti noti

- **Allegati PDF:** il blocco `file` di OpenRouter non è supportato da Ollama. Un post con PDF fallisce; le immagini funzionano.
- **Qualità, prova reale del 17 novembre** (30 personas: caso cliente concreto contro post generico sulla digitalizzazione): ranking corretto (2,73 contro 1,60), riassunti coerenti con le risposte e che dichiarano la simulazione. Da sistemare nei prompt e nel report:
  - `action`: 23 commenti su 30 e nessuna reazione. Su LinkedIn commentare è raro, quindi il prompt va ricalibrato.
  - Divergenza: 30 su 30, perché la regola confronta i testi e detto e pensato non coincidono mai alla lettera. Non distingue nessuno.
  - Obiezioni quasi uguali contate come diverse («Troppo generico.» e «Troppo generico»).
- **Il Mac deve restare acceso** durante test e calibrazione.

# Provider AI: Ollama in locale

Aggiornato al 18 novembre 2026. Sostituisce OpenRouter per la POC.

## Perché

- I modelli `:free` di OpenRouter non reggono il panel. `minimax/minimax-m3.1-flash:free` è stato ritirato il 22 ottobre (risponde 404). Su 6 modelli gratuiti con immagini, 2 rispondono in 46–178 s, 2 sono limitati a monte (429) e 2 sono bloccati dalle impostazioni privacy dell'account. Il free tier ha circa 50 richieste al giorno, mentre un test con 2 varianti ne fa 60.
- Decisione: solo strumenti gratuiti. Ollama gira sul Mac, senza limiti di richieste e senza che i dati escano dal computer, prototipi riservati compresi.

Il client non cambia: Ollama espone `/v1/chat/completions` compatibile OpenAI, con `response_format` json_schema e immagini. Si cambiano solo le variabili d'ambiente. Per tornare a OpenRouter basta rimettere le variabili di prima.

## Installazione (una volta)

```bash
brew install ollama
brew services start ollama
ollama pull qwen3-vl:8b-instruct
ollama create eco-qwen3-vl-8b -f backend/ollama/Modelfile
```

`eco-qwen3-vl-8b` è `qwen3-vl:8b-instruct` con il contesto a 16k token. Il default di Ollama (4096) taglia in silenzio il prompt del report quando le risposte sono 30.

## Variabili in `backend/.env`

```
RESPONDER=llm
SUMMARIZER=llm
OPENROUTER_BASE_URL=http://localhost:11434/v1
OPENROUTER_API_KEY=ollama
PERSONAS_PATH=data/processed/personas.json
PERSONA_MODEL=eco-qwen3-vl-8b
REPORT_MODEL=eco-qwen3-vl-8b
LLM_TIMEOUT_SECONDS=300
PANEL_CONCURRENCY=2
```

- `OPENROUTER_API_KEY` serve solo alla validazione all'avvio: Ollama ignora la chiave.
- Ollama esegue una richiesta alla volta. Più concorrenza non accelera, allunga solo l'attesa in coda, e una richiesta in coda può superare il timeout. Per questo concorrenza 2 e timeout 300 s.
- `.claude/launch.json` (locale, non versionato) passa le stesse variabili al backend avviato dall'app.

## Scelta del modello (18 novembre)

Confronto con `scripts/compare_models.py`: 10 personas reali, 4 post di calibrazione dall'ordine noto (forte, buono, debole, scadente), 2 ripetizioni, 80 chiamate per modello.

| Modello | JSON valido | Latenza media | Ordine atteso | Scarto migliore-peggiore | Differenze tra personas |
| --- | --- | --- | --- | --- | --- |
| `gemma3:12b` | 60% (32 fallite) | 42 s | 1,00 | 1,90 | 0,31 |
| **`qwen3-vl:8b-instruct`** | **100%** | **19 s** | **1,00** | **2,15** | **0,46** |
| `qwen3-vl:4b-instruct` | 96% (1 fallita) | 13 s, p95 89 s | 0,91 | 0,75 | 0,33 |

- Si usa Qwen3-VL 8B: è il più affidabile e veloce, e il più capace di distinguere i post. Il 4B non distingue i post e scrive un italiano scadente.
- `vl` serve per immagini e screenshot. La variante `instruct`, e non `thinking`, perché servono reazioni a freddo e non lunghi ragionamenti.
- Come modello del report, Qwen giudica la divergenza in modo stabile su casi costruiti apposta.

## Prestazioni misurate (M1 Pro, 16 GB)

| Cosa | Tempo |
| --- | --- |
| Una risposta persona (post) | circa 19 s con Qwen3-VL 8B |
| Una risposta persona (schermata con immagine) | circa 27 s con gemma, da rimisurare con Qwen |
| Test con 2 varianti × 30 personas | circa 20 minuti più 2 per il report (misurato con gemma; Qwen è più veloce per chiamata) |
| Calibrazione su 15 post × 30 personas | circa un'ora e mezza: nella prova generale del 25 novembre, con Qwen3-VL 8B e concorrenza 2, circa 12 s a risposta |

## Limiti noti

- **Allegati PDF:** Ollama non legge i PDF, quindi le prime 4 pagine si convertono in immagini (`pypdfium2`) e arrivano al modello come un carosello. Dalla quinta pagina in poi le personas non le vedono.
- **Qualità, prova reale del 17 novembre con gemma 3** (30 personas: caso cliente concreto contro post generico sulla digitalizzazione): ranking corretto (2,73 contro 1,60), riassunti coerenti con le risposte e che dichiarano la simulazione. Da sistemare nei prompt e nel report:
  - `action`: 23 commenti su 30 e nessuna reazione. Su LinkedIn commentare è raro, quindi il prompt va ricalibrato.
  - Divergenza: 30 su 30, perché la regola confronta i testi e detto e pensato non coincidono mai alla lettera. Non distingue nessuno.
  - Obiezioni quasi uguali contate come diverse («Troppo generico.» e «Troppo generico»).
- **Il Mac deve restare acceso** durante test e calibrazione.

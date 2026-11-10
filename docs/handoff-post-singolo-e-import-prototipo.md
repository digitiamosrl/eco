# Handoff: post singolo e import del prototipo

Da: Fabio · Per: Salvo · 22 ottobre 2026

Il frontend di queste due funzioni è pronto e gira sui mock (`VITE_USE_MOCKS=true`). Al backend serve quanto segue. Gli schemi in `shared/schemas/` sono già aggiornati come proposta. Se cambi qualcosa, dimmelo e riallineo il frontend.

## 1. Post singolo e allegato PDF

Si può testare un solo post, oltre a 2–5 varianti. Il report di un post singolo mostra cosa farebbe ogni persona vedendo il post nel feed. Il post può avere come allegato un'immagine oppure un PDF, che su LinkedIn diventa un documento o un carosello.

**`POST /tests`, multipart:**
- da 1 a 5 varianti, non più da 2 a 5;
- `variants[i][image]` accetta anche `application/pdf`, riconosciuto dai magic bytes `%PDF`, sempre entro i 5 MB.

**Stimulus:** c'è il campo nuovo `attachment_kind`, che vale `"image"` o `"pdf"` quando `image_url` è presente.

**Response:** ci sono due campi nuovi, facoltativi nello schema ma da riempire per tutti i post:

| Campo | Valori | Note |
| --- | --- | --- |
| `action` | `react` · `comment` · `share` · `scroll` | La prima cosa che la persona farebbe nel feed. Una sola |
| `reaction` | `consiglio` · `festeggio` · `sostengo` · `adoro` · `perspicace` · `divertente` | Le reazioni LinkedIn. Solo se `action` è `react` |

**Prompt (`prompts/persona_response.md`):** va chiesto anche `action`, ed eventualmente `reaction`, a freddo come il resto. Scorrere oltre senza fermarsi deve restare una scelta normale.

**Report:** nessun campo nuovo. I conteggi delle azioni li calcola il frontend dalle `responses`.

## 2. Import del prototipo da Figma o da artifact

Oggi il test di prototipo sceglie tra flussi già catturati (`GET /flows`). Nel nuovo flusso l'utente allega il prototipo:
- un link Figma, condiviso con «chiunque abbia il link»;
- oppure il link pubblico di un artifact Claude, o il suo file HTML.

Il backend trova i punti di partenza e cattura le schermate di ogni percorso. L'utente sceglie da 1 a 3 percorsi e può togliere singole schermate.

**`POST /prototypes/import`:**
- **Figma:** JSON `{"source": "figma", "url": "https://www.figma.com/proto/…"}`. Si leggono frame e collegamenti dal punto di partenza tramite l'API di Figma, che richiede un token in `.env`.
- **Artifact per link:** JSON `{"source": "artifact", "url": "https://claude.ai/public/artifacts/…"}`.
- **Artifact per file:** multipart con `source=artifact` e `file` (HTML).
- Per l'artifact: Playwright parte dalla prima schermata e segue pulsanti e link nell'ordine in cui compaiono. Al massimo 2–3 percorsi, come dice il CLAUDE.md.
- **201:** un oggetto `Prototype` (`shared/schemas/prototype.schema.json`), con `starts[].screens[].image_url` serviti da `GET /files/…`. Se trova una sola schermata, risponde con un solo start e una sola schermata: il frontend mostra l'avviso.
- **Errori `{"detail": "..."}` in italiano, che il frontend mostra così come arrivano:**
  - 422 se il link non è un link Figma o artifact valido;
  - 403 se il file Figma è privato, con il testo "Non possiamo aprire il file: è privato. In Figma imposta la condivisione su «chiunque abbia il link» e riprova.";
  - 502 se l'import fallisce per altri motivi.

**`POST /tests`, JSON del prototipo:**

```json
{
  "kind": "prototype",
  "prototype_id": "…",
  "paths": [{ "start_id": "s1", "screen_indexes": [0, 1, 3] }]
}
```

- `paths` contiene da 1 a 3 percorsi.
- `screen_indexes` sono le schermate tenute, in ordine.
- Sostituisce `flow_ids`. `GET /flows` non serve più al frontend.

**Report del prototipo:** resta TBD e il frontend continua a mostrare "non ancora disponibile".

## Cosa resta uguale

Avanzamento (`GET /tests/{id}`), un test alla volta (409), errori in italiano, `GET /tests/{id}/report` per i post.

# Flusso post del frontend: piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Panel, Test e Report funzionanti end-to-end per il pre-test dei post LinkedIn, su mock che rispettano gli schemi condivisi, pronti a passare agli endpoint reali cambiando una variabile d'ambiente.

**Architecture:** Un solo modulo `src/api/` espone le funzioni che le schermate usano. Dietro c'è il client HTTP verso `/api` oppure un mock in memoria che simula un test in esecuzione, scelto con `VITE_USE_MOCKS`. La logica pura (validazione varianti, barre della distribuzione, avanzamento del mock) sta in funzioni testate con Vitest. I componenti si verificano con typecheck, lint, build e una prova manuale.

**Tech Stack:** React 18, Vite 6, TypeScript strict, Vitest 4, CSS semplice con variabili. Tipi generati da `shared/schemas/` con `npm run gen:types`.

**Branch:** `feat/frontend-post-flow`

**Fonti:** `docs/piano-frontend.md`, `docs/piano-backend-per-frontend.md`, `design/wireframes.html`.

---

## Fuori da questo piano

- **Modalità prototipo** (Test 2b e Report 3b dei wireframe): dipende dallo schema `Flow` e dal Report per schermata, da concordare con Salvo il 21 ottobre. Avrà un piano a sé.
- **Testo e immagine della variante nel report:** il `Report` oggi non contiene gli stimoli. Si aggiunge quando lo schema lo prevede.
- **Etichetta "diverge"** sulle risposte: punto aperto con Salvo.
- **Scelta tra più test nel Report:** il Report mostra il test appena finito o il più recente completato.
- **Valori definitivi del brand:** il Task 6 mette valori provvisori nei token, Fabio li sostituisce con quelli del Brand Book.

## Struttura dei file

```
shared/schemas/
  test.schema.json            NUOVO  oggetto Test (bozza, da confermare con Salvo)
frontend/
  .env.example                NUOVO  VITE_USE_MOCKS
  index.html                  MOD    font Montserrat + Poppins
  package.json                MOD    vitest, script test
  src/
    main.tsx                  MOD    import degli stili
    App.tsx                   MOD    navigazione + passaggio Test → Report
    api/
      mock.ts                 NUOVO  test simulati in memoria
      mock.test.ts            NUOVO
      index.ts                NUOVO  funzioni usate dalle schermate: mock o fetch verso /api
    lib/
      variants.ts             NUOVO  regole delle varianti (2–5, testo obbligatorio)
      variants.test.ts        NUOVO
      distribution.ts         NUOVO  distribuzione → 5 barre
      distribution.test.ts    NUOVO
      useLoad.ts              NUOVO  caricamento asincrono con errore
    mocks/index.ts            MOD    3 personas, report con 2 varianti
    styles/
      tokens.css              NUOVO  colori, font, spazi (li decide Fabio)
      base.css                NUOVO  stili dell'app
    components/
      SimulatedBanner.tsx     NUOVO
      ScoreBars.tsx           NUOVO
      SayThink.tsx            NUOVO
      ResponsesTable.tsx      NUOVO
      TestProgress.tsx        NUOVO  polling dello stato del test
    screens/
      PanelScreen.tsx         MOD
      ReportScreen.tsx        MOD
      TestScreen.tsx          MOD
    types/test.ts             GENERATO
```

---

### Task 1: Vitest

**Files:**
- Modify: `frontend/package.json`
- Modify: `CLAUDE.md` (sezione Comandi)

- [ ] **Step 1: Installa Vitest**

Run: `cd frontend && npm install -D vitest@4.1.11`
Expected: `added ... packages`, nessun errore.

- [ ] **Step 2: Aggiungi lo script `test`**

In `frontend/package.json`, dentro `"scripts"`, dopo `"gen:types"`:

```json
    "gen:types": "node scripts/gen-types.mjs",
    "test": "vitest run"
```

- [ ] **Step 3: Verifica che parta**

Run: `cd frontend && npm test`
Expected: `No test files found`, exit code 1. È corretto: i test arrivano nei task successivi.

- [ ] **Step 4: Documenta il comando in `CLAUDE.md`**

Sostituisci la riga:

```bash
cd frontend && npm run lint && npm run typecheck
```

con:

```bash
cd frontend && npm run lint && npm run typecheck && npm test
```

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json CLAUDE.md
git commit -m "chore: add vitest to frontend"
```

---

### Task 2: Schema Test

Lo schema è il contratto con Salvo: è una bozza presa da `docs/piano-backend-per-frontend.md` e va confermata il 21 ottobre.

**Files:**
- Create: `shared/schemas/test.schema.json`
- Generated: `frontend/src/types/test.ts`

- [ ] **Step 1: Scrivi lo schema**

`shared/schemas/test.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "test.schema.json",
  "title": "Test",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "kind", "status", "created_at", "done_count", "total_count"],
  "properties": {
    "id": { "type": "string" },
    "kind": { "type": "string", "enum": ["post", "prototype"] },
    "status": { "type": "string", "enum": ["queued", "running", "done", "error"] },
    "created_at": { "type": "string", "format": "date-time" },
    "done_count": { "type": "integer", "minimum": 0, "description": "Risposte ricevute" },
    "total_count": { "type": "integer", "minimum": 0, "description": "Personas × stimoli" },
    "error": { "type": "string", "description": "Solo se status = error, in italiano" }
  }
}
```

- [ ] **Step 2: Genera i tipi**

Run: `cd frontend && npm run gen:types && grep -n "status" src/types/test.ts`
Expected: `status: "queued" | "running" | "done" | "error";`

- [ ] **Step 3: Commit**

```bash
git add shared/schemas/test.schema.json frontend/src/types/test.ts
git commit -m "feat: add draft Test schema

Draft from docs/piano-backend-per-frontend.md, to confirm with Salvo."
```

---

### Task 3: Regole delle varianti

**Files:**
- Create: `frontend/src/lib/variants.ts`
- Test: `frontend/src/lib/variants.test.ts`

- [ ] **Step 1: Scrivi il test che fallisce**

`frontend/src/lib/variants.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { nextLabel, validateVariants, type VariantDraft } from "./variants";

const variant = (label: string, text: string): VariantDraft => ({ id: label, label, text, image: null });

describe("validateVariants", () => {
  it("accepts 2 variants with text", () => {
    expect(validateVariants([variant("A", "uno"), variant("B", "due")])).toEqual([]);
  });

  it("rejects fewer than 2 variants", () => {
    expect(validateVariants([variant("A", "uno")])).toEqual(["Servono almeno 2 varianti."]);
  });

  it("rejects more than 5 variants", () => {
    const six = ["A", "B", "C", "D", "E", "F"].map((l) => variant(l, "testo"));
    expect(validateVariants(six)).toEqual(["Massimo 5 varianti."]);
  });

  it("rejects variants with blank text", () => {
    expect(validateVariants([variant("A", "uno"), variant("B", "   ")])).toEqual([
      "La variante B non ha testo.",
    ]);
  });
});

describe("nextLabel", () => {
  it("labels variants with letters", () => {
    expect([0, 1, 4].map(nextLabel)).toEqual(["A", "B", "E"]);
  });
});
```

- [ ] **Step 2: Verifica che fallisca**

Run: `cd frontend && npm test -- src/lib/variants.test.ts`
Expected: FAIL, `Failed to resolve import "./variants"`.

- [ ] **Step 3: Implementa**

`frontend/src/lib/variants.ts`:

```ts
export type VariantDraft = { id: string; label: string; text: string; image: File | null };

export const MIN_VARIANTS = 2;
export const MAX_VARIANTS = 5;

export const nextLabel = (index: number) => String.fromCharCode(65 + index);

export function validateVariants(variants: VariantDraft[]): string[] {
  const errors: string[] = [];
  if (variants.length < MIN_VARIANTS) errors.push(`Servono almeno ${MIN_VARIANTS} varianti.`);
  if (variants.length > MAX_VARIANTS) errors.push(`Massimo ${MAX_VARIANTS} varianti.`);
  for (const v of variants) {
    if (!v.text.trim()) errors.push(`La variante ${v.label} non ha testo.`);
  }
  return errors;
}
```

- [ ] **Step 4: Verifica che passi**

Run: `cd frontend && npm test -- src/lib/variants.test.ts`
Expected: PASS, 5 test.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/variants.ts frontend/src/lib/variants.test.ts
git commit -m "feat: add post variant validation"
```

---

### Task 4: Barre della distribuzione

`score_distribution` arriva come oggetto `{"1": 0, "2": 1, ...}` e può non avere tutte le chiavi. Le barre sono sempre 5, con altezza relativa alla più alta, come nei wireframe.

**Files:**
- Create: `frontend/src/lib/distribution.ts`
- Test: `frontend/src/lib/distribution.test.ts`

- [ ] **Step 1: Scrivi il test che fallisce**

`frontend/src/lib/distribution.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { toBars } from "./distribution";

describe("toBars", () => {
  it("returns 5 bars with height relative to the tallest", () => {
    expect(toBars({ "1": 0, "2": 1, "3": 2, "4": 4, "5": 2 })).toEqual([
      { score: 1, count: 0, height: 0 },
      { score: 2, count: 1, height: 0.25 },
      { score: 3, count: 2, height: 0.5 },
      { score: 4, count: 4, height: 1 },
      { score: 5, count: 2, height: 0.5 },
    ]);
  });

  it("fills missing scores with zero", () => {
    expect(toBars({ "3": 2 }).map((b) => b.count)).toEqual([0, 0, 2, 0, 0]);
  });

  it("handles an empty distribution", () => {
    expect(toBars({}).map((b) => b.height)).toEqual([0, 0, 0, 0, 0]);
  });
});
```

- [ ] **Step 2: Verifica che fallisca**

Run: `cd frontend && npm test -- src/lib/distribution.test.ts`
Expected: FAIL, `Failed to resolve import "./distribution"`.

- [ ] **Step 3: Implementa**

`frontend/src/lib/distribution.ts`:

```ts
export type Bar = { score: number; count: number; height: number };

const SCORES = [1, 2, 3, 4, 5];

export function toBars(distribution: Record<string, number>): Bar[] {
  const counts = SCORES.map((s) => distribution[String(s)] ?? 0);
  const max = Math.max(...counts);
  return SCORES.map((score, i) => ({
    score,
    count: counts[i],
    height: max === 0 ? 0 : counts[i] / max,
  }));
}
```

- [ ] **Step 4: Verifica che passi**

Run: `cd frontend && npm test -- src/lib/distribution.test.ts`
Expected: PASS, 3 test.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/distribution.ts frontend/src/lib/distribution.test.ts
git commit -m "feat: add score distribution bars helper"
```

---

### Task 5: Modulo API con mock

Le schermate importano solo da `src/api`. Con `VITE_USE_MOCKS` diverso da `"false"` (default) rispondono i mock; con `false` si chiama il backend via il proxy `/api` già configurato in `vite.config.ts`.

Il mock simula un test che dura 5 secondi, così si vede la barra di avanzamento.

**Files:**
- Modify: `frontend/src/mocks/index.ts`
- Create: `frontend/src/api/mock.ts`
- Create: `frontend/src/api/index.ts`
- Create: `frontend/.env.example`
- Test: `frontend/src/api/mock.test.ts`

- [ ] **Step 1: Aggiorna i dati finti**

Sostituisci tutto `frontend/src/mocks/index.ts` con:

```ts
// Mocks based on shared schemas, used until the endpoints are ready.
import type { Persona } from "../types/persona";
import type { Report } from "../types/report";

export const mockPersonas: Persona[] = [
  {
    id: "p1",
    role: "Titolare",
    sector: "Manifattura",
    company_size: "piccola",
    region: "Lombardia",
    profile: "Guida l'azienda di famiglia, poco tempo per LinkedIn.",
  },
  {
    id: "p2",
    role: "Direttrice commerciale",
    sector: "Servizi B2B",
    company_size: "media",
    region: "Emilia-Romagna",
    profile: "Valuta fornitori digitali, diffidente verso le promesse generiche.",
  },
  {
    id: "p3",
    role: "Amministratore",
    sector: "Commercio",
    company_size: "micro",
    region: "Puglia",
    profile: "Decide da solo, molto attento ai costi.",
  },
];

export const mockReport: Report = {
  test_id: "t1",
  simulated: true,
  summary: "La variante B convince per concretezza; la A è percepita come troppo generica.",
  items: [
    {
      stimulus_id: "B",
      rank: 1,
      mean_score: 3.7,
      score_distribution: { "1": 0, "2": 1, "3": 0, "4": 1, "5": 1 },
      objections: ["Non dice quanto costa"],
      said_summary: "Lo trovano utile e concreto, qualcuno lo girerebbe al team.",
      thought_summary: "Si fidano, ma pensano al costo senza dirlo.",
      responses: [
        {
          persona_id: "p1",
          stimulus_id: "B",
          thought: "Mi piace, ma se costa come l'ultimo consulente lascio stare.",
          said: "Esempio chiaro, complimenti.",
          score: 4,
          objections: ["Non dice quanto costa"],
        },
        {
          persona_id: "p2",
          stimulus_id: "B",
          thought: "Finalmente numeri veri. Lo giro al team.",
          said: "Lo giro al team.",
          score: 5,
          objections: [],
        },
        {
          persona_id: "p3",
          stimulus_id: "B",
          thought: "Roba per aziende più grandi della mia.",
          said: "",
          score: 2,
          objections: ["Non adatto a una micro impresa"],
        },
      ],
    },
    {
      stimulus_id: "A",
      rank: 2,
      mean_score: 2.3,
      score_distribution: { "1": 0, "2": 2, "3": 1, "4": 0, "5": 0 },
      objections: ["Troppo generico"],
      said_summary: "Apprezzano il tema e lo definiscono interessante.",
      thought_summary: "In privato lo trovano vago: manca un esempio concreto.",
      responses: [
        {
          persona_id: "p1",
          stimulus_id: "A",
          thought: "Bello, ma a me cosa cambia? Non ho tempo.",
          said: "Spunto interessante, grazie.",
          score: 2,
          objections: ["Non dice cosa ottengo"],
        },
        {
          persona_id: "p2",
          stimulus_id: "A",
          thought: "Il solito post sulla trasformazione digitale.",
          said: "Tema importante.",
          score: 3,
          objections: ["Troppo generico"],
        },
        {
          persona_id: "p3",
          stimulus_id: "A",
          thought: "Non ho capito cosa vendono.",
          said: "",
          score: 2,
          objections: ["Troppo generico"],
        },
      ],
    },
  ],
};
```

- [ ] **Step 2: Scrivi il test del mock che fallisce**

`frontend/src/api/mock.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import type { Test } from "../types/test";
import { RUN_MS, progress } from "./mock";

const test: Test = {
  id: "t9",
  kind: "post",
  status: "queued",
  created_at: "2026-10-15T10:00:00Z",
  done_count: 0,
  total_count: 6,
};

describe("progress", () => {
  it("is running with no answers at start", () => {
    expect(progress(test, 1000, 1000)).toMatchObject({ status: "running", done_count: 0 });
  });

  it("is halfway after half the run", () => {
    expect(progress(test, 1000, 1000 + RUN_MS / 2)).toMatchObject({ status: "running", done_count: 3 });
  });

  it("is done after the full run", () => {
    expect(progress(test, 1000, 1000 + RUN_MS * 2)).toMatchObject({ status: "done", done_count: 6 });
  });
});
```

- [ ] **Step 3: Verifica che fallisca**

Run: `cd frontend && npm test -- src/api/mock.test.ts`
Expected: FAIL, `Failed to resolve import "./mock"`.

- [ ] **Step 4: Implementa il mock**

`frontend/src/api/mock.ts`:

```ts
// In-memory fake backend. Simulates a test that takes RUN_MS to complete.
import { mockPersonas, mockReport } from "../mocks";
import type { Persona } from "../types/persona";
import type { Report } from "../types/report";
import type { Test } from "../types/test";

export const RUN_MS = 5000;

const started = new Map<string, { test: Test; startedAt: number }>([
  [
    "t1",
    {
      test: {
        id: "t1",
        kind: "post",
        status: "done",
        created_at: "2026-10-15T10:00:00Z",
        done_count: 6,
        total_count: 6,
      },
      startedAt: 0,
    },
  ],
]);

export function progress(test: Test, startedAt: number, now: number): Test {
  const ratio = Math.min(1, (now - startedAt) / RUN_MS);
  return {
    ...test,
    status: ratio >= 1 ? "done" : "running",
    done_count: Math.round(ratio * test.total_count),
  };
}

export async function getPersonas(): Promise<Persona[]> {
  return mockPersonas;
}

export async function startPostTest(variantCount: number): Promise<Test> {
  const id = `t${started.size + 1}`;
  const test: Test = {
    id,
    kind: "post",
    status: "queued",
    created_at: new Date().toISOString(),
    done_count: 0,
    total_count: variantCount * mockPersonas.length,
  };
  started.set(id, { test, startedAt: Date.now() });
  return test;
}

export async function getTest(id: string): Promise<Test> {
  const entry = started.get(id);
  if (!entry) throw new Error("Test non trovato.");
  return progress(entry.test, entry.startedAt, Date.now());
}

export async function getTests(): Promise<Test[]> {
  return [...started.values()].map((e) => progress(e.test, e.startedAt, Date.now())).reverse();
}

export async function getReport(id: string): Promise<Report> {
  return { ...mockReport, test_id: id };
}
```

- [ ] **Step 5: Verifica che passi**

Run: `cd frontend && npm test -- src/api/mock.test.ts`
Expected: PASS, 3 test.

- [ ] **Step 6: Funzioni per le schermate**

`frontend/src/api/index.ts`:

```ts
import type { VariantDraft } from "../lib/variants";
import type { Persona } from "../types/persona";
import type { Report } from "../types/report";
import type { Test } from "../types/test";
import * as mock from "./mock";

const useMocks = import.meta.env.VITE_USE_MOCKS !== "false";

async function parse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.detail ?? `Errore del server (${res.status}).`);
  return data as T;
}

const getJson = async <T,>(path: string) => parse<T>(await fetch(`/api${path}`));

const postForm = async <T,>(path: string, body: FormData) =>
  parse<T>(await fetch(`/api${path}`, { method: "POST", body }));

export const getPersonas = () => (useMocks ? mock.getPersonas() : getJson<Persona[]>("/personas"));

export const getTests = () => (useMocks ? mock.getTests() : getJson<Test[]>("/tests"));

export const getTest = (id: string) => (useMocks ? mock.getTest(id) : getJson<Test>(`/tests/${id}`));

export const getReport = (id: string) =>
  useMocks ? mock.getReport(id) : getJson<Report>(`/tests/${id}/report`);

export function startPostTest(variants: VariantDraft[]): Promise<Test> {
  if (useMocks) return mock.startPostTest(variants.length);
  const form = new FormData();
  form.append("kind", "post");
  variants.forEach((v, i) => {
    form.append(`variants[${i}][label]`, v.label);
    form.append(`variants[${i}][text]`, v.text);
    if (v.image) form.append(`variants[${i}][image]`, v.image);
  });
  return postForm<Test>("/tests", form);
}
```

- [ ] **Step 7: Documenta la variabile**

`frontend/.env.example`:

```
# true (default): dati finti in memoria. false: chiama il backend su /api.
VITE_USE_MOCKS=true
```

- [ ] **Step 8: Verifica tutto**

Run: `cd frontend && npm test && npm run typecheck && npm run lint`
Expected: 11 test PASS, typecheck e lint senza errori.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/mocks/index.ts frontend/src/api frontend/.env.example
git commit -m "feat: add api module with in-memory mock backend"
```

---

### Task 6: Stili e token

I colori sono provvisori. **Fabio** sostituisce i valori in `tokens.css` con quelli del Brand Book Digitiamo: è l'unico file da toccare per cambiare il look.

**Files:**
- Create: `frontend/src/styles/tokens.css`
- Create: `frontend/src/styles/base.css`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/index.html`

- [ ] **Step 1: Token**

`frontend/src/styles/tokens.css`:

```css
/* Design tokens. Provisional values: replace with the Digitiamo Brand Book. */
:root {
  --color-ink: #1d1b2e;
  --color-muted: #6b6880;
  --color-line: #d9d6e5;
  --color-surface: #ffffff;
  --color-bg: #f6f5fa;
  --color-primary: #5b2ee0;
  --color-primary-ink: #ffffff;
  --color-think-bg: #f0edfb;
  --color-alert: #b42318;
  --font-heading: "Montserrat", system-ui, sans-serif;
  --font-body: "Poppins", system-ui, sans-serif;
  --radius: 8px;
  --space: 16px;
}
```

- [ ] **Step 2: Stili dell'app**

`frontend/src/styles/base.css`:

```css
* { box-sizing: border-box; }
body { margin: 0; font: 15px/1.5 var(--font-body); color: var(--color-ink); background: var(--color-bg); }
h1, h2, h3 { font-family: var(--font-heading); line-height: 1.2; }
h1 { font-size: 1.6rem; margin: 0 0 4px; }
h2 { font-size: 1.2rem; margin: 0 0 12px; }
h3 { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-muted); margin: 16px 0 6px; }

.app-nav { display: flex; align-items: center; gap: 8px; padding: 12px var(--space); background: var(--color-surface); border-bottom: 1px solid var(--color-line); }
.app-nav strong { margin-right: auto; font-family: var(--font-heading); }
.app-nav button { background: none; border: 0; border-bottom: 2px solid transparent; padding: 6px 10px; font: inherit; color: var(--color-muted); cursor: pointer; }
.app-nav button[aria-current="page"] { color: var(--color-ink); border-bottom-color: var(--color-primary); }

main { max-width: 1100px; margin: 0 auto; padding: 24px var(--space); }
.sub { color: var(--color-muted); margin: 0 0 20px; }
.card { background: var(--color-surface); border: 1px solid var(--color-line); border-radius: var(--radius); padding: var(--space); margin-bottom: var(--space); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: var(--space); margin-bottom: var(--space); }

button.primary { background: var(--color-primary); color: var(--color-primary-ink); border: 0; border-radius: var(--radius); padding: 10px 18px; font: inherit; font-weight: 600; cursor: pointer; }
button.primary:disabled { opacity: 0.6; cursor: wait; }
button.secondary { background: none; border: 1px dashed var(--color-line); border-radius: var(--radius); padding: 10px 18px; font: inherit; color: var(--color-muted); cursor: pointer; }

label { display: block; font-weight: 600; margin-top: 10px; }
textarea, select, input[type="file"] { display: block; width: 100%; margin-top: 4px; font: inherit; font-weight: 400; }
textarea { min-height: 120px; padding: 8px; border: 1px solid var(--color-line); border-radius: var(--radius); }
[role="alert"] { color: var(--color-alert); }

.banner { border: 2px dashed var(--color-primary); border-radius: var(--radius); padding: 10px 14px; background: var(--color-surface); margin: 0 0 20px; }

.score-bars { margin: 0; }
.score-bars figcaption { font-size: 0.85rem; color: var(--color-muted); }
.bars { display: flex; align-items: flex-end; gap: 4px; height: 70px; max-width: 240px; }
.bar { flex: 1; background: var(--color-primary); border-radius: 2px 2px 0 0; min-height: 2px; }
.bars-x { display: flex; gap: 4px; max-width: 240px; font-size: 0.75rem; color: var(--color-muted); }
.bars-x span { flex: 1; text-align: center; }

.say-think { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.say-think > div { border: 1px solid var(--color-line); border-radius: var(--radius); padding: 0 12px; }
.say-think .think, td.think { background: var(--color-think-bg); font-style: italic; }

details { margin-top: 16px; }
summary { cursor: pointer; font-weight: 600; }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; vertical-align: top; padding: 8px; border-bottom: 1px solid var(--color-line); }
th { font-size: 0.8rem; color: var(--color-muted); font-weight: 500; }

progress { width: 100%; height: 12px; accent-color: var(--color-primary); }

@media (max-width: 640px) {
  .say-think { grid-template-columns: 1fr; }
}
```

- [ ] **Step 3: Importa gli stili**

In `frontend/src/main.tsx`, dopo `import App from "./App";`:

```ts
import "./styles/tokens.css";
import "./styles/base.css";
```

- [ ] **Step 4: Font**

In `frontend/index.html`, dopo `<title>eco</title>`:

```html
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&family=Poppins:wght@400;600&display=swap"
      rel="stylesheet"
    />
```

- [ ] **Step 5: Verifica**

Run: `cd frontend && npm run build`
Expected: build riuscita, in `dist/assets/` c'è un file `.css`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/styles frontend/src/main.tsx frontend/index.html
git commit -m "feat: add design tokens and base styles"
```

---

### Task 7: Caricamento dati e schermata Panel

**Files:**
- Create: `frontend/src/lib/useLoad.ts`
- Modify: `frontend/src/screens/PanelScreen.tsx`

- [ ] **Step 1: Hook di caricamento**

`frontend/src/lib/useLoad.ts`:

```ts
import { useEffect, useState } from "react";

// Loads data on mount and whenever deps change; ignores results of stale calls.
export function useLoad<T>(load: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setData(null);
    setError(null);
    load().then(
      (d) => {
        if (alive) setData(d);
      },
      (e: Error) => {
        if (alive) setError(e.message);
      },
    );
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error };
}
```

- [ ] **Step 2: Panel**

Sostituisci tutto `frontend/src/screens/PanelScreen.tsx` con:

```tsx
import { getPersonas } from "../api";
import { useLoad } from "../lib/useLoad";

const SIZES = ["micro", "piccola", "media"] as const;

export default function PanelScreen() {
  const { data: personas, error } = useLoad(getPersonas, []);

  if (error) return <p role="alert">{error}</p>;
  if (!personas) return <p>Caricamento del panel…</p>;

  return (
    <section>
      <h1>Panel</h1>
      <p className="sub">Decision maker di PMI italiane · {personas.length} personas sintetiche</p>
      <div className="grid">
        {SIZES.map((size) => (
          <div key={size} className="card">
            <h3>{size}</h3>
            <strong>{personas.filter((p) => p.company_size === size).length}</strong> personas
          </div>
        ))}
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Ruolo</th>
              <th scope="col">Settore</th>
              <th scope="col">Dimensione</th>
              <th scope="col">Regione</th>
              <th scope="col">Profilo</th>
            </tr>
          </thead>
          <tbody>
            {personas.map((p) => (
              <tr key={p.id}>
                <td>{p.role}</td>
                <td>{p.sector}</td>
                <td>{p.company_size}</td>
                <td>{p.region}</td>
                <td>{p.profile}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Verifica**

Run: `cd frontend && npm run typecheck && npm run lint`
Expected: nessun errore.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/useLoad.ts frontend/src/screens/PanelScreen.tsx
git commit -m "feat: load panel from api module"
```

---

### Task 8: Schermata Report

**Files:**
- Create: `frontend/src/components/SimulatedBanner.tsx`
- Create: `frontend/src/components/ScoreBars.tsx`
- Create: `frontend/src/components/SayThink.tsx`
- Create: `frontend/src/components/ResponsesTable.tsx`
- Modify: `frontend/src/screens/ReportScreen.tsx`

- [ ] **Step 1: Avviso "simulato"**

`frontend/src/components/SimulatedBanner.tsx`:

```tsx
export default function SimulatedBanner() {
  return (
    <p className="banner" role="note">
      <strong>Risultati simulati.</strong> Reazioni di personas sintetiche, non di persone reali.
      Usali per confrontare varianti, non come previsione.
    </p>
  );
}
```

- [ ] **Step 2: Barre della distribuzione**

`frontend/src/components/ScoreBars.tsx`:

```tsx
import { toBars } from "../lib/distribution";

type Props = { distribution: Record<string, number>; mean: number };

export default function ScoreBars({ distribution, mean }: Props) {
  const bars = toBars(distribution);
  return (
    <figure className="score-bars">
      <figcaption>Distribuzione dei voti (media {mean.toFixed(1)})</figcaption>
      <div
        className="bars"
        role="img"
        aria-label={bars.map((b) => `voto ${b.score}: ${b.count}`).join(", ")}
      >
        {bars.map((b) => (
          <div key={b.score} className="bar" style={{ height: `${b.height * 100}%` }} />
        ))}
      </div>
      <div className="bars-x" aria-hidden="true">
        {bars.map((b) => (
          <span key={b.score}>{b.score}</span>
        ))}
      </div>
    </figure>
  );
}
```

- [ ] **Step 3: Cosa dicono / cosa pensano**

`frontend/src/components/SayThink.tsx`:

```tsx
type Props = { said: string; thought: string };

export default function SayThink({ said, thought }: Props) {
  return (
    <div className="say-think">
      <div>
        <h3>Cosa dicono</h3>
        <p>{said}</p>
      </div>
      <div className="think">
        <h3>Cosa pensano</h3>
        <p>{thought}</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Tabella delle risposte**

`frontend/src/components/ResponsesTable.tsx`:

```tsx
import type { Persona } from "../types/persona";
import type { Response } from "../types/response";

type Props = { responses: Response[]; personas: Persona[] };

export default function ResponsesTable({ responses, personas }: Props) {
  const label = (id: string) => {
    const p = personas.find((p) => p.id === id);
    return p ? `${p.role} · ${p.sector} · ${p.company_size}` : id;
  };

  return (
    <details>
      <summary>Risposte delle personas ({responses.length})</summary>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Persona</th>
              <th scope="col">Voto</th>
              <th scope="col">Ha detto</th>
              <th scope="col">Ha pensato</th>
            </tr>
          </thead>
          <tbody>
            {responses.map((r) => (
              <tr key={r.persona_id}>
                <td>{label(r.persona_id)}</td>
                <td>{r.score}</td>
                <td>{r.said || "Non commenterebbe"}</td>
                <td className="think">{r.thought}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
```

- [ ] **Step 5: Report**

Sostituisci tutto `frontend/src/screens/ReportScreen.tsx` con:

```tsx
import { getPersonas, getReport, getTests } from "../api";
import ResponsesTable from "../components/ResponsesTable";
import SayThink from "../components/SayThink";
import ScoreBars from "../components/ScoreBars";
import SimulatedBanner from "../components/SimulatedBanner";
import { useLoad } from "../lib/useLoad";
import type { Report } from "../types/report";

export default function ReportScreen({ testId }: { testId?: string }) {
  const tests = useLoad(getTests, []);
  const personas = useLoad(getPersonas, []);
  const selected = testId ?? tests.data?.find((t) => t.status === "done")?.id;
  const report = useLoad<Report | null>(
    () => (selected ? getReport(selected) : Promise.resolve(null)),
    [selected],
  );

  const error = tests.error ?? personas.error ?? report.error;
  if (error) return <p role="alert">{error}</p>;
  if (!tests.data) return <p>Caricamento…</p>;
  if (!selected) return <p>Nessun test completato. Avviane uno dalla schermata Test.</p>;
  if (!report.data) return <p>Caricamento del report…</p>;

  const items = [...report.data.items].sort((a, b) => a.rank - b.rank);

  return (
    <section>
      <SimulatedBanner />
      <h1>Report · {items.length} varianti</h1>
      <p className="sub">{report.data.summary}</p>
      {items.map((item) => (
        <article key={item.stimulus_id} className="card">
          <h2>
            #{item.rank} · Variante {item.stimulus_id}
          </h2>
          <ScoreBars distribution={item.score_distribution} mean={item.mean_score} />
          <h3>Obiezioni principali</h3>
          <ul>
            {item.objections.map((o) => (
              <li key={o}>{o}</li>
            ))}
          </ul>
          <SayThink said={item.said_summary} thought={item.thought_summary} />
          <ResponsesTable responses={item.responses} personas={personas.data ?? []} />
        </article>
      ))}
    </section>
  );
}
```

- [ ] **Step 6: Verifica**

Run: `cd frontend && npm run typecheck && npm run lint && npm test`
Expected: nessun errore, 11 test PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components frontend/src/screens/ReportScreen.tsx
git commit -m "feat: build post report with distribution and said/thought"
```

---

### Task 9: Schermata Test, avanzamento e navigazione

**Files:**
- Create: `frontend/src/components/TestProgress.tsx`
- Modify: `frontend/src/screens/TestScreen.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Avanzamento con polling**

`frontend/src/components/TestProgress.tsx`:

```tsx
import { useEffect, useState } from "react";
import { getTest } from "../api";
import type { Test } from "../types/test";

const POLL_MS = 2000;

type Props = { initial: Test; onShowReport: (testId: string) => void };

export default function TestProgress({ initial, onShowReport }: Props) {
  const [test, setTest] = useState(initial);
  const [error, setError] = useState<string | null>(null);

  // Each new Test state schedules the next poll, until done or error.
  useEffect(() => {
    if (test.status === "done" || test.status === "error") return;
    const timer = setTimeout(() => {
      getTest(test.id).then(setTest, (e: Error) => setError(e.message));
    }, POLL_MS);
    return () => clearTimeout(timer);
  }, [test]);

  const retry = () => {
    setError(null);
    setTest({ ...test });
  };

  return (
    <section>
      <h1>{test.status === "done" ? "Test completato" : "Test in corso"}</h1>
      <progress max={test.total_count || 1} value={test.done_count} />
      <p>
        {test.done_count} risposte su {test.total_count}
      </p>
      {test.status === "error" && <p role="alert">{test.error ?? "Il test si è interrotto."}</p>}
      {error && (
        <p role="alert">
          {error}{" "}
          <button type="button" className="secondary" onClick={retry}>
            Riprova
          </button>
        </p>
      )}
      {test.status === "done" && (
        <button type="button" className="primary" onClick={() => onShowReport(test.id)}>
          Vai al report
        </button>
      )}
    </section>
  );
}
```

- [ ] **Step 2: Form delle varianti**

Sostituisci tutto `frontend/src/screens/TestScreen.tsx` con:

```tsx
import { useState } from "react";
import { startPostTest } from "../api";
import TestProgress from "../components/TestProgress";
import {
  MAX_VARIANTS,
  MIN_VARIANTS,
  nextLabel,
  validateVariants,
  type VariantDraft,
} from "../lib/variants";
import type { Test } from "../types/test";

const emptyVariant = (index: number): VariantDraft => ({
  id: crypto.randomUUID(),
  label: nextLabel(index),
  text: "",
  image: null,
});

type Props = { onShowReport: (testId: string) => void };

export default function TestScreen({ onShowReport }: Props) {
  const [variants, setVariants] = useState<VariantDraft[]>([emptyVariant(0), emptyVariant(1)]);
  const [errors, setErrors] = useState<string[]>([]);
  const [sending, setSending] = useState(false);
  const [test, setTest] = useState<Test | null>(null);

  const update = (id: string, patch: Partial<VariantDraft>) =>
    setVariants((vs) => vs.map((v) => (v.id === id ? { ...v, ...patch } : v)));

  const remove = (id: string) =>
    setVariants((vs) => vs.filter((v) => v.id !== id).map((v, i) => ({ ...v, label: nextLabel(i) })));

  async function start() {
    const found = validateVariants(variants);
    setErrors(found);
    if (found.length > 0) return;
    setSending(true);
    try {
      setTest(await startPostTest(variants));
    } catch (e) {
      setErrors([(e as Error).message]);
    } finally {
      setSending(false);
    }
  }

  if (test) return <TestProgress initial={test} onShowReport={onShowReport} />;

  return (
    <section>
      <h1>Nuovo test</h1>
      <p className="sub">
        Confronta da {MIN_VARIANTS} a {MAX_VARIANTS} varianti dello stesso post LinkedIn
      </p>
      <div className="grid">
        {variants.map((v) => (
          <div key={v.id} className="card">
            <h2>Variante {v.label}</h2>
            <label>
              Testo del post
              <textarea value={v.text} onChange={(e) => update(v.id, { text: e.target.value })} />
            </label>
            <label>
              Immagine (facoltativa)
              <input
                type="file"
                accept="image/*"
                onChange={(e) => update(v.id, { image: e.target.files?.[0] ?? null })}
              />
            </label>
            {variants.length > MIN_VARIANTS && (
              <button type="button" className="secondary" onClick={() => remove(v.id)}>
                Rimuovi
              </button>
            )}
          </div>
        ))}
        {variants.length < MAX_VARIANTS && (
          <button
            type="button"
            className="secondary"
            onClick={() => setVariants((vs) => [...vs, emptyVariant(vs.length)])}
          >
            + Aggiungi variante
          </button>
        )}
      </div>
      {errors.length > 0 && (
        <ul role="alert">
          {errors.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      )}
      <button type="button" className="primary" disabled={sending} onClick={start}>
        {sending ? "Avvio…" : "Avvia test"}
      </button>
    </section>
  );
}
```

- [ ] **Step 3: Navigazione**

Sostituisci tutto `frontend/src/App.tsx` con:

```tsx
import { useState } from "react";
import PanelScreen from "./screens/PanelScreen";
import ReportScreen from "./screens/ReportScreen";
import TestScreen from "./screens/TestScreen";

const SCREENS = { panel: "Panel", test: "Test", report: "Report" } as const;
type ScreenKey = keyof typeof SCREENS;

export default function App() {
  const [current, setCurrent] = useState<ScreenKey>("panel");
  const [reportId, setReportId] = useState<string>();

  const showReport = (testId: string) => {
    setReportId(testId);
    setCurrent("report");
  };

  return (
    <>
      <nav className="app-nav">
        <strong>eco</strong>
        {(Object.keys(SCREENS) as ScreenKey[]).map((key) => (
          <button
            key={key}
            type="button"
            aria-current={key === current ? "page" : undefined}
            onClick={() => setCurrent(key)}
          >
            {SCREENS[key]}
          </button>
        ))}
      </nav>
      <main>
        {current === "panel" && <PanelScreen />}
        {current === "test" && <TestScreen onShowReport={showReport} />}
        {current === "report" && <ReportScreen testId={reportId} />}
      </main>
    </>
  );
}
```

- [ ] **Step 4: Verifica**

Run: `cd frontend && npm run typecheck && npm run lint && npm test`
Expected: nessun errore, 11 test PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/TestProgress.tsx frontend/src/screens/TestScreen.tsx frontend/src/App.tsx
git commit -m "feat: add post test form with progress polling"
```

---

### Task 10: Verifica finale

- [ ] **Step 1: Controlli automatici**

Run: `cd frontend && npm test && npm run typecheck && npm run lint && npm run build`
Expected: 11 test PASS, nessun errore, build riuscita.

- [ ] **Step 2: Prova manuale**

Run: `cd frontend && npm run dev` e apri l'URL stampato da Vite.

Controlla, in ordine:
1. **Panel:** 3 personas, conteggi micro 1 · piccola 1 · media 1.
2. **Test:** clicca "Avvia test" con le varianti vuote → compaiono "La variante A non ha testo." e "La variante B non ha testo.".
3. Aggiungi varianti fino a 5 → il bottone "+ Aggiungi variante" sparisce. Rimuovi la C → le lettere restano A, B, C, D in ordine.
4. Scrivi un testo in A e B, togli le altre, avvia → barra di avanzamento, dopo circa 5 secondi "Test completato" e "Vai al report".
5. **Report:** avviso "Risultati simulati" in cima, variante B prima, barre con altezze diverse, riquadri "Cosa dicono" e "Cosa pensano", tabella espandibile con 3 risposte.
6. Restringi la finestra a 375 px: niente scroll orizzontale della pagina, "Cosa dicono" e "Cosa pensano" vanno uno sotto l'altro.

- [ ] **Step 3: Push del branch**

Solo quando Fabio lo chiede:

```bash
git push -u origin feat/frontend-post-flow
```

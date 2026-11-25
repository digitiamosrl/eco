# Dashboard dei test — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A dashboard home listing past tests, a page per test that shows progress then its saved report, a Panel page in a sidebar, and a local user name stored with each test.

**Architecture:** Backend: two optional fields on `Test` (`title`, `created_by`) stored as new SQLite columns, and a `reports` table so a report is generated once and survives restarts (fidelity is attached at read time). Frontend: a 30-line hash router picks the page; `TestScreen` splits into `NewTestScreen` (the form) and `TestPage` (progress, then `ReportScreen` for that test); `AppNav` gives way to a new DS `Sidebar`.

**Tech Stack:** FastAPI, Pydantic, SQLite (backend); React 18, Vite, TypeScript strict, vitest (frontend). No new dependencies.

Spec: `docs/superpowers/specs/2026-11-25-dashboard-design.md`.

Commands (from repo root):
- backend tests: `cd backend && .venv/bin/pytest -q` · lint: `cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .`
- frontend: `cd frontend && npm run lint && npm run typecheck && npm test && npm run build`

---

## File map

| File | Change |
| --- | --- |
| `shared/schemas/test.schema.json` | + `title`, `created_by` |
| `backend/app/models.py` | `Test` + fields; `PostTestRequest`, `PrototypeTestRequest` + `created_by` |
| `backend/app/store.py` | new columns with migration; `reports` table; `save_report`, `load_report` |
| `backend/app/api/create_request.py` | read `created_by` from the form |
| `backend/app/api/tests.py` | `_title`, `created_by` in `_build_test` |
| `backend/app/api/reports.py` | read/write the saved report, fidelity at read |
| `backend/tests/test_dashboard_fields.py` | new |
| `backend/tests/test_saved_reports.py` | new |
| `frontend/src/types/test.ts`, `stimulus.ts`… | regenerated |
| `frontend/src/lib/route.ts` (+ test) | new: hash router |
| `frontend/src/lib/userName.ts` | new: local name |
| `frontend/src/lib/format.ts` (+ test) | new: `formatWhen`, `testTitle` |
| `frontend/src/api/index.ts`, `api/mock.ts` | send `created_by`; mock titles and seeded tests |
| `frontend/src/ds/components/navigation/Sidebar.tsx` | new |
| `frontend/src/ds/components/test/TestRow.tsx` | new |
| `frontend/src/ds/components.css`, `ds/index.ts` | styles and exports |
| `frontend/src/screens/DashboardScreen.tsx` | new |
| `frontend/src/screens/NameScreen.tsx` | new: first-run name |
| `frontend/src/screens/NewTestScreen.tsx` | renamed from `TestScreen.tsx`, form only |
| `frontend/src/screens/TestPage.tsx` | new: progress + report |
| `frontend/src/screens/ReportScreen.tsx` | takes the loaded `test` |
| `frontend/src/App.tsx` | routes + sidebar |
| `CLAUDE.md`, `docs/contratti-backend.md` | screens rule; contract note |

---

### Task 1: `title` and `created_by` on Test, stored in SQLite

**Files:** Modify `shared/schemas/test.schema.json`, `backend/app/models.py`, `backend/app/store.py`. Test: `backend/tests/test_dashboard_fields.py`.

- [ ] **Step 1: failing test**

```python
# backend/tests/test_dashboard_fields.py
from app import store
from app.models import Stimulus, Test


def _test(**extra) -> Test:
    return Test(
        id="t1",
        kind="post",
        status="queued",
        created_at="2026-11-25T10:00:00+00:00",
        done_count=0,
        total_count=1,
        stimuli=[Stimulus(id="variante-a", kind="post", variant_label="A", text="Ciao")],
        **extra,
    )


def test_title_and_author_survive_the_store(validate) -> None:
    assert store.add_if_idle(_test(title="Ciao", created_by="Fabio"))
    saved = store.get("t1")
    assert (saved.title, saved.created_by) == ("Ciao", "Fabio")
    validate("test.schema.json", saved.model_dump(mode="json", exclude_none=True))


def test_old_database_gains_the_new_columns(tmp_path, monkeypatch) -> None:
    import sqlite3

    from app.config import settings

    path = tmp_path / "old.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE tests (id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT NOT NULL,"
            " created_at TEXT NOT NULL, done_count INTEGER NOT NULL, total_count INTEGER NOT NULL,"
            " stimuli TEXT NOT NULL, error TEXT)"
        )
    monkeypatch.setattr(settings, "database_path", str(path))
    store.init_db()
    assert store.add_if_idle(_test(title="Ciao"))
    assert store.get("t1").title == "Ciao"
```

- [ ] **Step 2:** `cd backend && .venv/bin/pytest tests/test_dashboard_fields.py -q` → FAIL (`Test` has no `title`).

- [ ] **Step 3: implement**

`shared/schemas/test.schema.json`, add to `properties`:
```json
    "error": { "type": "string" },
    "title": {
      "type": "string",
      "maxLength": 81,
      "description": "Per la dashboard: nome del prototipo o inizio del primo post. Lo calcola il backend."
    },
    "created_by": {
      "type": "string",
      "maxLength": 60,
      "description": "Nome locale di chi ha lanciato il test. Non è un account."
    }
```
(81 = 80 characters plus the «…».)

`backend/app/models.py`, in `class Test` after `error`:
```python
    error: str | None = None
    title: str | None = Field(default=None, max_length=81)
    created_by: str | None = Field(default=None, max_length=60)
```

`backend/app/store.py`:
- in `_SCHEMA`, the `tests` table gets `title TEXT, created_by TEXT` after `error TEXT`;
- after `_SCHEMA` add the migration and use it in `init_db`:
```python
# Database creati prima della dashboard: le colonne nuove si aggiungono senza perdere i test.
_ADDED_COLUMNS = ("title", "created_by")


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(tests)")}
        for column in _ADDED_COLUMNS:
            if column not in existing:
                conn.execute(f"ALTER TABLE tests ADD COLUMN {column} TEXT")
```
- `_insert`:
```python
    conn.execute(
        "INSERT INTO tests (id, kind, status, created_at, done_count, total_count, stimuli, error,"
        " title, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            test.id,
            test.kind,
            test.status,
            test.created_at,
            test.done_count,
            test.total_count,
            stimuli,
            test.error,
            test.title,
            test.created_by,
        ),
    )
```
`_to_test` already passes every column; `None` columns validate as `None`.

- [ ] **Step 4:** `.venv/bin/pytest -q` → all pass.
- [ ] **Step 5: commit** `git add shared/schemas/test.schema.json backend && git commit -m "feat: store title and author of each test"`

---

### Task 2: title computed at creation, `created_by` from the request

**Files:** Modify `backend/app/models.py`, `backend/app/api/create_request.py`, `backend/app/api/tests.py`. Test: `backend/tests/test_dashboard_fields.py`.

- [ ] **Step 1: failing tests** (append)

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_title_is_the_first_line_cut_at_80() -> None:
    body = {
        "kind": "post",
        "variants": [{"label": "A", "text": "x" * 100 + "\nseconda riga"}],
        "created_by": "  Fabio  ",
    }
    created = client.post("/tests", json=body).json()
    assert created["title"] == "x" * 80 + "…"
    assert created["created_by"] == "Fabio"


def test_blank_author_is_omitted() -> None:
    body = {"kind": "post", "variants": [{"label": "A", "text": "Breve"}], "created_by": " "}
    created = client.post("/tests", json=body).json()
    assert created["title"] == "Breve"
    assert "created_by" not in created


def test_author_arrives_with_the_form_too() -> None:
    form = {"kind": "post", "variants[0][label]": "A", "variants[0][text]": "Ciao", "created_by": "Salvo"}
    created = client.post("/tests", data=form).json()
    assert created["created_by"] == "Salvo"
```
And for the prototype title, in `backend/tests/test_prototype_import.py` add to the existing test `test_prototype_test_uses_the_chosen_screens_and_runs_on_the_panel`, after `created = ...`:
```python
    assert created.json()["title"] == prototype_name
```
where `prototype_name` is the `name` used by that test's imported prototype (read it from the fixture used there and inline the literal).

- [ ] **Step 2:** `.venv/bin/pytest tests/test_dashboard_fields.py -q` → FAIL.

- [ ] **Step 3: implement**

`backend/app/models.py`: add to both `PostTestRequest` and `PrototypeTestRequest`:
```python
    created_by: str | None = Field(default=None, max_length=60)
```

`backend/app/api/create_request.py`, in the multipart branch:
```python
    body = _validate(
        {
            "kind": form.get("kind"),
            "variants": [{"label": v.get("label"), "text": v.get("text")} for v in variants],
            "created_by": form.get("created_by"),
        }
    )
```

`backend/app/api/tests.py`:
```python
_TITLE_MAX = 80


def _title(body: CreateTestRequest, stimuli: list[Stimulus]) -> str | None:
    """Per la dashboard: il nome del prototipo o la prima riga del primo post."""
    if isinstance(body, PostTestRequest):
        text = (stimuli[0].text or "").strip().splitlines()[0] if stimuli[0].text else ""
    else:
        prototype = store.get_prototype(body.prototype_id) if body.prototype_id else None
        text = prototype.name if prototype else ", ".join(body.flow_ids or [])
    text = text.strip()
    if not text:
        return None
    return text if len(text) <= _TITLE_MAX else text[:_TITLE_MAX] + "…"
```
In `_build_test`, add to the `Test(...)` call:
```python
        title=_title(body, stimuli),
        created_by=(body.created_by or "").strip() or None,
```

- [ ] **Step 4:** `.venv/bin/pytest -q && .venv/bin/ruff check . && .venv/bin/ruff format --check .` → all pass.
- [ ] **Step 5: commit** `git commit -am "feat: title and author on new tests"`

---

### Task 3: saved reports

**Files:** Modify `backend/app/store.py`, `backend/app/api/reports.py`. Test: `backend/tests/test_saved_reports.py`.

- [ ] **Step 1: failing tests**

```python
# backend/tests/test_saved_reports.py
from fastapi.testclient import TestClient

from app.api import reports
from app.main import app
from app.models import Fidelity

client = TestClient(app)
BODY = {"kind": "post", "variants": [{"label": "A", "text": "Uno."}, {"label": "B", "text": "Due."}]}


def test_report_is_saved_and_read_back_after_a_restart(monkeypatch) -> None:
    created = client.post("/tests", json=BODY).json()
    first = client.get(f"/tests/{created['id']}/report").json()
    reports._REPORTS.clear()  # come dopo un riavvio
    monkeypatch.setattr(reports, "build_report", _must_not_build)
    assert client.get(f"/tests/{created['id']}/report").json() == first


def test_fidelity_is_added_when_reading_a_saved_report(monkeypatch) -> None:
    created = client.post("/tests", json=BODY).json()
    assert "fidelity" not in client.get(f"/tests/{created['id']}/report").json()
    reports._REPORTS.clear()
    monkeypatch.setattr(reports, "load_fidelity", lambda: Fidelity(score=0.4, basis="57 post"))
    report = client.get(f"/tests/{created['id']}/report").json()
    assert report["fidelity"] == {"score": 0.4, "basis": "57 post"}


async def _must_not_build(*args, **kwargs):
    raise AssertionError("il report salvato non va rigenerato")
```
If `Fidelity` is not the model name in `app/models.py`, use the one that `Report.fidelity` is typed with.

- [ ] **Step 2:** `.venv/bin/pytest tests/test_saved_reports.py -q` → FAIL (the second read rebuilds).

- [ ] **Step 3: implement**

`backend/app/store.py`: in `_SCHEMA` add
```sql
CREATE TABLE IF NOT EXISTS reports (
    test_id TEXT PRIMARY KEY,
    report TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```
and the functions (import `Report` from `app.models`, `datetime`/`UTC` from `datetime`):
```python
def save_report(report: Report) -> None:
    """Il report senza fidelity: la calibrazione si aggiunge a ogni lettura."""
    data = report.model_copy(update={"fidelity": None}).model_dump_json(exclude_none=True)
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO reports (test_id, report, created_at) VALUES (?, ?, ?)",
            (report.test_id, data, datetime.now(UTC).isoformat()),
        )


def load_report(test_id: str) -> Report | None:
    with _connect() as conn:
        row = conn.execute("SELECT report FROM reports WHERE test_id = ?", (test_id,)).fetchone()
    return None if row is None else Report.model_validate_json(row["report"])
```

`backend/app/api/reports.py`: replace `_report_for` so it reads the store first, builds without fidelity, saves, and adds fidelity on the way out:
```python
async def _build_and_save(test: Test) -> Report:
    report = await build_report(
        test.id, test.stimuli, store.list_responses(test.id), build_summarizer(), None
    )
    store.save_report(report)
    return report


async def _report_for(test: Test) -> Report:
    """Il report salvato, oppure una sola costruzione per test anche con richieste simultanee."""
    report = store.load_report(test.id)
    if report is None:
        task = _REPORTS.get(test.id)
        if task is None:
            task = asyncio.create_task(_build_and_save(test))
            _REPORTS[test.id] = task
        try:
            report = await asyncio.shield(task)
        finally:
            # Un fallimento non resta in cache: la richiesta successiva riprova.
            if task.done() and (task.cancelled() or task.exception() is not None):
                _REPORTS.pop(test.id, None)
    # La calibrazione è sui post pubblicati: per un prototipo manca e il report lo dice.
    fidelity = load_fidelity() if test.kind == "post" else None
    return report.model_copy(update={"fidelity": fidelity})
```
Update the `# shortcut:` comment above `_REPORTS` to: `# Solo per non costruire due volte lo stesso report: quelli finiti stanno nello store.` Check `build_report`'s fifth parameter name in `app/report/builder.py` and pass `None` the same way the old code passed `load_fidelity()`.

- [ ] **Step 4:** `.venv/bin/pytest -q && .venv/bin/ruff check . && .venv/bin/ruff format --check .` → all pass.
- [ ] **Step 5: commit** `git commit -am "feat: save each report so it survives restarts"`

---

### Task 4: regenerated types and the hash router

**Files:** `frontend/src/types/*` (generated), create `frontend/src/lib/route.ts` and `route.test.ts`.

- [ ] **Step 1:** `cd frontend && npm run gen:types` → `src/types/test.ts` now has `title?` and `created_by?`. `git diff --stat src/types` shows only test-related files.

- [ ] **Step 2: failing test**

```ts
// frontend/src/lib/route.test.ts
import { describe, expect, it } from "vitest";
import { parseRoute, routeHref } from "./route";

describe("parseRoute", () => {
  it("reads every page", () => {
    expect(parseRoute("")).toEqual({ page: "dashboard" });
    expect(parseRoute("#/")).toEqual({ page: "dashboard" });
    expect(parseRoute("#/panel")).toEqual({ page: "panel" });
    expect(parseRoute("#/test/nuovo")).toEqual({ page: "new-test" });
    expect(parseRoute("#/test/abc123")).toEqual({ page: "test", id: "abc123" });
  });
  it("sends unknown addresses to the dashboard", () => {
    expect(parseRoute("#/report")).toEqual({ page: "dashboard" });
    expect(parseRoute("#/test/")).toEqual({ page: "dashboard" });
  });
  it("round-trips", () => {
    expect(parseRoute(routeHref({ page: "test", id: "t9" }))).toEqual({ page: "test", id: "t9" });
  });
});
```

- [ ] **Step 3:** `npx vitest run src/lib/route.test.ts` → FAIL.

- [ ] **Step 4: implement**

```ts
// frontend/src/lib/route.ts
import { useEffect, useState } from "react";

export type Route =
  | { page: "dashboard" }
  | { page: "panel" }
  | { page: "new-test" }
  | { page: "test"; id: string };

export function parseRoute(hash: string): Route {
  const path = hash.replace(/^#/, "");
  if (path === "/panel") return { page: "panel" };
  if (path === "/test/nuovo") return { page: "new-test" };
  const test = /^\/test\/([\w-]+)$/.exec(path);
  return test ? { page: "test", id: test[1] } : { page: "dashboard" };
}

export function routeHref(route: Route): string {
  switch (route.page) {
    case "panel":
      return "#/panel";
    case "new-test":
      return "#/test/nuovo";
    case "test":
      return `#/test/${route.id}`;
    default:
      return "#/";
  }
}

export const go = (route: Route) => {
  window.location.hash = routeHref(route);
};

/** The current page; follows the back button and links. */
export function useRoute(): Route {
  const [route, setRoute] = useState(() => parseRoute(window.location.hash));
  useEffect(() => {
    const onChange = () => {
      setRoute(parseRoute(window.location.hash));
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
```

- [ ] **Step 5:** `npx vitest run src/lib/route.test.ts` → PASS. Commit: `git add src/types src/lib/route.ts src/lib/route.test.ts && git commit -m "feat: hash routes for dashboard, panel and tests"`

---

### Task 5: local name, title fallback, date format, API and mocks

**Files:** create `frontend/src/lib/userName.ts`, `frontend/src/lib/format.ts`, `format.test.ts`; modify `frontend/src/api/index.ts`, `frontend/src/api/mock.ts`.

- [ ] **Step 1: failing test**

```ts
// frontend/src/lib/format.test.ts
import { describe, expect, it } from "vitest";
import { formatWhen, testTitle } from "./format";

describe("formatWhen", () => {
  it("writes day, short month and time", () => {
    expect(formatWhen("2026-11-25T14:32:00")).toBe("25 nov, 14:32");
  });
});

describe("testTitle", () => {
  it("falls back when the test has no title", () => {
    expect(testTitle({ title: "Caso cliente" })).toBe("Caso cliente");
    expect(testTitle({})).toBe("Senza titolo");
  });
});
```

- [ ] **Step 2:** `npx vitest run src/lib/format.test.ts` → FAIL.

- [ ] **Step 3: implement**

```ts
// frontend/src/lib/format.ts
import type { Test } from "../types/test";

const WHEN = new Intl.DateTimeFormat("it-IT", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

/** "25 nov, 14:32", in local time. */
export const formatWhen = (iso: string) => WHEN.format(new Date(iso)).replace(/\.?,? (?=\d{2}:)/, ", ");

// Tests saved before the dashboard have no title.
export const testTitle = (test: Pick<Test, "title">) => test.title || "Senza titolo";
```
(If the `Intl` output on Node differs, adjust only the `replace` so the test passes; keep the visible format "25 nov, 14:32".)

```ts
// frontend/src/lib/userName.ts
const KEY = "eco.name";
let fallback = ""; // when localStorage is blocked, the name lasts for the session

export function getUserName(): string {
  try {
    return localStorage.getItem(KEY) ?? fallback;
  } catch {
    return fallback;
  }
}

export function setUserName(name: string) {
  fallback = name.trim();
  try {
    localStorage.setItem(KEY, fallback);
  } catch {
    // blocked storage: the session fallback is enough
  }
}
```

`frontend/src/api/index.ts`: import `getUserName`; in `startPostTest` add `form.append("created_by", getUserName());` after `kind`; `startPrototypeTest` body becomes `{ kind: "prototype", prototype_id: prototypeId, paths, task, created_by: getUserName() }` (keep the existing `task` argument as it is today).

`frontend/src/api/mock.ts`:
- `start(kind, stimuli, title)` sets `title` and `created_by: getUserName() || undefined` on the new test;
- `startPostTest` passes `variants[0].text.split("\n")[0].slice(0, 80)`;
- `startPrototypeTest` passes `prototypes.get(prototypeId)?.name`;
- the seeded `t1` gets `title: "Tre settimane per un preventivo: come le abbiamo ridotte a due giorni"` and `created_by: "Fabio"`, and a second seeded done prototype test `t0` (created `2026-10-10T09:00:00Z`, kind `prototype`, two `prototype_screen` stimuli with `flow_id: "s1"`, `screen_index` 0 and 1, `title: "Onboarding cliente v3"`, `created_by: "Salvo"`, `done_count`/`total_count` = 2 × `mockPersonas.length`). `getReport` already returns `mockPrototypeReport` for prototype tests.

- [ ] **Step 4:** `npm run typecheck && npm test` → all pass.
- [ ] **Step 5: commit** `git add -A src && git commit -m "feat: local user name sent with each test"`

---

### Task 6: DS `Sidebar` and `TestRow`

**Files:** create `frontend/src/ds/components/navigation/Sidebar.tsx`, `frontend/src/ds/components/test/TestRow.tsx`; modify `frontend/src/ds/components.css`, `frontend/src/ds/index.ts`.

- [ ] **Step 1: implement `Sidebar`**

```tsx
// frontend/src/ds/components/navigation/Sidebar.tsx
import { Logo } from "../brand/Logo";

export type SidebarItem = { key: string; label: string; href: string };

export type SidebarProps = {
  items: SidebarItem[];
  current?: string;
  user?: string;
  onChangeUser?: () => void;
};

export function Sidebar({ items, current, user, onChangeUser }: SidebarProps) {
  return (
    <nav className="eco-side" aria-label="Navigazione eco">
      <div className="eco-brand">
        <Logo />
        <span className="eco-brand__sep" aria-hidden="true" />
        <span className="eco-brand__eco">eco</span>
      </div>
      <ul className="eco-side__items">
        {items.map((it) => (
          <li key={it.key}>
            <a className="eco-side__item" href={it.href} aria-current={it.key === current ? "page" : undefined}>
              {it.label}
            </a>
          </li>
        ))}
      </ul>
      {user && (
        <div className="eco-side__user">
          <span>{user}</span>
          {onChangeUser && (
            <button type="button" className="eco-side__change" onClick={onChangeUser}>
              Cambia
            </button>
          )}
        </div>
      )}
    </nav>
  );
}
```

- [ ] **Step 2: implement `TestRow`**

```tsx
// frontend/src/ds/components/test/TestRow.tsx
import { Icon } from "../icons/Icon";

export type TestRowProps = {
  href: string;
  kind: "post" | "prototype";
  title: string;
  detail: string; // "2 varianti" · "5 schermate"
  when: string;
  by?: string;
  status: "running" | "done" | "error";
  percent?: number;
};

const STATUS = { done: "Completato", error: "Interrotto" } as const;

export function TestRow({ href, kind, title, detail, when, by, status, percent = 0 }: TestRowProps) {
  return (
    <a className="eco-testrow" href={href}>
      <span className="eco-testrow__kind" aria-label={kind === "post" ? "Post LinkedIn" : "Prototipo"}>
        <Icon name={kind === "post" ? "linkedin" : "phone"} />
      </span>
      <span className="eco-testrow__main">
        <b>{title}</b>
        <span>{[detail, when, by].filter(Boolean).join(" · ")}</span>
      </span>
      <span className={`eco-testrow__status eco-testrow__status--${status}`}>
        {status === "running" ? `In corso · ${percent}%` : STATUS[status]}
      </span>
    </a>
  );
}
```
Check the real path and export name of `Icon` in `ds/index.ts` and adjust the import.

- [ ] **Step 3: CSS** — append to `frontend/src/ds/components.css`:
```css
.eco-screen--side{display:grid;grid-template-columns:240px 1fr;min-height:80vh}
.eco-side{display:flex;flex-direction:column;gap:28px;padding:24px 18px;border-right:2px solid var(--lilac);background:var(--white)}
.eco-side .eco-brand{margin:0 0 4px 6px}
.eco-side__items{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}
.eco-side__item{display:block;padding:10px 14px;border-radius:var(--r-chip);font:800 16px/1.2 var(--font-text);color:var(--muted);text-decoration:none;border:2px solid transparent}
.eco-side__item:hover{color:var(--violet)}
.eco-side__item[aria-current=page]{color:var(--violet);background:var(--mist);border-color:var(--line)}
.eco-side__item:focus-visible,.eco-side__change:focus-visible,.eco-testrow:focus-visible{outline:var(--ring-focus);outline-offset:var(--ring-offset)}
.eco-side__user{margin-top:auto;display:flex;align-items:center;justify-content:space-between;gap:8px;font:700 14px/1.2 var(--font-text);color:var(--night)}
.eco-side__change{background:none;border:0;padding:4px;font:800 13px/1 var(--font-text);color:var(--violet);cursor:pointer}
.eco-testlist{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:12px}
.eco-testrow{display:flex;align-items:center;gap:16px;padding:16px 20px;border-radius:var(--r-card);border:2px solid var(--line);background:var(--white);box-shadow:var(--shadow-light-sm);text-decoration:none;color:var(--night)}
.eco-testrow:hover{border-color:var(--violet)}
.eco-testrow__kind{width:44px;height:44px;flex:none;display:grid;place-items:center;border-radius:var(--r-chip);background:var(--mist);color:var(--violet)}
.eco-testrow__main{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px}
.eco-testrow__main b{font:800 17px/1.25 var(--font-text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.eco-testrow__main span{font:600 14px/1.3 var(--font-text);color:var(--muted)}
.eco-testrow__status{flex:none;padding:6px 12px;border-radius:var(--r-pill);font:800 13px/1 var(--font-text);background:var(--mist);color:var(--night)}
.eco-testrow__status--running{background:var(--violet);color:var(--white)}
.eco-testrow__status--error{background:var(--warm-soft);color:var(--warm-ink)}
@media (max-width:760px){.eco-screen--side{grid-template-columns:1fr}.eco-side{flex-direction:row;flex-wrap:wrap;align-items:center;gap:12px;padding:12px 16px;border-right:0;border-bottom:2px solid var(--lilac)}.eco-side__items{flex-direction:row}.eco-side__user{margin:0 0 0 auto}.eco-testrow{flex-wrap:wrap}}
```
Use only tokens that exist in `ds/tokens.css` (`grep -o "\-\-[a-z-]*" src/ds/tokens.css | sort -u`); replace any missing one with its closest existing token.

- [ ] **Step 4: exports** — in `frontend/src/ds/index.ts` add
```ts
export { Sidebar, type SidebarProps } from "./components/navigation/Sidebar";
export { TestRow, type TestRowProps } from "./components/test/TestRow";
```
- [ ] **Step 5:** `npm run lint && npm run typecheck` → clean. Commit: `git commit -am "feat(ds): sidebar and test row"` (add the new files first).

---

### Task 7: `ReportScreen` takes the loaded test

**Files:** Modify `frontend/src/screens/ReportScreen.tsx`.

- [ ] **Step 1:** change the props and loading:
```tsx
type Props = { test: Test };

export default function ReportScreen({ test }: Props) {
  const [attempt, setAttempt] = useState(0);
  const [filter, setFilter] = useState<Filter>("all");
  const personas = useLoad(getPersonas, [attempt]);
  const report = useLoad(() => getReport(test.id), [test.id, attempt]);
```
- delete `tests`, `selected` and the `getTests` import; import `type { Test } from "../types/test"`;
- `const error = personas.error ?? report.error;`
- delete the `if (tests.data && !test)` EmptyState branch and the `EmptyState` import if unused;
- the loading guard becomes `if (!report.data || !personas.data)`;
- the rest is unchanged (it already uses `test.kind`, `test.stimuli`).
- [ ] **Step 2:** `npm run typecheck` will fail in `App.tsx` until Task 9; that is expected. Do not commit yet: continue to Task 8.

---

### Task 8: `NewTestScreen` and `TestPage`

**Files:** `git mv frontend/src/screens/TestScreen.tsx frontend/src/screens/NewTestScreen.tsx`; create `frontend/src/screens/TestPage.tsx`.

- [ ] **Step 1: `NewTestScreen` = the form only.** In the renamed file:
- `type Props = { onStarted: (testId: string) => void };` and `export default function NewTestScreen({ onStarted }: Props)`;
- remove the state `test`, `pollError`, `responses`, `readAttempt`, `shownTest`, both `useEffect`s, the whole `if (test) { … }` block, `joinLabels`, `POLL_MS`, and the imports only they used (`getResponses`, `getTest`, `Card`, `TestProgress`, `LiveResults`, `useEffect`, `Response`);
- in `start`, replace `setTest(...)` with:
```tsx
      const test = mode === "post" || !proto ? await startPostTest(variants) : await startPrototypeTest(proto.id, proto.paths, proto.task);
      onStarted(test.id);
```
and in `catch` drop `setTest(null)`.

- [ ] **Step 2: `TestPage`**

```tsx
// frontend/src/screens/TestPage.tsx
import { useEffect, useRef, useState } from "react";
import { getPersonas, getResponses, getTest } from "../api";
import { Alert, Button, Card, Icon, Skeleton, TestProgress } from "../ds";
import { routeHref } from "../lib/route";
import { useLoad } from "../lib/useLoad";
import type { Response } from "../types/response";
import type { Test } from "../types/test";
import LiveResults from "./LiveResults";
import ReportScreen from "./ReportScreen";

const POLL_MS = 1500;
const message = (e: unknown) => (e instanceof Error && e.message ? e.message : "Errore imprevisto.");

// "A, B e C"
const joinLabels = (labels: string[]) => labels.join(", ").replace(/, ([^,]*)$/, " e $1");

/** One test: progress and live answers while it runs, its report when done. */
export default function TestPage({ id }: { id: string }) {
  const [test, setTest] = useState<Test | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [responses, setResponses] = useState<Response[]>([]);
  const personas = useLoad(getPersonas, []);

  // First read, again on "Riprova" or when the address changes to another test.
  useEffect(() => {
    let alive = true;
    setError(null);
    getTest(id).then(
      (t) => alive && setTest(t),
      (e: unknown) => alive && setError(message(e)),
    );
    return () => {
      alive = false;
    };
  }, [id, attempt]);

  // Each new state schedules the next poll until the test ends.
  useEffect(() => {
    if (!test || test.id !== id || test.status === "done" || test.status === "error") return;
    const timer = setTimeout(() => getTest(id).then(setTest, (e: unknown) => setError(message(e))), POLL_MS);
    return () => clearTimeout(timer);
  }, [test, id]);

  // Answers follow the progress: one read each time done_count changes.
  const doneCount = test?.id === id ? test.done_count : 0;
  const shown = useRef(id);
  shown.current = id;
  useEffect(() => {
    if (doneCount === 0) return setResponses([]);
    getResponses(id).then(
      (r) => shown.current === id && setResponses((prev) => (r.length >= prev.length ? r : prev)),
      (e: unknown) => setError(message(e)),
    );
  }, [id, doneCount, attempt]);

  const retry = (
    <Button variant="light" icon={<Icon name="refresh" />} onClick={() => setAttempt((n) => n + 1)}>
      Riprova
    </Button>
  );

  if (!test || test.id !== id)
    return error ? (
      <Alert tone="offline" title="Non riusciamo a caricare il test." action={retry}>
        {error}
      </Alert>
    ) : (
      <div role="status" aria-label="Caricamento del test" className="scr-stack">
        <Skeleton shape="title" width={320} height={48} />
        <Skeleton shape="block" height={160} />
      </div>
    );

  if (test.status === "done") return <ReportScreen test={test} />;

  const personasInTest = test.stimuli.length ? test.total_count / test.stimuli.length : 0;
  const pathCount = new Set(test.stimuli.map((s) => s.flow_id)).size;
  const subject =
    test.kind === "prototype"
      ? `${pathCount === 1 ? "1 percorso" : `${pathCount} percorsi`} · prototipo`
      : test.stimuli.length === 1
        ? "Un post LinkedIn"
        : `${joinLabels(test.stimuli.map((s) => s.variant_label ?? s.id))} · post LinkedIn`;

  return (
    <>
      <div className="eco-head">
        <div>
          <h1>{test.status === "error" ? "Test interrotto" : "Test in corso"}</h1>
          <p className="eco-sub">
            {subject} · {personasInTest} personas
          </p>
        </div>
      </div>
      <Card pad="lg" style={{ marginBottom: 20 }}>
        <TestProgress
          done={test.done_count}
          total={test.total_count}
          personas={personasInTest}
          status={test.status === "error" ? "error" : "running"}
        />
      </Card>
      {error ? (
        <Alert tone="offline" title="Non riusciamo a leggere l'avanzamento." action={retry}>
          {error}
        </Alert>
      ) : test.status === "error" ? (
        <Alert
          title="Il test si è interrotto."
          action={
            <Button variant="light" onClick={() => (window.location.hash = routeHref({ page: "new-test" }))}>
              Nuovo test
            </Button>
          }
        >
          {test.error ?? "Errore imprevisto."}
        </Alert>
      ) : (
        <Alert tone="busy" title="Puoi chiudere la pagina.">
          Il test continua anche senza di te: lo ritrovi nella dashboard, con il report quando è finito.
        </Alert>
      )}
      {responses.length > 0 && (
        <LiveResults
          stimuli={test.stimuli}
          responses={responses}
          personas={personas.data ?? []}
          status={test.status === "error" ? "error" : "running"}
        />
      )}
    </>
  );
}
```
Note: when the test ends the page switches straight to the report (its skeleton covers the 2–3 minutes of the summary), so there is no "Vedi il report" button any more.

Proceed to Task 9 before running checks.

---

### Task 9: Dashboard, first-run name, App wiring

**Files:** create `frontend/src/screens/DashboardScreen.tsx`, `frontend/src/screens/NameScreen.tsx`; modify `frontend/src/App.tsx`.

- [ ] **Step 1: `DashboardScreen`**

```tsx
// frontend/src/screens/DashboardScreen.tsx
import { useState } from "react";
import { getTests } from "../api";
import { Alert, Button, EmptyState, Icon, Skeleton, TestRow } from "../ds";
import { formatWhen, testTitle } from "../lib/format";
import { go, routeHref } from "../lib/route";
import { useLoad } from "../lib/useLoad";
import type { Test } from "../types/test";

const detail = (t: Test) => {
  if (t.kind === "post") return t.stimuli.length === 1 ? "1 post" : `${t.stimuli.length} varianti`;
  return t.stimuli.length === 1 ? "1 schermata" : `${t.stimuli.length} schermate`;
};

export default function DashboardScreen() {
  const [attempt, setAttempt] = useState(0);
  const tests = useLoad(getTests, [attempt]);
  const newTest = (
    <Button icon={<Icon name="plus" />} onClick={() => go({ page: "new-test" })}>
      Nuovo test
    </Button>
  );

  return (
    <>
      <div className="eco-head">
        <div>
          <h1>I tuoi test</h1>
          <p className="eco-sub">Post e prototipi provati sul panel, dal più recente</p>
        </div>
        {newTest}
      </div>
      {tests.error ? (
        <Alert
          tone="offline"
          title="Non riusciamo a caricare i test."
          action={
            <Button variant="light" icon={<Icon name="refresh" />} onClick={() => setAttempt((n) => n + 1)}>
              Riprova
            </Button>
          }
        >
          {tests.error}
        </Alert>
      ) : !tests.data ? (
        <div role="status" aria-label="Caricamento dei test" className="scr-stack">
          <Skeleton shape="block" height={76} />
          <Skeleton shape="block" height={76} />
        </div>
      ) : tests.data.length === 0 ? (
        <EmptyState title="Nessun test ancora" action={newTest}>
          Lancia il primo: un post, fino a 5 varianti da confrontare, oppure un prototipo.
        </EmptyState>
      ) : (
        <ul className="eco-testlist">
          {tests.data.map((t) => (
            <li key={t.id}>
              <TestRow
                href={routeHref({ page: "test", id: t.id })}
                kind={t.kind}
                title={testTitle(t)}
                detail={detail(t)}
                when={formatWhen(t.created_at)}
                by={t.created_by}
                status={t.status === "done" || t.status === "error" ? t.status : "running"}
                percent={t.total_count ? Math.round((t.done_count / t.total_count) * 100) : 0}
              />
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
```
If the DS has no `plus` icon (`ICON_NAMES` in `ds/components/icons`), drop the `icon` prop.

- [ ] **Step 2: `NameScreen`**

```tsx
// frontend/src/screens/NameScreen.tsx
import { useState } from "react";
import { Button, Card, FieldError } from "../ds";

type Props = { initial?: string; onDone: (name: string) => void };

/** First run, or "Cambia" in the sidebar: a name saved with each test. Not an account. */
export default function NameScreen({ initial = "", onDone }: Props) {
  const [name, setName] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  const submit = () => (name.trim() ? onDone(name.trim().slice(0, 60)) : setError("Scrivi un nome, anche solo il tuo."));

  return (
    <Card pad="lg" style={{ maxWidth: 520, margin: "40px auto" }}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <h1 style={{ fontSize: 32 }}>Come ti chiami?</h1>
        <p className="eco-sub">Lo salviamo con ogni test che lanci, così nella dashboard si vede chi l'ha fatto.</p>
        <label className="scr-pt-label" htmlFor="eco-name">
          Nome
        </label>
        <input
          id="eco-name"
          className="scr-pt-input"
          value={name}
          maxLength={60}
          autoFocus
          onChange={(e) => {
            setName(e.target.value);
            setError(null);
          }}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? "eco-name-err" : undefined}
        />
        {error && <FieldError id="eco-name-err">{error}</FieldError>}
        <div style={{ marginTop: 20 }}>
          <Button type="submit">Continua</Button>
        </div>
      </form>
    </Card>
  );
}
```
Check that `Button` forwards `type`; if not, use `onClick={submit}`.

- [ ] **Step 3: `App`**

```tsx
// frontend/src/App.tsx
import { useState } from "react";
import { Screen, Sidebar } from "./ds";
import { getUserName, setUserName } from "./lib/userName";
import { go, useRoute } from "./lib/route";
import DashboardScreen from "./screens/DashboardScreen";
import NameScreen from "./screens/NameScreen";
import NewTestScreen from "./screens/NewTestScreen";
import PanelScreen from "./screens/PanelScreen";
import TestPage from "./screens/TestPage";
import "./screens/screens.css";

const ITEMS = [
  { key: "dashboard", label: "Dashboard", href: "#/" },
  { key: "panel", label: "Panel", href: "#/panel" },
];

export default function App() {
  const route = useRoute();
  const [name, setName] = useState(getUserName);
  const [editingName, setEditingName] = useState(false);
  const saveName = (n: string) => {
    setUserName(n);
    setName(n);
    setEditingName(false);
  };

  return (
    <div className="scr-app">
      <Screen
        className="eco-screen--side"
        nav={
          <Sidebar
            items={ITEMS}
            current={route.page === "panel" ? "panel" : "dashboard"}
            user={name || undefined}
            onChangeUser={() => setEditingName(true)}
          />
        }
      >
        {!name || editingName ? (
          <NameScreen initial={name} onDone={saveName} />
        ) : route.page === "panel" ? (
          <PanelScreen />
        ) : route.page === "new-test" ? (
          <NewTestScreen onStarted={(id) => go({ page: "test", id })} />
        ) : route.page === "test" ? (
          <TestPage key={route.id} id={route.id} />
        ) : (
          <DashboardScreen />
        )}
      </Screen>
    </div>
  );
}
```
Check `Screen` renders `nav` as a sibling of the body so the grid in `.eco-screen--side` gets two columns; if it wraps the body differently, adapt the CSS selector, not the component.

- [ ] **Step 4:** `npm run lint && npm run typecheck && npm test && npm run build` → all pass. Fix unused imports/exports reported by lint (e.g. `AppNav` stays exported from the DS, unused by the app — fine).
- [ ] **Step 5: commit** `git add -A src && git commit -m "feat: dashboard home, test page with its report, sidebar"`

---

### Task 10: docs and visual check

**Files:** `CLAUDE.md`, `docs/contratti-backend.md`.

- [ ] **Step 1:** `CLAUDE.md`, section Frontend, replace «Tre schermate: Panel, Test, Report. Niente altro senza accordo.» with:
  «Pagine: Dashboard (i test fatti e "Nuovo test"), Panel, Nuovo test e la pagina del singolo test, che a test finito mostra il suo report. Niente altro senza accordo.»
- [ ] **Step 2:** `docs/contratti-backend.md`: add row 9 «✅ Dashboard: `title` e `created_by` nel test, report salvati» and a short section 9 that lists: the two optional fields, how `title` is computed, `created_by` in JSON and form, the `reports` table, fidelity added at read.
- [ ] **Step 3: visual check with mocks.** `cd frontend && npx vite --port 5174 --strictPort` (5173 is Fabio's). With the backend venv's Playwright Chromium, take screenshots of: first run (name), dashboard with the two seeded tests, `#/test/t1` (post report), `#/test/t0` (prototype report), a new post test running then its report, reload on `#/test/<id>`, back button to the dashboard, width 390 px. Save to the scratchpad and send them to Fabio for approval **before** opening the PR.
- [ ] **Step 4: commit** `git commit -am "docs: pages and contract for the dashboard"`.
- [ ] **Step 5:** after Fabio approves: push and open the PR; mention to Salvo the two schema fields and the `reports` table.

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.config import settings
from app.models import Stimulus, Test

INTERRUPTED_MESSAGE = "Il server è stato riavviato durante il test"
_ACTIVE_STATUSES = ("queued", "running")
_UPDATABLE_COLUMNS = {"status", "done_count", "error"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tests (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    done_count INTEGER NOT NULL,
    total_count INTEGER NOT NULL,
    stimuli TEXT NOT NULL,
    error TEXT
);
CREATE TABLE IF NOT EXISTS responses (
    test_id TEXT NOT NULL,
    persona_id TEXT NOT NULL,
    stimulus_id TEXT NOT NULL,
    response TEXT NOT NULL,
    PRIMARY KEY (test_id, persona_id, stimulus_id)
);
"""


# Una connessione per operazione: sicuro con i task in background.
@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.database_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)


def _insert(conn: sqlite3.Connection, test: Test) -> None:
    stimuli = json.dumps([s.model_dump(mode="json") for s in test.stimuli])
    conn.execute(
        "INSERT INTO tests (id, kind, status, created_at, done_count, total_count, stimuli, error)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            test.id,
            test.kind,
            test.status,
            test.created_at,
            test.done_count,
            test.total_count,
            stimuli,
            test.error,
        ),
    )


def _to_test(row: sqlite3.Row) -> Test:
    return Test.model_validate(
        {**dict(row), "stimuli": [Stimulus.model_validate(s) for s in json.loads(row["stimuli"])]}
    )


def add_if_idle(test: Test) -> bool:
    """Inserisce il test solo se non ce ne sono di attivi, in una transazione atomica."""
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        busy = conn.execute(
            "SELECT 1 FROM tests WHERE status IN (?, ?) LIMIT 1", _ACTIVE_STATUSES
        ).fetchone()
        if busy is None:
            _insert(conn, test)
        conn.execute("ROLLBACK" if busy is not None else "COMMIT")
        return busy is None


def get(test_id: str) -> Test | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM tests WHERE id = ?", (test_id,)).fetchone()
    return None if row is None else _to_test(row)


def list_most_recent_first() -> list[Test]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM tests ORDER BY rowid DESC").fetchall()
    return [_to_test(row) for row in rows]


def update(test_id: str, **changes: object) -> Test:
    unknown = set(changes) - _UPDATABLE_COLUMNS
    if unknown:
        raise ValueError(f"Colonne non modificabili: {', '.join(sorted(unknown))}")
    assignments = ", ".join(f"{column} = ?" for column in changes)
    with _connect() as conn:
        conn.execute(f"UPDATE tests SET {assignments} WHERE id = ?", (*changes.values(), test_id))
    test = get(test_id)
    if test is None:
        raise KeyError(test_id)
    return test


def mark_interrupted() -> None:
    """Un test ancora attivo all'avvio non ha più un task che lo porti a termine."""
    with _connect() as conn:
        conn.execute(
            "UPDATE tests SET status = 'error', error = ? WHERE status IN (?, ?)",
            (INTERRUPTED_MESSAGE, *_ACTIVE_STATUSES),
        )

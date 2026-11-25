from fastapi.testclient import TestClient

from app import store
from app.main import app
from app.models import Stimulus
from app.models import Test as TestModel

client = TestClient(app)


def _test(**extra) -> TestModel:
    return TestModel(
        id="t1",
        kind="post",
        status="queued",
        created_at="2026-11-25T10:00:00+00:00",
        done_count=0,
        total_count=1,
        stimuli=[Stimulus(id="variante-a", kind="post", variant_label="A", text="Ciao")],
        **extra,
    )


def test_title_survives_the_store(validate) -> None:
    assert store.add_if_idle(_test(title="Ciao"))
    saved = store.get("t1")
    assert saved.title == "Ciao"
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


def test_post_title_is_the_first_line_cut_at_80() -> None:
    body = {
        "kind": "post",
        "variants": [{"label": "A", "text": "x" * 100 + "\nseconda riga"}],
    }
    created = client.post("/tests", json=body).json()
    assert created["title"] == "x" * 80 + "…"


def test_short_post_title_is_kept_whole() -> None:
    body = {"kind": "post", "variants": [{"label": "A", "text": "Breve"}]}
    assert client.post("/tests", json=body).json()["title"] == "Breve"

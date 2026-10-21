import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

# Il runner di fixture non deve dormire nei test; va impostato prima di importare app.
os.environ.setdefault("FIXTURE_DELAY_SECONDS", "0")
# Il .env locale può puntare al pool generato: i test usano sempre le fixture.
os.environ.setdefault("PERSONAS_PATH", "")

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "shared" / "schemas"


def _build_registry() -> Registry:
    registry: Registry = Registry()
    for path in SCHEMAS_DIR.glob("*.schema.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(contents, default_specification=DRAFT202012)
        registry = registry.with_resource(contents["$id"], resource)
    return registry


REGISTRY = _build_registry()


def _validate(name: str, data: object) -> None:
    """Valida data contro shared/schemas/<name>; i $ref tra schemi si risolvono."""
    schema = json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))
    validator = Draft202012Validator(
        schema,
        registry=REGISTRY,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
    validator.validate(data)


@pytest.fixture
def validate():
    return _validate


@pytest.fixture(autouse=True)
def _temp_database(tmp_path, monkeypatch):
    """Ogni test usa un database SQLite temporaneo, mai quello di sviluppo."""
    from app import store
    from app.config import settings

    monkeypatch.setattr(settings, "database_path", str(tmp_path / "test.sqlite"))
    monkeypatch.setattr(settings, "upload_dir", tmp_path / "uploads")
    # Il .env locale può impostare provider reali: i test non devono chiamare la rete.
    monkeypatch.setattr(settings, "responder", "fake")
    monkeypatch.setattr(settings, "summarizer", "fake")
    store.init_db()


@pytest.fixture
def no_background(monkeypatch):
    """Il test resta in queued: il task in background non parte."""
    from app.api import tests as tests_api

    async def _noop(*args) -> None:
        return None

    monkeypatch.setattr(tests_api, "run_test", lambda test_id: None)
    monkeypatch.setattr(tests_api, "run_post_test", _noop)


@pytest.fixture
def anyio_backend():
    return "asyncio"

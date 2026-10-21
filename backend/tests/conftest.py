import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

# Il runner di fixture non deve dormire nei test; va impostato prima di importare app.
os.environ.setdefault("FIXTURE_DELAY_SECONDS", "0")

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
def _reset_store():
    from app import store

    store.reset()

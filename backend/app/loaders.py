import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from app.config import REPO_ROOT
from app.models import Persona

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

ModelT = TypeVar("ModelT", bound=BaseModel)


def _read(name: str) -> object:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def load_list(name: str, model: type[ModelT]) -> tuple[ModelT, ...]:
    return tuple(model.model_validate(item) for item in _read(name))


def load_one(name: str, model: type[ModelT]) -> ModelT:
    return model.model_validate(_read(name))


def load_personas(path: str) -> tuple[Persona, ...]:
    """Le personas del file indicato (dalla radice del repo), altrimenti le fixture."""
    if not path:
        return load_list("personas.json", Persona)
    source = REPO_ROOT / path
    return tuple(Persona.model_validate(item) for item in json.loads(source.read_text("utf-8")))

from fastapi import APIRouter

from app.config import settings
from app.loaders import load_personas
from app.models import Persona

router = APIRouter()

# Fixture di default; PERSONAS_PATH punta al pool generato da scripts.generate_personas.
PERSONAS = load_personas(settings.personas_path)


@router.get("/personas", response_model=list[Persona])
def list_personas() -> tuple[Persona, ...]:
    return PERSONAS

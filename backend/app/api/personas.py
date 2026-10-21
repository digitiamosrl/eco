from fastapi import APIRouter

from app.loaders import load_list
from app.models import Persona

router = APIRouter()

# shortcut: fixture, sostituire con il panel generato (A2)
PERSONAS = load_list("personas.json", Persona)


@router.get("/personas", response_model=list[Persona])
def list_personas() -> tuple[Persona, ...]:
    return PERSONAS

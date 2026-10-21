from fastapi import APIRouter

from app.loaders import load_list
from app.models import Persona

router = APIRouter()

PERSONAS = load_list("personas.json", Persona)


@router.get("/personas", response_model=list[Persona])
def list_personas() -> tuple[Persona, ...]:
    return PERSONAS

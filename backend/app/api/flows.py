from fastapi import APIRouter

from app.loaders import load_list
from app.models import Flow

router = APIRouter()

FLOWS = load_list("flows.json", Flow)


@router.get("/flows", response_model=list[Flow])
def list_flows() -> tuple[Flow, ...]:
    return FLOWS

import asyncio

from fastapi import APIRouter, HTTPException

from app import store
from app.engine.llm_client import LlmError
from app.models import Report, Test
from app.report.builder import build_post_report
from app.report.summarize import build_summarizer

router = APIRouter()

# shortcut: cache in memoria senza scadenza, il riavvio la svuota; passare allo store se serve.
_REPORTS: dict[str, asyncio.Task[Report]] = {}


async def _report_for(test: Test) -> Report:
    """Una sola costruzione per test: richieste ripetute o simultanee riusano lo stesso task."""
    task = _REPORTS.get(test.id)
    if task is None:
        task = asyncio.create_task(
            build_post_report(
                test.id, test.stimuli, store.list_responses(test.id), build_summarizer()
            )
        )
        _REPORTS[test.id] = task
    try:
        return await asyncio.shield(task)
    finally:
        # Un fallimento non resta in cache: la richiesta successiva riprova.
        if task.done() and (task.cancelled() or task.exception() is not None):
            _REPORTS.pop(test.id, None)


@router.get(
    "/tests/{test_id}/report",
    response_model=Report,
    response_model_exclude_none=True,
)
async def get_report(test_id: str) -> Report:
    test = store.get(test_id)
    if test is None:
        raise HTTPException(status_code=404, detail="Test non trovato")
    if test.status != "done":
        raise HTTPException(status_code=409, detail="Il test non è ancora completato")
    if test.kind == "prototype":
        raise HTTPException(status_code=501, detail="Report del prototipo non ancora disponibile")
    try:
        return await _report_for(test)
    except LlmError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

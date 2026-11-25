import asyncio
import logging

from fastapi import APIRouter, HTTPException

from app import store
from app.engine.llm_client import LlmError
from app.models import Report, Test
from app.report.builder import build_report
from app.report.calibration import load_fidelity
from app.report.summarize import build_summarizer

router = APIRouter()
logger = logging.getLogger(__name__)

# Solo per non costruire due volte lo stesso report: quelli finiti stanno nello store.
_REPORTS: dict[str, asyncio.Task[Report]] = {}


async def _build_and_save(test: Test) -> Report:
    report = await build_report(
        test.id, test.stimuli, store.list_responses(test.id), build_summarizer()
    )
    store.save_report(report)
    return report


async def _report_for(test: Test) -> Report:
    """Il report salvato, oppure una sola costruzione per test anche con richieste simultanee."""
    report = store.load_report(test.id)
    if report is None:
        task = _REPORTS.get(test.id)
        if task is None:
            task = asyncio.create_task(_build_and_save(test))
            _REPORTS[test.id] = task
        try:
            report = await asyncio.shield(task)
        finally:
            # Un fallimento non resta in cache: la richiesta successiva riprova.
            if task.done() and (task.cancelled() or task.exception() is not None):
                _REPORTS.pop(test.id, None)
    # La calibrazione è sui post pubblicati: per un prototipo manca e il report lo dice.
    fidelity = load_fidelity() if test.kind == "post" else None
    return report.model_copy(update={"fidelity": fidelity})


async def prepare_report(test_id: str) -> None:
    """Avviata a fine test: con un modello locale la sintesi richiede minuti.

    Così il report è pronto quando lo si apre; se fallisce, si riprova alla prima richiesta.
    """
    test = store.get(test_id)
    if test is None or test.status != "done":
        return
    try:
        await _report_for(test)
    except Exception:
        logger.exception("Preparazione del report %s fallita", test_id)


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
    try:
        return await _report_for(test)
    except LlmError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

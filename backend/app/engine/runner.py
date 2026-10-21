import asyncio
import json
import logging
from collections.abc import Sequence

from jsonschema import Draft202012Validator

from app import store
from app.config import REPO_ROOT, settings
from app.engine.responder import Responder
from app.models import Persona, Response, Stimulus

logger = logging.getLogger(__name__)

PANEL_ERROR = "Il test non è stato completato: il servizio di analisi non è riuscito a rispondere."
_ATTEMPTS = 2  # un tentativo più un solo retry se la risposta non è valida
_RESPONSE_VALIDATOR = Draft202012Validator(
    json.loads((REPO_ROOT / "shared" / "schemas" / "response.schema.json").read_text("utf-8"))
)


class _InvalidResponseError(Exception):
    pass


def _is_valid(response: Response) -> bool:
    return _RESPONSE_VALIDATOR.is_valid(response.model_dump(mode="json", exclude_none=True))


async def _ask(
    responder: Responder,
    semaphore: asyncio.Semaphore,
    stop: asyncio.Event,
    persona: Persona,
    stimulus: Stimulus,
) -> Response | None:
    """None se il test è già fallito: le chiamate rimaste non partono."""
    async with semaphore:
        for _ in range(_ATTEMPTS):
            if stop.is_set():
                return None
            try:
                response = await responder.respond(persona, stimulus)
            except Exception:
                stop.set()
                raise
            if _is_valid(response):
                return response
        stop.set()
    raise _InvalidResponseError(f"{persona.id} / {stimulus.id}")


async def _job(
    test_id: str,
    responder: Responder,
    semaphore: asyncio.Semaphore,
    stop: asyncio.Event,
    persona: Persona,
    stimulus: Stimulus,
) -> None:
    response = await _ask(responder, semaphore, stop, persona, stimulus)
    if response is None:
        return
    store.add_response(test_id, response)
    store.update(test_id, done_count=store.count_responses(test_id))


async def run_post_test(test_id: str, responder: Responder, personas: Sequence[Persona]) -> None:
    test = store.update(test_id, status="running")
    semaphore = asyncio.Semaphore(settings.panel_concurrency)
    stop = asyncio.Event()
    jobs = [
        asyncio.ensure_future(_job(test_id, responder, semaphore, stop, persona, stimulus))
        for persona in personas
        for stimulus in test.stimuli
    ]
    try:
        await asyncio.gather(*jobs)
    except Exception:
        logger.exception("Test %s interrotto", test_id)
        for job in jobs:
            job.cancel()
        await asyncio.gather(*jobs, return_exceptions=True)
        store.update(test_id, status="error", error=PANEL_ERROR)
        return
    store.update(test_id, status="done")

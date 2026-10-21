"""Verifica manuale con la chiave reale di OpenRouter. Non è un test: non gira in pytest.

Uso, da backend/ con OPENROUTER_API_KEY e PERSONA_MODEL nel file .env:
    python -m scripts.smoke_llm
"""

import asyncio
import statistics
import time
from typing import Any

import httpx

from app.api.personas import PERSONAS
from app.config import settings
from app.engine.responder import LlmResponder
from app.engine.runner import _is_valid  # stessa validazione del runner
from app.models import Response, Stimulus

PERSONA_COUNT = 3
REPEATS = 4
POST = Stimulus(
    id="smoke-post",
    kind="post",
    text="Ogni lunedì raccontiamo un caso concreto di un cliente: il problema, la soluzione "
    "e il risultato misurato.",
)
_usage: list[dict[str, Any]] = []


async def _record_usage(response: httpx.Response) -> None:
    await response.aread()
    try:
        data = response.json()
    except ValueError:
        return
    if isinstance(data, dict) and isinstance(data.get("usage"), dict):
        _usage.append(data["usage"])


async def _ask(
    responder: LlmResponder, persona: Any, semaphore: asyncio.Semaphore
) -> dict[str, Any]:
    """Due tentativi come il runner: eccezione o risposta fuori schema contano come fallimento."""
    async with semaphore:
        for attempt in (1, 2):
            started = time.perf_counter()
            try:
                response: Response = await responder.respond(persona, POST)
            except Exception as exc:  # qui si conta il tipo di errore, non si nasconde
                print(f"  tentativo {attempt} fallito: {type(exc).__name__}")
                continue
            if _is_valid(response):
                latency = time.perf_counter() - started
                return {"attempt": attempt, "latency": latency, "response": response}
            print(f"  tentativo {attempt}: risposta fuori schema")
    return {"attempt": None, "latency": None, "response": None}


def _report(results: list[dict[str, Any]]) -> None:
    first = [r for r in results if r["attempt"] == 1]
    retried = [r for r in results if r["attempt"] == 2]
    failed = [r for r in results if r["attempt"] is None]
    latencies = [r["latency"] for r in results if r["latency"] is not None]
    print(f"Chiamate: {len(results)} ({PERSONA_COUNT} personas x {REPEATS} ripetizioni)")
    print(f"Valide al primo tentativo: {len(first)}")
    print(f"Valide dopo retry: {len(retried)}")
    print(f"Fallite: {len(failed)}")
    if latencies:
        print(f"Latenza media per risposta valida: {statistics.mean(latencies):.2f} s")
    valid = [r["response"] for r in results if r["response"] is not None]
    if valid:
        print(f"Esempio (persona {valid[0].persona_id}):")
        print(f"  thought: {valid[0].thought}")
        print(f"  said: {valid[0].said}")
    if not _usage:
        print("Token: usage non presente nelle risposte")
    else:
        prompt = sum(u.get("prompt_tokens", 0) for u in _usage)
        completion = sum(u.get("completion_tokens", 0) for u in _usage)
        print(f"Token: {prompt} in ingresso, {completion} in uscita ({len(_usage)} risposte)")


async def main() -> int:
    if not settings.openrouter_api_key or not settings.persona_model:
        print("Servono OPENROUTER_API_KEY e PERSONA_MODEL nel file .env.")
        return 1
    client = httpx.AsyncClient(
        timeout=settings.llm_timeout_seconds, event_hooks={"response": [_record_usage]}
    )
    responder = LlmResponder(client)
    semaphore = asyncio.Semaphore(settings.panel_concurrency)
    jobs = [
        _ask(responder, persona, semaphore)
        for persona in PERSONAS[:PERSONA_COUNT]
        for _ in range(REPEATS)
    ]
    results = await asyncio.gather(*jobs)
    await client.aclose()
    _report(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

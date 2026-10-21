import asyncio
import json
import re
from typing import Any

import httpx

from app.config import REPO_ROOT, settings

# Module-level perché i test lo azzerano; un solo retry, quindi l'attesa è breve.
RETRY_DELAY_SECONDS = 1.0
_ATTEMPTS = 2
_FENCED_JSON = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)

_UNAVAILABLE = "Il servizio di analisi non è disponibile in questo momento. Riprova più tardi."
_AUTH = "La chiave del servizio di analisi non è valida."
_BAD_JSON = "Il servizio di analisi ha restituito una risposta non leggibile."

# shortcut: un solo client per processo, nessuna chiusura esplicita, ok per una POC locale
_client: httpx.AsyncClient | None = None


class LlmError(Exception):
    """Messaggio in italiano senza dettagli interni: può arrivare all'utente."""


def load_prompt(name: str) -> str:
    """Il prompt senza il commento di bozza in testa: il modello non lo deve leggere."""
    text = (REPO_ROOT / "prompts" / name).read_text(encoding="utf-8")
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()


def shared_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=settings.llm_timeout_seconds)
    return _client


def _parse_content(content: str) -> dict[str, Any]:
    text = content.strip()
    fenced = _FENCED_JSON.match(text)
    if fenced is not None:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LlmError(_BAD_JSON) from exc
    if not isinstance(data, dict):
        raise LlmError(_BAD_JSON)
    return data


def _message_content(response: httpx.Response) -> str:
    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LlmError(_BAD_JSON) from exc
    if not isinstance(content, str):
        raise LlmError(_BAD_JSON)
    return content


async def _post(client: httpx.AsyncClient, payload: dict[str, Any]) -> httpx.Response:
    url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.openrouter_api_key}"}
    for attempt in range(1, _ATTEMPTS + 1):
        try:
            response = await client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise LlmError(_UNAVAILABLE) from exc
        if response.status_code == 200:
            return response
        if response.status_code in (401, 403):
            raise LlmError(_AUTH)
        retryable = response.status_code == 429 or response.status_code >= 500
        if not retryable or attempt == _ATTEMPTS:
            raise LlmError(_UNAVAILABLE)
        await asyncio.sleep(RETRY_DELAY_SECONDS)
    raise LlmError(_UNAVAILABLE)  # irraggiungibile, chiude il tipo di ritorno


async def chat_json(
    client: httpx.AsyncClient,
    *,
    model: str,
    messages: list[dict[str, Any]],
    schema_name: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
    }
    response = await _post(client, payload)
    return _parse_content(_message_content(response))

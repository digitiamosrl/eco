import json

import httpx
import pytest

from app.config import settings
from app.engine import llm_client
from app.engine.llm_client import LlmError, chat_json

pytestmark = pytest.mark.anyio

SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
MESSAGES = [{"role": "user", "content": "ciao"}]
API_KEY = "sk-or-test-key"


@pytest.fixture(autouse=True)
def _llm_settings(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", API_KEY)
    monkeypatch.setattr(settings, "openrouter_base_url", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(llm_client, "RETRY_DELAY_SECONDS", 0)


def _completion(content: str) -> httpx.Response:
    body = {"choices": [{"message": {"role": "assistant", "content": content}}]}
    return httpx.Response(200, json=body)


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def _call(client: httpx.AsyncClient) -> dict:
    return await chat_json(
        client, model="modello/test", messages=MESSAGES, schema_name="esito", schema=SCHEMA
    )


async def test_sends_well_formed_request() -> None:
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return _completion('{"ok": true}')

    assert await _call(_client(handler)) == {"ok": True}
    request = sent[0]
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["Authorization"] == f"Bearer {API_KEY}"
    body = json.loads(request.content)
    assert body["model"] == "modello/test"
    assert body["messages"] == MESSAGES
    assert body["response_format"] == {
        "type": "json_schema",
        "json_schema": {"name": "esito", "strict": True, "schema": SCHEMA},
    }
    assert body["provider"] == {"require_parameters": True}


async def test_strips_json_code_block() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _completion('```json\n{"ok": false}\n```')

    assert await _call(_client(handler)) == {"ok": False}


async def test_retries_once_on_429() -> None:
    calls = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429)
        return _completion('{"ok": true}')

    assert await _call(_client(handler)) == {"ok": True}
    assert len(calls) == 2


async def test_persistent_500_raises_llm_error_after_one_retry() -> None:
    calls = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(500)

    with pytest.raises(LlmError, match="non è disponibile"):
        await _call(_client(handler))
    assert len(calls) == 2


async def test_other_client_errors_are_not_retried() -> None:
    calls = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(401)

    with pytest.raises(LlmError, match="chiave"):
        await _call(_client(handler))
    assert len(calls) == 1


async def test_invalid_json_raises_llm_error_without_retry() -> None:
    calls = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return _completion("non è JSON")

    with pytest.raises(LlmError, match="non leggibile"):
        await _call(_client(handler))
    assert len(calls) == 1


async def test_transport_error_raises_llm_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("rete assente", request=request)

    with pytest.raises(LlmError, match="non è disponibile"):
        await _call(_client(handler))


async def test_api_key_never_appears_in_errors() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text=f"echo {API_KEY}")

    with pytest.raises(LlmError) as info:
        await _call(_client(handler))
    assert API_KEY not in str(info.value)
    assert API_KEY not in repr(info.value)

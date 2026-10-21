import base64
import json

import httpx
import pytest

from app import models, store
from app.api.personas import PERSONAS
from app.config import settings
from app.engine import llm_client
from app.engine.llm_client import LlmError
from app.engine.responder import LlmResponder
from app.engine.runner import run_post_test
from app.models import Response, Stimulus

pytestmark = pytest.mark.anyio

PERSONA = PERSONAS[0]
POST = Stimulus(id="variante-a", kind="post", variant_label="A", text="Testo del post.")
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"dati"
VALID_OUTPUT = {
    "thought": "Non mi convince.",
    "said": "Lo guarderei.",
    "score": 3,
    "objections": ["Manca un riferimento concreto."],
}


@pytest.fixture(autouse=True)
def _llm_settings(monkeypatch):
    monkeypatch.setattr(settings, "persona_model", "modello/persona")
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or-test-key")


def _completion(output: dict) -> httpx.Response:
    body = {"choices": [{"message": {"role": "assistant", "content": json.dumps(output)}}]}
    return httpx.Response(200, json=body)


def _recording_client(output: dict, sent: list[dict]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return _completion(output)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _user_content(body: dict) -> list[dict]:
    return body["messages"][0]["content"]


async def test_prompt_is_filled_and_asks_no_ids() -> None:
    sent: list[dict] = []
    await LlmResponder(_recording_client(VALID_OUTPUT, sent)).respond(PERSONA, POST)

    text = _user_content(sent[0])[0]["text"]
    assert PERSONA.profile in text
    assert POST.text in text
    assert "{persona}" not in text and "{stimulus}" not in text
    assert "BOZZA" not in text
    assert "persona_id" not in text and "stimulus_id" not in text

    schema = sent[0]["response_format"]["json_schema"]["schema"]
    assert "persona_id" not in schema["properties"]
    assert "stimulus_id" not in schema["properties"]
    assert "persona_id" not in schema["required"]
    assert "score" in schema["required"]


async def test_ids_are_filled_by_code() -> None:
    sent: list[dict] = []
    wrong_ids = {**VALID_OUTPUT, "persona_id": "altro", "stimulus_id": "altro"}
    response = await LlmResponder(_recording_client(wrong_ids, sent)).respond(PERSONA, POST)

    assert response.persona_id == PERSONA.id
    assert response.stimulus_id == POST.id
    assert response.score == 3


async def test_image_is_sent_as_data_url(tmp_path) -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    (settings.upload_dir / "abc.png").write_bytes(PNG_BYTES)
    screen = Stimulus(id="post-img", kind="post", text="Con immagine.", image_url="/files/abc.png")
    sent: list[dict] = []

    await LlmResponder(_recording_client(VALID_OUTPUT, sent)).respond(PERSONA, screen)

    image = _user_content(sent[0])[1]
    assert image["type"] == "image_url"
    prefix = "data:image/png;base64,"
    assert image["image_url"]["url"].startswith(prefix)
    encoded = image["image_url"]["url"].removeprefix(prefix)
    assert base64.b64decode(encoded) == PNG_BYTES


async def test_missing_image_raises_llm_error() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    screen = Stimulus(id="post-img", kind="post", text="x", image_url="/files/assente.png")
    sent: list[dict] = []

    with pytest.raises(LlmError):
        await LlmResponder(_recording_client(VALID_OUTPUT, sent)).respond(PERSONA, screen)
    assert sent == []


async def test_path_traversal_in_image_name_is_rejected(tmp_path) -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "segreto.png").write_bytes(PNG_BYTES)
    screen = Stimulus(id="post-img", kind="post", text="x", image_url="/files/../segreto.png")
    sent: list[dict] = []

    with pytest.raises(LlmError):
        await LlmResponder(_recording_client(VALID_OUTPUT, sent)).respond(PERSONA, screen)
    assert sent == []


async def test_output_outside_schema_raises_llm_error() -> None:
    sent: list[dict] = []
    bad = {**VALID_OUTPUT, "score": 9}

    with pytest.raises(LlmError):
        await LlmResponder(_recording_client(bad, sent)).respond(PERSONA, POST)


async def test_valid_response_goes_through_runner() -> None:
    test = models.Test(
        id="t-llm",
        kind="post",
        status="queued",
        created_at="2026-10-21T10:00:00+00:00",
        done_count=0,
        total_count=1,
        stimuli=[POST],
    )
    assert store.add_if_idle(test)

    client = _recording_client(VALID_OUTPUT, [])
    await run_post_test("t-llm", LlmResponder(client), [PERSONA])

    assert store.get("t-llm").status == "done"
    responses = store.list_responses("t-llm")
    assert len(responses) == 1
    assert isinstance(responses[0], Response)


async def test_shared_client_is_created_once() -> None:
    assert llm_client.shared_client() is llm_client.shared_client()

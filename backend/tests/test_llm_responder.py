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


async def test_model_can_be_overridden_per_responder() -> None:
    sent: list[dict] = []
    client = _recording_client(VALID_OUTPUT, sent)
    await LlmResponder(client, model="altro/modello").respond(PERSONA, POST)
    await LlmResponder(client).respond(PERSONA, POST)

    assert [body["model"] for body in sent] == ["altro/modello", "modello/persona"]


async def test_pdf_attachment_is_sent_as_file_block(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "upload_dir", tmp_path)
    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.7 dati")
    stimulus = POST.model_copy(update={"image_url": "/files/doc.pdf", "attachment_kind": "pdf"})
    sent: list[dict] = []
    client = _recording_client({**VALID_OUTPUT, "action": "react", "reaction": "adoro"}, sent)
    response = await LlmResponder(client=client).respond(PERSONA, stimulus)
    assert (response.action, response.reaction) == ("react", "adoro")
    block = sent[0]["messages"][0]["content"][1]
    assert block["type"] == "file"
    assert block["file"]["file_data"].startswith("data:application/pdf;base64,")


async def test_prototype_screen_is_framed_as_a_step_of_an_app(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "upload_dir", tmp_path)
    (tmp_path / "schermata.png").write_bytes(PNG_BYTES)
    screen = Stimulus(
        id="p-s1-2",
        kind="prototype_screen",
        flow_id="p:s1",
        screen_index=2,
        image_url="/files/schermata.png",
        page_structure="Scelta del piano",
    )
    sent: list[dict] = []
    await LlmResponder(_recording_client(VALID_OUTPUT, sent)).respond(PERSONA, screen)

    text = _user_content(sent[0])[0]["text"]
    assert "Scelta del piano" in text
    assert "schermata 3" in text
    assert "{name}" not in text and "{step}" not in text


async def test_model_decides_the_action_before_writing_what_it_says() -> None:
    sent: list[dict] = []
    await LlmResponder(_recording_client(VALID_OUTPUT, sent)).respond(PERSONA, POST)
    order = list(sent[0]["response_format"]["json_schema"]["schema"]["properties"])
    assert order[:4] == ["thought", "action", "reaction", "said"]


async def test_persona_calls_keep_the_model_temperature() -> None:
    sent: list[dict] = []
    await LlmResponder(_recording_client(VALID_OUTPUT, sent)).respond(PERSONA, POST)
    assert "temperature" not in sent[0]  # la varietà tra personas viene anche da qui


async def test_required_fields_depend_on_the_stimulus() -> None:
    screen = Stimulus(id="s", kind="prototype_screen", flow_id="f", screen_index=0, text="x")
    sent: list[dict] = []
    client = _recording_client(VALID_OUTPUT, sent)
    await LlmResponder(client).respond(PERSONA, POST)
    await LlmResponder(client).respond(PERSONA, screen)
    post_required, screen_required = (
        body["response_format"]["json_schema"]["schema"]["required"] for body in sent
    )
    # Facoltativi nello schema condiviso, ma un modello locale li salta se non li impone.
    assert "action" in post_required and "would_abandon" not in post_required
    assert {"would_abandon", "misunderstood"} <= set(screen_required)
    assert "action" not in screen_required


async def test_prototype_screen_tells_the_persona_what_it_is_trying_to_do() -> None:
    screen = Stimulus(
        id="s",
        kind="prototype_screen",
        flow_id="f",
        screen_index=0,
        page_structure="Home",
        task="Chiedere un preventivo per il gestionale",
    )
    sent: list[dict] = []
    await LlmResponder(_recording_client(VALID_OUTPUT, sent)).respond(PERSONA, screen)
    text = _user_content(sent[0])[0]["text"]
    assert "Chiedere un preventivo per il gestionale" in text
    assert "{task}" not in text

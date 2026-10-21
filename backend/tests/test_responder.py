import pytest

from app.api.personas import PERSONAS
from app.config import settings
from app.engine.responder import FakeResponder, LlmResponder, build_responder
from app.models import Stimulus

pytestmark = pytest.mark.anyio

STIMULI = [
    Stimulus(id="variante-a", kind="post", variant_label="A", text="Primo testo."),
    Stimulus(id="variante-b", kind="post", variant_label="B", text="Secondo testo."),
]


async def test_fake_responder_returns_valid_responses(validate) -> None:
    responder = FakeResponder()
    for persona in PERSONAS:
        for stimulus in STIMULI:
            response = await responder.respond(persona, stimulus)
            assert response.persona_id == persona.id
            assert response.stimulus_id == stimulus.id
            assert 1 <= response.score <= 5
            validate("response.schema.json", response.model_dump(mode="json", exclude_none=True))


async def test_fake_responder_is_deterministic() -> None:
    responder = FakeResponder()
    first = await responder.respond(PERSONAS[0], STIMULI[0])
    second = await responder.respond(PERSONAS[0], STIMULI[0])
    assert first == second


async def test_fake_responder_has_some_objections_and_some_without() -> None:
    responder = FakeResponder()
    responses = [await responder.respond(p, s) for p in PERSONAS for s in STIMULI]
    assert any(r.objections for r in responses)
    assert any(not r.objections for r in responses)


async def test_llm_responder_is_a_stub() -> None:
    with pytest.raises(NotImplementedError, match="Provider AI non ancora configurato"):
        await LlmResponder().respond(PERSONAS[0], STIMULI[0])


def test_build_responder_defaults_to_fake(monkeypatch) -> None:
    monkeypatch.setattr(settings, "responder", "fake")
    assert isinstance(build_responder(), FakeResponder)
    monkeypatch.setattr(settings, "responder", "llm")
    assert isinstance(build_responder(), LlmResponder)

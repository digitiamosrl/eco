import asyncio

import pytest

from app import models, store
from app.api.personas import PERSONAS
from app.config import settings
from app.engine.llm_client import LlmError
from app.engine.responder import FakeResponder
from app.engine.runner import PANEL_ERROR, run_post_test
from app.models import Response, Stimulus

STIMULI = [
    Stimulus(id="variante-a", kind="post", variant_label="A", text="Primo testo."),
    Stimulus(id="variante-b", kind="post", variant_label="B", text="Secondo testo."),
]
TOTAL = len(PERSONAS) * len(STIMULI)

pytestmark = pytest.mark.anyio


def _queue_test(test_id: str = "t1") -> None:
    test = models.Test(
        id=test_id,
        kind="post",
        status="queued",
        created_at="2026-10-21T10:00:00+00:00",
        done_count=0,
        total_count=TOTAL,
        stimuli=STIMULI,
    )
    assert store.add_if_idle(test)


def _valid(persona_id: str, stimulus_id: str, score: int = 3) -> Response:
    return Response(
        persona_id=persona_id,
        stimulus_id=stimulus_id,
        thought="Non so.",
        said="Non so.",
        score=score,
        objections=[],
    )


class CountingResponder:
    def __init__(self) -> None:
        self.in_flight = 0
        self.max_in_flight = 0

    async def respond(self, persona, stimulus) -> Response:
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        await asyncio.sleep(0.01)
        self.in_flight -= 1
        return _valid(persona.id, stimulus.id)


class InvalidOnceResponder:
    """Prima risposta fuori schema (score 9), poi valida: serve un solo retry."""

    def __init__(self) -> None:
        self.seen: set[tuple[str, str]] = set()

    async def respond(self, persona, stimulus) -> Response:
        key = (persona.id, stimulus.id)
        if key not in self.seen:
            self.seen.add(key)
            return Response.model_construct(
                persona_id=persona.id,
                stimulus_id=stimulus.id,
                thought="x",
                said="x",
                score=9,
                objections=[],
            )
        return _valid(persona.id, stimulus.id)


class AlwaysInvalidResponder:
    async def respond(self, persona, stimulus) -> Response:
        return Response.model_construct(
            persona_id=persona.id,
            stimulus_id=stimulus.id,
            thought="x",
            said="x",
            score=0,
            objections=[],
        )


class UnreadableOnceResponder:
    """Prima risposta del modello illeggibile (LlmError), poi valida: serve un solo retry."""

    def __init__(self) -> None:
        self.seen: set[tuple[str, str]] = set()

    async def respond(self, persona, stimulus) -> Response:
        key = (persona.id, stimulus.id)
        if key not in self.seen:
            self.seen.add(key)
            raise LlmError("Il servizio di analisi ha restituito una risposta non leggibile.")
        return _valid(persona.id, stimulus.id)


class AlwaysUnreadableResponder:
    def __init__(self) -> None:
        self.calls = 0

    async def respond(self, persona, stimulus) -> Response:
        self.calls += 1
        raise LlmError("Il servizio di analisi ha restituito una risposta non leggibile.")


class FailingResponder:
    def __init__(self) -> None:
        self.calls = 0

    async def respond(self, persona, stimulus) -> Response:
        self.calls += 1
        raise RuntimeError("chiave segreta sk-123")


async def test_run_reaches_done_with_all_responses_saved() -> None:
    _queue_test()
    await run_post_test("t1", FakeResponder(), PERSONAS)
    test = store.get("t1")
    assert test.status == "done"
    assert test.done_count == test.total_count == TOTAL
    assert store.count_responses("t1") == TOTAL


async def test_concurrency_limit_is_respected(monkeypatch) -> None:
    monkeypatch.setattr(settings, "panel_concurrency", 3)
    _queue_test()
    responder = CountingResponder()
    await run_post_test("t1", responder, PERSONAS)
    assert responder.max_in_flight == 3
    assert store.get("t1").status == "done"


async def test_invalid_response_is_retried_once() -> None:
    _queue_test()
    responder = InvalidOnceResponder()
    await run_post_test("t1", responder, PERSONAS)
    test = store.get("t1")
    assert test.status == "done"
    assert store.count_responses("t1") == TOTAL


async def test_invalid_response_after_retry_fails_the_test() -> None:
    _queue_test()
    await run_post_test("t1", AlwaysInvalidResponder(), PERSONAS)
    test = store.get("t1")
    assert test.status == "error"
    assert test.error == PANEL_ERROR


async def test_responder_exception_fails_without_leaking_details() -> None:
    _queue_test()
    responder = FailingResponder()
    await run_post_test("t1", responder, PERSONAS)
    test = store.get("t1")
    assert test.status == "error"
    assert test.error == PANEL_ERROR
    assert "sk-123" not in (test.error or "")
    assert responder.calls < TOTAL


async def test_unreadable_model_output_is_retried_once() -> None:
    _queue_test()
    await run_post_test("t1", UnreadableOnceResponder(), PERSONAS)
    test = store.get("t1")
    assert test.status == "done"
    assert store.count_responses("t1") == TOTAL


async def test_unreadable_output_after_retry_fails_the_test() -> None:
    _queue_test()
    responder = AlwaysUnreadableResponder()
    await run_post_test("t1", responder, PERSONAS)
    test = store.get("t1")
    assert test.status == "error"
    assert test.error == PANEL_ERROR
    assert responder.calls < TOTAL * 2

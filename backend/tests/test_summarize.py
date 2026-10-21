import json

import httpx
import pytest

from app.config import settings
from app.engine.llm_client import LlmError
from app.models import Response, Stimulus
from app.report.aggregate import StimulusStats
from app.report.summarize import FakeSummarizer, LlmSummarizer

pytestmark = pytest.mark.anyio


def _stats(label: str, scores: list[int], objections: tuple[str, ...]) -> StimulusStats:
    stimulus = Stimulus(id=f"variante-{label.lower()}", kind="post", variant_label=label, text="x")
    responses = tuple(
        Response(
            persona_id=f"p{i}",
            stimulus_id=stimulus.id,
            thought="x",
            said="x",
            score=s,
            objections=[],
        )
        for i, s in enumerate(scores)
    )
    mean = round(sum(scores) / len(scores), 2)
    return StimulusStats(
        stimulus=stimulus,
        rank=1,
        mean_score=mean,
        score_distribution={str(n): scores.count(n) for n in range(1, 6)},
        objections=objections,
        responses=responses,
    )


async def test_fake_summarizer_mentions_mean_and_top_objection() -> None:
    stats = _stats("A", [5, 4], ("Prezzo alto",))
    text = await FakeSummarizer().said_summary(stats)
    assert "4.50" in text and "Prezzo alto" in text
    assert "4 o 5" in await FakeSummarizer().thought_summary(stats)


async def test_fake_summarizer_without_objections() -> None:
    stats = _stats("A", [3], ())
    assert "Nessuna obiezione" in await FakeSummarizer().said_summary(stats)


async def test_fake_summarizer_overall_names_the_top_variant() -> None:
    ranking = [_stats("B", [5], ())]
    assert "variante B" in await FakeSummarizer().summary(ranking)
    assert await FakeSummarizer().summary([]) == "Nessuna risposta registrata."


def _llm(handler_output: dict | None, sent: list[dict]) -> LlmSummarizer:
    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        content = json.dumps(handler_output)
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    return LlmSummarizer(httpx.AsyncClient(transport=httpx.MockTransport(handler)))


async def test_llm_summarizer_empty_ranking_makes_no_call(monkeypatch) -> None:
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or-test-key")
    sent: list[dict] = []
    assert await _llm({}, sent).summary([]) == "Nessuna risposta registrata."
    assert sent == []


async def test_said_and_thought_come_from_one_call(monkeypatch) -> None:
    monkeypatch.setattr(settings, "report_model", "modello/report")
    sent: list[dict] = []
    output = {"said_summary": "Dicono no.", "thought_summary": "Pensano sì."}
    summarizer = _llm(output, sent)
    stats = _stats("A", [5, 2], ("Prezzo alto",))

    assert await summarizer.said_summary(stats) == "Dicono no."
    assert await summarizer.thought_summary(stats) == "Pensano sì."
    assert len(sent) == 1
    assert sent[0]["model"] == "modello/report"
    prompt = sent[0]["messages"][0]["content"][0]["text"]
    assert "Variante: A" in prompt
    assert '"score": 5' in prompt


async def test_overview_names_top_variant_and_says_simulated(monkeypatch) -> None:
    sent: list[dict] = []
    summarizer = _llm({"summary": "In testa la variante B. Risultati simulati."}, sent)
    text = await summarizer.summary([_stats("B", [5], ())])

    assert "variante B" in text
    prompt = sent[0]["messages"][0]["content"][0]["text"]
    assert "variante B" in prompt


async def test_invalid_variant_output_raises_llm_error() -> None:
    summarizer = _llm({"said_summary": "", "thought_summary": "ok"}, [])
    with pytest.raises(LlmError):
        await summarizer.said_summary(_stats("A", [4], ()))


async def test_invalid_overview_output_raises_llm_error() -> None:
    with pytest.raises(LlmError):
        await _llm({"summary": 3}, []).summary([_stats("A", [4], ())])


async def test_report_summaries_run_in_parallel() -> None:
    import asyncio

    from app.models import Response, Stimulus
    from app.report.builder import build_post_report

    stimuli = [Stimulus(id=f"v{i}", kind="post", text="t") for i in range(2)]
    responses = [
        Response(persona_id="p1", stimulus_id=s.id, thought="a", said="b", score=3, objections=[])
        for s in stimuli
    ]
    # Due varianti e il riepilogo: partono insieme solo se le chiamate sono concorrenti.
    barrier = asyncio.Barrier(3)

    class BarrierSummarizer:
        async def said_summary(self, stats) -> str:
            await asyncio.wait_for(barrier.wait(), timeout=2)
            return "detto"

        async def thought_summary(self, stats) -> str:
            return "pensato"

        async def summary(self, ranking) -> str:
            await asyncio.wait_for(barrier.wait(), timeout=2)
            return "riepilogo"

    report = await build_post_report("t1", stimuli, responses, BarrierSummarizer())
    assert report.summary == "riepilogo"
    assert len(report.items) == 2

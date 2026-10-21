import pytest

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


async def test_llm_summarizer_is_a_stub() -> None:
    with pytest.raises(NotImplementedError, match="Provider AI non ancora configurato"):
        await LlmSummarizer().summary([])

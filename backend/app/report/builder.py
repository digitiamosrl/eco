import asyncio
from collections.abc import Sequence

from app.models import Fidelity, Report, ReportItem, Response, Stimulus
from app.report.aggregate import StimulusStats, aggregate
from app.report.summarize import Summarizer


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def divergent_persona_ids(responses: Sequence[Response]) -> list[str]:
    """Personas che in pubblico dicono (said) cosa diversa da ciò che pensano (thought).

    shortcut: confronto dei testi normalizzati, non del significato; passare al modello
    del report se la regola risulta troppo larga.
    """
    return [r.persona_id for r in responses if _norm(r.said) != _norm(r.thought)]


async def _summarize_variant(stats: StimulusStats, summarizer: Summarizer) -> tuple[str, str]:
    # said prima di thought: il summarizer riusa la stessa chiamata al modello.
    return await summarizer.said_summary(stats), await summarizer.thought_summary(stats)


async def build_post_report(
    test_id: str,
    stimuli: Sequence[Stimulus],
    responses: Sequence[Response],
    summarizer: Summarizer,
    fidelity: Fidelity | None = None,
) -> Report:
    ranking = aggregate(stimuli, responses)
    variant_texts, summary = await asyncio.gather(
        asyncio.gather(*(_summarize_variant(stats, summarizer) for stats in ranking)),
        summarizer.summary(ranking),
    )
    items = [
        ReportItem(
            stimulus_id=stats.stimulus.id,
            rank=stats.rank,
            mean_score=stats.mean_score,
            score_distribution=stats.score_distribution,
            objections=list(stats.objections),
            said_summary=said,
            thought_summary=thought,
            responses=list(stats.responses),
            divergent_persona_ids=divergent_persona_ids(stats.responses),
        )
        for stats, (said, thought) in zip(ranking, variant_texts, strict=True)
    ]
    return Report(test_id=test_id, simulated=True, summary=summary, items=items, fidelity=fidelity)

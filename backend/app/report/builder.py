from collections.abc import Sequence

from app.models import Report, ReportItem, Response, Stimulus
from app.report.aggregate import aggregate
from app.report.summarize import Summarizer


async def build_post_report(
    test_id: str,
    stimuli: Sequence[Stimulus],
    responses: Sequence[Response],
    summarizer: Summarizer,
) -> Report:
    ranking = aggregate(stimuli, responses)
    items = [
        ReportItem(
            stimulus_id=stats.stimulus.id,
            rank=stats.rank,
            mean_score=stats.mean_score,
            score_distribution=stats.score_distribution,
            objections=list(stats.objections),
            said_summary=await summarizer.said_summary(stats),
            thought_summary=await summarizer.thought_summary(stats),
            responses=list(stats.responses),
        )
        for stats in ranking
    ]
    return Report(
        test_id=test_id,
        simulated=True,
        summary=await summarizer.summary(ranking),
        items=items,
    )

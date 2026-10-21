from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from app.models import Response, Stimulus

MAX_OBJECTIONS = 5
_SCALE = range(1, 6)


@dataclass(frozen=True)
class StimulusStats:
    stimulus: Stimulus
    rank: int
    mean_score: float
    score_distribution: dict[str, int]
    objections: tuple[str, ...]
    responses: tuple[Response, ...]


def _mean(scores: Sequence[int]) -> float:
    return round(sum(scores) / len(scores), 2) if scores else 0.0


def _top_objections(responses: Sequence[Response]) -> tuple[str, ...]:
    counts = Counter(objection for response in responses for objection in response.objections)
    return tuple(objection for objection, _ in counts.most_common(MAX_OBJECTIONS))


def aggregate(stimuli: Sequence[Stimulus], responses: Sequence[Response]) -> list[StimulusStats]:
    """Statistiche per stimolo, in ordine di rank. Parità: vince la variante che viene prima."""
    groups = [
        (index, stimulus, tuple(r for r in responses if r.stimulus_id == stimulus.id))
        for index, stimulus in enumerate(stimuli)
    ]
    means = {index: _mean([r.score for r in group]) for index, _, group in groups}
    ranked = sorted(groups, key=lambda row: (-means[row[0]], row[0]))
    return [
        StimulusStats(
            stimulus=stimulus,
            rank=rank,
            mean_score=means[index],
            score_distribution={
                str(score): sum(1 for r in group if r.score == score) for score in _SCALE
            },
            objections=_top_objections(group),
            responses=group,
        )
        for rank, (index, stimulus, group) in enumerate(ranked, start=1)
    ]

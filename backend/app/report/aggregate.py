from collections import Counter
from collections.abc import Iterable, Sequence
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
    # Solo per le schermate di un prototipo; None per i post.
    abandon_count: int | None = None
    misunderstood: tuple[str, ...] | None = None


def _mean(scores: Sequence[int]) -> float:
    return round(sum(scores) / len(scores), 2) if scores else 0.0


def _most_common(items: Iterable[str]) -> tuple[str, ...]:
    return tuple(item for item, _ in Counter(items).most_common(MAX_OBJECTIONS))


def _top_objections(responses: Sequence[Response]) -> tuple[str, ...]:
    return _most_common(o for r in responses for o in r.objections)


def _abandons(responses: Sequence[Response]) -> int:
    return sum(1 for r in responses if r.would_abandon)


def aggregate(stimuli: Sequence[Stimulus], responses: Sequence[Response]) -> list[StimulusStats]:
    """Statistiche per stimolo, in ordine di rank. Parità: vince lo stimolo che viene prima.

    Post: rank 1 è il punteggio medio più alto. Schermate di prototipo: rank 1 è il punto
    più critico, cioè più abbandoni e, a parità, punteggio più basso.
    """
    screens = bool(stimuli) and all(s.kind == "prototype_screen" for s in stimuli)
    groups = [
        (index, stimulus, tuple(r for r in responses if r.stimulus_id == stimulus.id))
        for index, stimulus in enumerate(stimuli)
    ]
    means = {index: _mean([r.score for r in group]) for index, _, group in groups}
    if screens:
        ranked = sorted(groups, key=lambda row: (-_abandons(row[2]), means[row[0]], row[0]))
    else:
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
            abandon_count=_abandons(group) if screens else None,
            misunderstood=_most_common(m for r in group for m in r.misunderstood or [])
            if screens
            else None,
        )
        for rank, (index, stimulus, group) in enumerate(ranked, start=1)
    ]

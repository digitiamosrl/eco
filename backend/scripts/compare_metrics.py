"""Metriche per confrontare modelli e misurare la stabilità. Funzioni pure, nessuna rete.

Un run è l'elenco delle risposte valide di un'esecuzione completa (tutte le personas
su tutti i post); un modello ha più run.
"""

from collections import defaultdict
from collections.abc import Sequence
from itertools import combinations
from math import sqrt
from statistics import mean, pstdev

from app.models import Response

Run = Sequence[Response]


def post_means(run: Run) -> dict[str, float]:
    scores: dict[str, list[int]] = defaultdict(list)
    for response in run:
        scores[response.stimulus_id].append(response.score)
    return {post: mean(values) for post, values in scores.items()}


def kendall_tau_b(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Correlazione di rango con gestione dei pareggi. None se un vettore è costante."""
    concordant = discordant = tied_x = tied_y = 0
    for (x1, y1), (x2, y2) in combinations(zip(x, y, strict=True), 2):
        dx, dy = x1 - x2, y1 - y2
        if dx == 0 and dy == 0:
            continue
        if dx == 0:
            tied_x += 1
        elif dy == 0:
            tied_y += 1
        elif (dx > 0) == (dy > 0):
            concordant += 1
        else:
            discordant += 1
    denominator = sqrt((concordant + discordant + tied_x) * (concordant + discordant + tied_y))
    return None if denominator == 0 else (concordant - discordant) / denominator


def _tau_between(a: dict[str, float], b: dict[str, float]) -> float | None:
    common = sorted(a.keys() & b.keys())
    return kendall_tau_b([a[p] for p in common], [b[p] for p in common])


def _average(values: Sequence[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return mean(present) if present else None


def mean_pairwise_tau(runs: Sequence[Run]) -> float | None:
    """Quanto la classifica dei post è la stessa tra run diversi (1 = identica)."""
    means = [post_means(run) for run in runs]
    return _average([_tau_between(a, b) for a, b in combinations(means, 2)])


def top1_agreement(runs: Sequence[Run]) -> float:
    """Quota di run con lo stesso post al primo posto del run più frequente."""
    tops = [max(sorted(m), key=lambda p: m[p]) for m in map(post_means, runs) if m]
    if not tops:
        return 0.0
    return max(tops.count(t) for t in set(tops)) / len(tops)


def post_std(runs: Sequence[Run]) -> float:
    """Deviazione standard della media di ciascun post tra i run (più bassa è meglio)."""
    by_post: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        for post, value in post_means(run).items():
            by_post[post].append(value)
    return mean(pstdev(v) for v in by_post.values()) if by_post else 0.0


def spread(runs: Sequence[Run]) -> float:
    """Scarto medio tra il post migliore e il peggiore: 0 significa che non discrimina."""
    gaps = [max(m.values()) - min(m.values()) for m in map(post_means, runs) if m]
    return mean(gaps) if gaps else 0.0


def expected_tau(runs: Sequence[Run], expected_order: Sequence[str]) -> float | None:
    """Accordo tra la classifica media dei run e l'ordine atteso (dal migliore al peggiore)."""
    averaged = {
        post: mean(m[post] for m in map(post_means, runs) if post in m)
        for post in expected_order
        if any(post in post_means(run) for run in runs)
    }
    present = [p for p in expected_order if p in averaged]
    expected_scores = [len(present) - i for i in range(len(present))]
    return kendall_tau_b([averaged[p] for p in present], expected_scores)


def persona_consistency(runs: Sequence[Run]) -> float:
    """Quanto cambia il voto della stessa persona sullo stesso post tra run (più bassa è meglio)."""
    by_pair: dict[tuple[str, str], list[int]] = defaultdict(list)
    for run in runs:
        for r in run:
            by_pair[(r.persona_id, r.stimulus_id)].append(r.score)
    stds = [pstdev(v) for v in by_pair.values() if len(v) > 1]
    return mean(stds) if stds else 0.0


def persona_spread(runs: Sequence[Run]) -> float:
    """Quanto le personas differiscono tra loro sullo stesso post (più alta = meno omogenee)."""
    by_post: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for run in runs:
        for r in run:
            by_post[r.stimulus_id][r.persona_id].append(r.score)
    spreads = [pstdev([mean(s) for s in personas.values()]) for personas in by_post.values()]
    return mean(spreads) if spreads else 0.0


def distinct_objection_ratio(runs: Sequence[Run]) -> float:
    """Obiezioni diverse su obiezioni totali (1 = tutte diverse, 0 = nessuna obiezione)."""
    objections = [o.strip().lower() for run in runs for r in run for o in r.objections]
    return len(set(objections)) / len(objections) if objections else 0.0

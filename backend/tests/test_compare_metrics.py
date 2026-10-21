import pytest

from app.models import Response
from scripts.compare_metrics import (
    distinct_objection_ratio,
    expected_tau,
    kendall_tau_b,
    mean_pairwise_tau,
    persona_consistency,
    persona_spread,
    post_std,
    spread,
    top1_agreement,
)


def _run(
    scores: dict[tuple[str, str], int], objections: dict[tuple[str, str], list[str]] | None = None
):
    objections = objections or {}
    return [
        Response(
            persona_id=persona,
            stimulus_id=post,
            thought="t",
            said="s",
            score=score,
            objections=objections.get((persona, post), []),
        )
        for (persona, post), score in scores.items()
    ]


# Due personas, tre post: p1 a=5 b=3 c=1 (poi varia a seconda del run).
RUN_A = _run(
    {("p1", "a"): 5, ("p2", "a"): 5, ("p1", "b"): 3, ("p2", "b"): 3, ("p1", "c"): 1, ("p2", "c"): 1}
)
RUN_SAME = RUN_A
RUN_REVERSED = _run(
    {("p1", "a"): 1, ("p2", "a"): 1, ("p1", "b"): 3, ("p2", "b"): 3, ("p1", "c"): 5, ("p2", "c"): 5}
)


def test_kendall_tau_b_perfect_and_reversed() -> None:
    assert kendall_tau_b([3, 2, 1], [30, 20, 10]) == pytest.approx(1.0)
    assert kendall_tau_b([3, 2, 1], [10, 20, 30]) == pytest.approx(-1.0)


def test_kendall_tau_b_handles_ties_and_constant_vectors() -> None:
    assert kendall_tau_b([1, 1, 1], [1, 2, 3]) is None
    assert 0 < kendall_tau_b([3, 3, 1], [3, 2, 1]) < 1


def test_identical_runs_are_fully_stable() -> None:
    runs = [RUN_A, RUN_SAME, RUN_A]
    assert mean_pairwise_tau(runs) == pytest.approx(1.0)
    assert top1_agreement(runs) == 1.0
    assert post_std(runs) == 0.0
    assert persona_consistency(runs) == 0.0


def test_reversed_run_lowers_stability() -> None:
    runs = [RUN_A, RUN_REVERSED]
    assert mean_pairwise_tau(runs) == pytest.approx(-1.0)
    assert top1_agreement(runs) == 0.5
    assert post_std(runs) > 0
    assert persona_consistency(runs) > 0


def test_spread_is_gap_between_best_and_worst_post() -> None:
    assert spread([RUN_A]) == 4.0
    flat = _run({("p1", "a"): 3, ("p1", "b"): 3})
    assert spread([flat]) == 0.0


def test_expected_tau_compares_with_expected_order() -> None:
    assert expected_tau([RUN_A, RUN_A], ["a", "b", "c"]) == pytest.approx(1.0)
    assert expected_tau([RUN_REVERSED], ["a", "b", "c"]) == pytest.approx(-1.0)


def test_persona_spread_is_higher_when_personas_disagree() -> None:
    same = _run({("p1", "a"): 3, ("p2", "a"): 3})
    different = _run({("p1", "a"): 1, ("p2", "a"): 5})
    assert persona_spread([same]) == 0.0
    assert persona_spread([different]) > 0


def test_distinct_objection_ratio() -> None:
    repeated = _run(
        {("p1", "a"): 2, ("p2", "a"): 2},
        {("p1", "a"): ["troppo generico"], ("p2", "a"): ["Troppo generico"]},
    )
    varied = _run(
        {("p1", "a"): 2, ("p2", "a"): 2},
        {("p1", "a"): ["troppo generico"], ("p2", "a"): ["manca il costo"]},
    )
    assert distinct_objection_ratio([repeated]) == 0.5
    assert distinct_objection_ratio([varied]) == 1.0
    assert distinct_objection_ratio([RUN_A]) == 0.0

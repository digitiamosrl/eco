from app.models import Response, Stimulus
from app.report.aggregate import aggregate


def _stimulus(label: str) -> Stimulus:
    return Stimulus(id=f"variante-{label.lower()}", kind="post", variant_label=label, text="x")


def _response(stimulus: Stimulus, persona: str, score: int, objections: list[str]) -> Response:
    return Response(
        persona_id=persona,
        stimulus_id=stimulus.id,
        thought="x",
        said="x",
        score=score,
        objections=objections,
    )


A, B, C = _stimulus("A"), _stimulus("B"), _stimulus("C")
RESPONSES = [
    _response(A, "p1", 5, ["Prezzo alto", "Tono freddo"]),
    _response(A, "p2", 4, ["Prezzo alto"]),
    _response(B, "p1", 3, ["Troppo lungo"]),
    _response(B, "p2", 3, []),
    _response(C, "p1", 5, []),
    _response(C, "p2", 4, []),
]


def test_mean_and_distribution_per_stimulus() -> None:
    stats = {s.stimulus.id: s for s in aggregate([A, B, C], RESPONSES)}
    assert stats["variante-a"].mean_score == 4.5
    assert stats["variante-b"].mean_score == 3.0
    assert stats["variante-a"].score_distribution == {"1": 0, "2": 0, "3": 0, "4": 1, "5": 1}
    assert sum(stats["variante-b"].score_distribution.values()) == 2


def test_rank_is_by_mean_descending_and_ties_keep_variant_order() -> None:
    ranked = aggregate([A, B, C], RESPONSES)
    assert [s.stimulus.id for s in ranked] == ["variante-a", "variante-c", "variante-b"]
    assert [s.rank for s in ranked] == [1, 2, 3]


def test_objections_are_most_frequent_first_without_duplicates() -> None:
    stats = {s.stimulus.id: s for s in aggregate([A, B, C], RESPONSES)}
    assert stats["variante-a"].objections == ("Prezzo alto", "Tono freddo")
    assert stats["variante-c"].objections == ()


def test_objections_are_capped_at_five() -> None:
    many = [_response(A, f"p{i}", 3, [f"obiezione {i}"]) for i in range(7)]
    (only,) = aggregate([A], many)
    assert len(only.objections) == 5
    assert len(set(only.objections)) == 5


def test_mean_is_rounded_to_two_decimals() -> None:
    three = [_response(A, f"p{i}", s, []) for i, s in enumerate([5, 4, 4])]
    (only,) = aggregate([A], three)
    assert only.mean_score == 4.33

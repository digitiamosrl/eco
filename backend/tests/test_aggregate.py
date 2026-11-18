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


def _screen(index: int) -> Stimulus:
    return Stimulus(
        id=f"s{index}", kind="prototype_screen", flow_id="f", screen_index=index, page_structure="x"
    )


def _screen_response(
    stimulus: Stimulus, persona: str, score: int, abandon: bool, misunderstood: list[str]
) -> Response:
    return Response(
        persona_id=persona,
        stimulus_id=stimulus.id,
        thought="x",
        said="x",
        score=score,
        objections=[],
        misunderstood=misunderstood,
        would_abandon=abandon,
    )


S0, S1, S2 = _screen(0), _screen(1), _screen(2)
SCREEN_RESPONSES = [
    _screen_response(S0, "p1", 4, False, []),
    _screen_response(S0, "p2", 4, False, []),
    _screen_response(S1, "p1", 2, True, ["Cosa vuol dire «piano»?"]),
    _screen_response(S1, "p2", 3, True, ["Cosa vuol dire «piano»?", "Il prezzo è mensile?"]),
    _screen_response(S2, "p1", 3, False, []),
    _screen_response(S2, "p2", 2, True, []),
]


def test_screens_rank_by_abandons_then_lowest_score() -> None:
    ranking = aggregate([S0, S1, S2], SCREEN_RESPONSES)
    assert [s.stimulus.id for s in ranking] == ["s1", "s2", "s0"]
    assert [s.abandon_count for s in ranking] == [2, 1, 0]


def test_screens_collect_misunderstood_by_frequency() -> None:
    critical = aggregate([S0, S1, S2], SCREEN_RESPONSES)[0]
    assert critical.misunderstood == ("Cosa vuol dire «piano»?", "Il prezzo è mensile?")


def test_posts_have_no_abandon_count() -> None:
    assert all(stats.abandon_count is None for stats in aggregate([A, B, C], RESPONSES))


def test_near_identical_objections_count_as_one() -> None:
    responses = [
        _response(A, "p1", 2, ["Troppo generico."]),
        _response(A, "p2", 2, ["troppo generico"]),
        _response(A, "p3", 2, ["  Troppo  generico! "]),
        _response(A, "p4", 2, ["Manca un esempio"]),
        _response(A, "p5", 2, ["Manca un esempio."]),
        _response(A, "p6", 2, ["Prezzo alto"]),
    ]
    [stats] = aggregate([A], responses)
    assert stats.objections == ("Troppo generico.", "Manca un esempio", "Prezzo alto")

import json
from pathlib import Path

import pytest

from app.personas.audience import (
    DECISION_SENIORITIES,
    blend,
    company_size_of,
    pool_weights,
    quota,
    region_of,
)
from app.personas.sampler import is_coherent, sample_attributes

AUDIENCE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "processed" / "linkedin_audience.json"
)
AUDIENCE = json.loads(AUDIENCE_PATH.read_text(encoding="utf-8"))


def test_blend_averages_normalised_distributions() -> None:
    result = blend({"a": 90, "b": 10}, {"a": 1, "b": 3})
    assert result == pytest.approx({"a": 0.575, "b": 0.425})
    assert sum(result.values()) == pytest.approx(1.0)


def test_quota_follows_weights_and_sums_to_n() -> None:
    result = quota({"a": 0.5, "b": 0.3, "c": 0.2}, 10)
    assert sorted(result) == ["a"] * 5 + ["b"] * 3 + ["c"] * 2
    assert len(quota({"a": 1 / 3, "b": 1 / 3, "c": 1 / 3}, 10)) == 10


def test_quota_is_deterministic_on_ties() -> None:
    weights = {"a": 1 / 3, "b": 1 / 3, "c": 1 / 3}
    assert quota(weights, 10) == quota(weights, 10)


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("1", "micro"),
        ("2-10", "micro"),
        ("11-50", "piccola"),
        ("51-200", "media"),
        ("201-500", "grande"),
        ("10001+", "grande"),
    ],
)
def test_company_size_buckets(label: str, expected: str) -> None:
    assert company_size_of(label) == expected


def test_company_size_rejects_unknown_label() -> None:
    with pytest.raises(KeyError):
        company_size_of("tanti")


def test_region_of_maps_italian_areas_and_drops_foreign_ones() -> None:
    assert region_of("Greater Milan Metropolitan Area, Italy") == "Lombardia"
    assert region_of("Florence, Italy Metropolitan Area, Italy") == "Toscana"
    assert region_of("Greater Padova (Padua) Metropolitan Area, Italy") == "Veneto"
    assert region_of("Greater Bengaluru Area, India") is None


def test_every_italian_location_in_the_export_has_a_region() -> None:
    for source in ("followers", "visitors"):
        for location in AUDIENCE[source]["location"]:
            if location.endswith("Italy"):
                assert region_of(location), location


def test_pool_weights_cover_the_whole_audience() -> None:
    weights = pool_weights(AUDIENCE)
    assert set(weights) == {"seniority", "company_size", "job_function", "industry", "region"}
    for distribution in weights.values():
        assert sum(distribution.values()) == pytest.approx(1.0)
    assert set(weights["company_size"]) == {"micro", "piccola", "media", "grande"}


def test_pool_weights_can_keep_only_decision_makers() -> None:
    weights = pool_weights(AUDIENCE, decision_makers_only=True)
    assert set(weights["seniority"]) <= DECISION_SENIORITIES


def test_sampled_marginals_match_the_quotas() -> None:
    weights = pool_weights(AUDIENCE)
    people = sample_attributes(weights, 40, seed=1)
    assert len(people) == 40
    for dimension in ("seniority", "company_size", "region"):
        counts: dict[str, int] = {}
        for person in people:
            value = getattr(person, dimension)
            counts[value] = counts.get(value, 0) + 1
        assert sorted(counts.values()) == sorted(
            quota(weights[dimension], 40).count(v) for v in set(quota(weights[dimension], 40))
        )


def test_sampling_is_reproducible_and_coherent() -> None:
    weights = pool_weights(AUDIENCE)
    first = sample_attributes(weights, 30, seed=7)
    assert first == sample_attributes(weights, 30, seed=7)
    assert first != sample_attributes(weights, 30, seed=8)
    assert all(is_coherent(person) for person in first)


def test_owner_of_a_large_company_is_not_coherent() -> None:
    weights = {
        "seniority": {"Owner": 1.0},
        "company_size": {"grande": 1.0},
        "job_function": {"Sales": 1.0},
        "industry": {"Retail": 1.0},
        "region": {"Lombardia": 1.0},
    }
    with pytest.raises(ValueError, match="coerent"):
        sample_attributes(weights, 3, seed=1)


def test_personas_are_loaded_from_a_custom_file(tmp_path) -> None:
    from app.loaders import load_personas

    custom = tmp_path / "pool.json"
    custom.write_text(
        json.dumps(
            [
                {
                    "id": "x1",
                    "role": "Titolare, Vendite",
                    "sector": "Retail",
                    "company_size": "grande",
                    "region": "Lazio",
                    "profile": "Profilo di prova.",
                }
            ]
        ),
        encoding="utf-8",
    )
    assert [p.id for p in load_personas(str(custom))] == ["x1"]
    assert len(load_personas("")) == 6  # senza percorso: le fixture


def test_a_missing_personas_file_is_an_explicit_error() -> None:
    from app.loaders import load_personas

    with pytest.raises(FileNotFoundError):
        load_personas("data/processed/non-esiste.json")

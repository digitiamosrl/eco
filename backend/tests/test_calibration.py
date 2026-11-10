import json
from pathlib import Path

import pytest

from app.report.calibration import compute_fidelity, kendall_tau_b, load_fidelity


def test_fidelity_is_tau_on_shared_posts() -> None:
    fidelity = compute_fidelity(
        {"a": 4.0, "b": 3.0, "c": 2.0, "solo-panel": 5.0},
        {"a": 100, "b": 50, "c": 10, "solo-reale": 1},
        "3 post pubblicati",
    )
    assert fidelity is not None
    assert fidelity.score == 1.0
    assert fidelity.basis == "3 post pubblicati"


def test_fidelity_is_negative_when_ranking_is_reversed() -> None:
    fidelity = compute_fidelity({"a": 1, "b": 2, "c": 3}, {"a": 9, "b": 5, "c": 1}, "x")
    assert fidelity is not None and fidelity.score == -1.0


def test_fidelity_is_none_without_variation() -> None:
    assert compute_fidelity({"a": 3, "b": 3}, {"a": 1, "b": 2}, "x") is None
    assert compute_fidelity({}, {}, "x") is None


def test_kendall_is_still_exported_for_scripts() -> None:
    assert kendall_tau_b([3, 2, 1], [30, 20, 10]) == pytest.approx(1.0)


def test_load_fidelity_reads_file(tmp_path: Path) -> None:
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps({"score": 0.4, "basis": "12 post"}), "utf-8")
    fidelity = load_fidelity(path)
    assert fidelity is not None and fidelity.score == 0.4


def test_load_fidelity_missing_or_invalid_is_none(tmp_path: Path) -> None:
    assert load_fidelity(tmp_path / "assente.json") is None
    broken = tmp_path / "rotto.json"
    broken.write_text(json.dumps({"score": 7, "basis": "x"}), "utf-8")
    assert load_fidelity(broken) is None

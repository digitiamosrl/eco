import json
from pathlib import Path

import pytest

from app.api.personas import PERSONAS
from app.models import Persona, Response, Stimulus
from scripts.calibrate import (
    PublishedPost,
    calibrate,
    describe_basis,
    engagement_rate,
    load_posts,
)

pytestmark = pytest.mark.anyio


def _post(post_id: str, reactions: int, published_at: str = "2026-01-15") -> PublishedPost:
    return PublishedPost(
        id=post_id,
        text=f"Testo del post {post_id}",
        published_at=published_at,
        impressions=1000,
        reactions=reactions,
        comments=0,
        reposts=0,
    )


class _ScoreByPost:
    """Ogni persona dà a un post il voto indicato; i post in `broken` falliscono sempre."""

    def __init__(self, scores: dict[str, int], broken: frozenset[str] = frozenset()) -> None:
        self.scores = scores
        self.broken = broken

    async def respond(self, persona: Persona, stimulus: Stimulus) -> Response:
        if stimulus.id in self.broken:
            raise RuntimeError("servizio giù")
        return Response(
            persona_id=persona.id,
            stimulus_id=stimulus.id,
            thought="Pensiero",
            said="Detto",
            score=self.scores[stimulus.id],
            objections=[],
            action="scroll",
        )


POSTS = [_post(f"p{i}", reactions=10 * i, published_at=f"2026-0{i}-10") for i in range(1, 6)]


def test_engagement_rate_counts_all_interactions_over_impressions() -> None:
    post = PublishedPost(
        id="a",
        text="x",
        published_at="2026-01-01",
        impressions=200,
        reactions=10,
        comments=5,
        reposts=5,
    )
    assert engagement_rate(post) == pytest.approx(0.1)


async def test_calibrate_matches_engagement_order() -> None:
    responder = _ScoreByPost({f"p{i}": i for i in range(1, 6)})
    fidelity, failed = await calibrate(POSTS, responder, PERSONAS[:3], concurrency=4)
    assert fidelity.score == 1.0
    assert failed == 0
    assert fidelity.basis.startswith("5 post Digitiamo pubblicati")


async def test_calibrate_skips_failed_posts_and_counts_them() -> None:
    posts = [*POSTS, _post("p6", reactions=60)]
    responder = _ScoreByPost({f"p{i}": min(i, 5) for i in range(1, 7)}, frozenset({"p6"}))
    fidelity, failed = await calibrate(posts, responder, PERSONAS[:2], concurrency=4)
    assert failed == 2
    assert fidelity.basis.startswith("5 post")


async def test_calibrate_refuses_too_few_posts() -> None:
    responder = _ScoreByPost({f"p{i}": i for i in range(1, 6)})
    with pytest.raises(ValueError, match="almeno"):
        await calibrate(POSTS[:4], responder, PERSONAS[:2], concurrency=4)


def test_basis_names_the_period_in_italian() -> None:
    posts = [_post("a", 1, "2025-10-03"), _post("b", 2, "2026-09-20")]
    assert describe_basis(posts) == "2 post Digitiamo pubblicati, ott 2025–set 2026"


def test_load_posts_rejects_zero_impressions(tmp_path: Path) -> None:
    path = tmp_path / "posts.json"
    raw = _post("a", 1).model_dump(mode="json")
    path.write_text(json.dumps([{**raw, "impressions": 0}]), "utf-8")
    with pytest.raises(ValueError):
        load_posts(path)


def test_load_posts_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = tmp_path / "posts.json"
    raw = _post("a", 1).model_dump(mode="json")
    path.write_text(json.dumps([raw, raw]), "utf-8")
    with pytest.raises(ValueError, match="duplicat"):
        load_posts(path)

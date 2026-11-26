"""Calibrazione: il panel classifica i post Digitiamo già pubblicati e si confronta con
l'engagement reale. Scrive `calibration.json` ({score, basis}), che ogni report legge.

Non gira in pytest. Uso, da backend/ con OPENROUTER_API_KEY e PERSONA_MODEL nel .env:
    python -m scripts.calibrate

Il file dei post (versionato, `data/processed/published_posts.json`) è una lista di
oggetti come `PublishedPost`; `image` è un percorso relativo al file stesso.
Solo testi pubblici e conteggi aggregati: nessun dato personale.
"""

import argparse
import asyncio
import json
from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from statistics import mean

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from app.config import REPO_ROOT, settings
from app.engine.responder import Responder, build_responder
from app.engine.runner import _ask  # stesso retry e stessa validazione del runner
from app.models import Fidelity, Persona, Stimulus
from app.report.calibration import compute_fidelity
from app.uploads import (
    Upload,
    attachment_kind,
    delete_uploads,
    make_upload,
    save_uploads,
    upload_url,
)

# Con meno post il tau di Kendall oscilla troppo per dire qualcosa.
MIN_POSTS = 5
DEFAULT_POSTS = REPO_ROOT / "data" / "processed" / "published_posts.json"
_MONTHS = ("gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic")


class PublishedPost(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    image: str | None = None
    published_at: date
    impressions: int = Field(gt=0)
    reactions: int = Field(ge=0)
    comments: int = Field(ge=0)
    reposts: int = Field(ge=0)


def load_posts(path: Path) -> list[PublishedPost]:
    posts = TypeAdapter(list[PublishedPost]).validate_json(path.read_bytes())
    ids = [post.id for post in posts]
    if len(set(ids)) != len(ids):
        raise ValueError("Id dei post duplicati nel file")
    return posts


def engagement_rate(post: PublishedPost) -> float:
    """Tasso, non conteggio: i post vecchi hanno avuto meno follower a cui arrivare."""
    return (post.reactions + post.comments + post.reposts) / post.impressions


def _month(day: date) -> str:
    return f"{_MONTHS[day.month - 1]} {day.year}"


def describe_basis(posts: Sequence[PublishedPost]) -> str:
    days = sorted(post.published_at for post in posts)
    return f"{len(posts)} post Digitiamo pubblicati, {_month(days[0])}–{_month(days[-1])}"


async def _panel_scores(
    posts: Sequence[PublishedPost],
    stimuli: dict[str, Stimulus],
    responder: Responder,
    personas: Sequence[Persona],
    concurrency: int,
) -> tuple[dict[str, list[int]], int]:
    """Voti per post. Una coppia che fallisce si salta e si conta, non ferma la calibrazione."""
    semaphore = asyncio.Semaphore(concurrency)

    async def one(persona: Persona, post: PublishedPost) -> tuple[str, int | None]:
        try:
            # Evento nuovo per ogni coppia: un fallimento non deve fermare le altre.
            response = await _ask(responder, semaphore, asyncio.Event(), persona, stimuli[post.id])
        except Exception as error:
            print(f"Saltato {persona.id} / {post.id}: {error}")
            return post.id, None
        return post.id, None if response is None else response.score

    results = await asyncio.gather(*(one(p, post) for p in personas for post in posts))
    scores: dict[str, list[int]] = defaultdict(list)
    for post_id, score in results:
        if score is not None:
            scores[post_id].append(score)
    failed = sum(score is None for _, score in results)
    return scores, failed


async def calibrate(
    posts: Sequence[PublishedPost],
    responder: Responder,
    personas: Sequence[Persona],
    concurrency: int,
    stimuli: dict[str, Stimulus] | None = None,
) -> tuple[Fidelity, int]:
    """Fidelity sui post con almeno una risposta, più il numero di risposte fallite."""
    stimuli = stimuli or {p.id: Stimulus(id=p.id, kind="post", text=p.text) for p in posts}
    scores, failed = await _panel_scores(posts, stimuli, responder, personas, concurrency)
    answered = [post for post in posts if scores.get(post.id)]
    if len(answered) < MIN_POSTS:
        raise ValueError(f"Servono almeno {MIN_POSTS} post con risposte, ne ho {len(answered)}")
    fidelity = compute_fidelity(
        {post.id: mean(scores[post.id]) for post in answered},
        {post.id: engagement_rate(post) for post in answered},
        describe_basis(answered),
    )
    if fidelity is None:
        raise ValueError("Il panel ha dato lo stesso voto medio a tutti i post: niente ranking")
    for post in sorted(answered, key=lambda p: -mean(scores[p.id])):
        print(f"{mean(scores[post.id]):.2f}  {engagement_rate(post):.3%}  {post.id}")
    return fidelity, failed


def _stimuli_with_images(
    posts: Sequence[PublishedPost], base_dir: Path
) -> tuple[dict[str, Stimulus], list[Upload]]:
    """Le immagini passano dalla cartella upload, come nei test veri, così il responder le legge."""
    uploads = {p.id: make_upload((base_dir / p.image).read_bytes()) for p in posts if p.image}
    stimuli = {
        p.id: Stimulus(
            id=p.id,
            kind="post",
            text=p.text,
            image_url=upload_url(uploads.get(p.id)),
            attachment_kind=attachment_kind(uploads.get(p.id)),
        )
        for p in posts
    }
    return stimuli, list(uploads.values())


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--posts", type=Path, default=DEFAULT_POSTS)
    parser.add_argument("--out", type=Path, default=Path(settings.calibration_path))
    parser.add_argument("--concurrency", type=int, default=settings.panel_concurrency)
    args = parser.parse_args()
    if not settings.openrouter_api_key:
        print("Serve OPENROUTER_API_KEY nel file .env.")
        return 1
    from app.api.personas import PERSONAS  # qui: carica il pool scelto da PERSONAS_PATH

    posts = load_posts(args.posts)
    stimuli, uploads = _stimuli_with_images(posts, args.posts.parent)
    save_uploads(uploads)
    try:
        fidelity, failed = await calibrate(
            posts, build_responder(), PERSONAS, args.concurrency, stimuli
        )
    finally:
        delete_uploads(uploads)
    args.out.write_text(json.dumps(fidelity.model_dump(), ensure_ascii=False) + "\n", "utf-8")
    print(f"Fidelity {fidelity.score} ({fidelity.basis}), risposte fallite: {failed}")
    print(f"Scritto {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

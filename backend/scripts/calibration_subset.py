"""Sottoinsieme per ricalibrare con le immagini: i post con engagement più alto e più basso.

L'export LinkedIn non ha le immagini: arrivano a mano in una cartella, una per riga della
tabella nell'issue #31 (`01.png`, `07.jpg`, ...; PDF per i caroselli). La cartella resta
fuori dal repository: le immagini possono mostrare persone.

Uso, da backend/:
    python -m scripts.calibration_subset ../data/calibration_images
    python -m scripts.calibrate --posts ../data/calibration_images/posts.json
"""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from scripts.calibrate import DEFAULT_POSTS, PublishedPost, engagement_rate, load_posts

PER_SIDE = 10
SUBSET_NAME = "posts.json"
_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}


def select_extremes(posts: Sequence[PublishedPost], per_side: int) -> list[PublishedPost]:
    """Gli estremi rendono visibile in fretta se il panel distingue; ordine per data = righe."""
    ranked = sorted(posts, key=engagement_rate, reverse=True)
    if len(ranked) <= 2 * per_side:
        picked = ranked
    else:
        picked = ranked[:per_side] + ranked[-per_side:]
    return sorted(picked, key=lambda p: p.published_at)


def attach_images(posts: Sequence[PublishedPost], folder: Path) -> list[PublishedPost]:
    """`07.png` va al post della riga 7. Riga senza file: il post resta solo testo."""
    files = sorted(
        path
        for path in folder.iterdir()
        if path.suffix.lower() in _SUFFIXES and path.stem.isdigit()
    )
    by_row: dict[int, str] = {}
    for path in files:
        row = int(path.stem)
        if row in by_row:
            # Le immagini le carica a mano qualcuno: meglio fermarsi che sceglierne una a caso.
            raise ValueError(f"Due file per la riga {row}: {by_row[row]} e {path.name}")
        by_row[row] = path.name
    return [post.model_copy(update={"image": by_row.get(row)}) for row, post in enumerate(posts, 1)]


def write_subset(posts: Sequence[PublishedPost], folder: Path) -> Path:
    """Nella cartella delle immagini, così `image` resta relativo al file come vuole calibrate."""
    out = folder / SUBSET_NAME
    data = [post.model_dump(mode="json") for post in posts]
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("images", type=Path, help="cartella con 01.png, 02.jpg, ...")
    parser.add_argument("--posts", type=Path, default=DEFAULT_POSTS)
    parser.add_argument("--per-side", type=int, default=PER_SIDE)
    args = parser.parse_args()
    if not args.images.is_dir():
        print(f"Cartella non trovata: {args.images}")
        return 1
    picked = attach_images(select_extremes(load_posts(args.posts), args.per_side), args.images)
    for row, post in enumerate(picked, 1):
        print(f"{row:02d}  {post.published_at}  {post.image or 'solo testo'}  {post.id}")
    with_image = sum(post.image is not None for post in picked)
    out = write_subset(picked, args.images)
    print(f"{with_image}/{len(picked)} post con immagine. Scritto {out}")
    # Stessi post due volte, solo testo e con immagini: è il confronto che dice se contano.
    note = f"i {args.per_side} con più e i {args.per_side} con meno engagement"
    print("Confronto, da backend/:")
    print(f'  python -m scripts.calibrate --posts {out} --no-images --note "{note}, solo testo"')
    print(f'  python -m scripts.calibrate --posts {out} --note "{note}, con immagini"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

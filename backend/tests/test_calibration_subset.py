import json
from pathlib import Path

from scripts.calibrate import PublishedPost, _stimuli_with_images, load_posts
from scripts.calibration_subset import attach_images, select_extremes, write_subset


def _post(post_id: str, reactions: int, published_at: str) -> PublishedPost:
    return PublishedPost(
        id=post_id,
        text=f"Testo {post_id}",
        published_at=published_at,
        impressions=100,
        reactions=reactions,
        comments=0,
        reposts=0,
    )


# Engagement crescente con l'indice, date in ordine inverso.
POSTS = [_post(f"p{i}", reactions=i, published_at=f"2026-01-{30 - i:02d}") for i in range(10)]


def test_select_extremes_takes_top_and_bottom_sorted_by_date() -> None:
    picked = select_extremes(POSTS, per_side=2)
    assert [p.id for p in picked] == ["p9", "p8", "p1", "p0"]


def test_select_extremes_keeps_all_when_too_few() -> None:
    assert len(select_extremes(POSTS[:3], per_side=2)) == 3


def test_attach_images_maps_row_numbers_and_skips_missing(tmp_path: Path) -> None:
    (tmp_path / "01.png").write_bytes(b"x")
    (tmp_path / "3.jpg").write_bytes(b"x")
    (tmp_path / "note.txt").write_bytes(b"x")
    picked = select_extremes(POSTS, per_side=2)
    result = attach_images(picked, tmp_path)
    assert [p.image for p in result] == ["01.png", None, "3.jpg", None]
    assert all(p.image is None for p in picked)


def test_write_subset_is_loadable_with_paths_relative_to_the_file(tmp_path: Path) -> None:
    (tmp_path / "02.pdf").write_bytes(b"x")
    picked = attach_images(select_extremes(POSTS, per_side=1), tmp_path)
    out = write_subset(picked, tmp_path)
    loaded = load_posts(out)
    assert [p.image for p in loaded] == [None, "02.pdf"]
    assert json.loads(out.read_text("utf-8"))[1]["published_at"] == "2026-01-30"


def test_stimuli_carry_image_or_pdf_kind(tmp_path: Path) -> None:
    (tmp_path / "01.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "02.pdf").write_bytes(b"%PDF-1.4")
    picked = attach_images(select_extremes(POSTS, per_side=2), tmp_path)
    stimuli, uploads = _stimuli_with_images(picked, tmp_path)
    kinds = [stimuli[p.id].attachment_kind for p in picked]
    assert kinds == ["image", "pdf", None, None]
    assert len(uploads) == 2

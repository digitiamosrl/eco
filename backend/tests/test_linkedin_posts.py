import json
from pathlib import Path

import pytest

from scripts.calibrate import load_posts
from scripts.linkedin_posts import convert

EN_EXPORT = """All posts,,,,,,,,,
Post title,Post link,Posted by,Created date,Campaign name,Impressions,Clicks,Likes,Comments,Reposts
Caso cliente,u/activity:111,Mario R,03/12/2026,,"1,840",30,42,6,3
Post sponsorizzato,u/activity:222,Mario R,03/15/2026,Campagna Q1,9000,100,80,2,1
Post senza dati,u/activity:333,Mario R,03/20/2026,,0,0,0,0,0
"""

IT_EXPORT = (
    "Titolo del post;Link del post;Pubblicato da;Data di creazione;Nome campagna;"
    "Impressioni;Reazioni;Commenti;Diffusioni post\n"
    "Webinar sull'AI;u/activity:444;Mario R;12/03/2026;;1.200;20;1;0\n"
)


def test_english_export_keeps_organic_posts_with_impressions(tmp_path: Path) -> None:
    source = tmp_path / "export.csv"
    source.write_text(EN_EXPORT, "utf-8")
    posts = convert(source)
    assert [p["id"] for p in posts] == ["post-111"]
    assert posts[0] == {
        "id": "post-111",
        "text": "Caso cliente",
        "published_at": "2026-03-12",
        "impressions": 1840,
        "reactions": 42,
        "comments": 6,
        "reposts": 3,
    }


def test_output_never_contains_the_author(tmp_path: Path) -> None:
    source = tmp_path / "export.csv"
    source.write_text(EN_EXPORT, "utf-8")
    assert "Mario R" not in json.dumps(convert(source))


def test_italian_export_reads_day_first_dates_and_dot_thousands(tmp_path: Path) -> None:
    source = tmp_path / "export.csv"
    source.write_text(IT_EXPORT, "utf-8")
    [post] = convert(source)
    assert post["published_at"] == "2026-03-12"
    assert post["impressions"] == 1200


def test_converted_file_is_valid_calibration_input(tmp_path: Path) -> None:
    source = tmp_path / "export.csv"
    source.write_text(EN_EXPORT, "utf-8")
    target = tmp_path / "published_posts.json"
    target.write_text(json.dumps(convert(source)), "utf-8")
    assert load_posts(target)[0].reactions == 42


def test_unknown_columns_name_what_is_missing(tmp_path: Path) -> None:
    source = tmp_path / "export.csv"
    source.write_text("a,b\n1,2\n", "utf-8")
    with pytest.raises(ValueError, match="impressioni"):
        convert(source)


def test_xls_cells_become_the_same_text_as_in_a_csv() -> None:
    from xlrd import XL_CELL_DATE, XL_CELL_NUMBER, XL_CELL_TEXT
    from xlrd.sheet import Cell

    from scripts.linkedin_posts import _cell_text

    # Nell'xls i conteggi sono float e le date numeri seriali di Excel.
    assert _cell_text(Cell(XL_CELL_NUMBER, 1840.0), 0) == "1840"
    assert _cell_text(Cell(XL_CELL_DATE, 46093.0), 0) == "2026-03-12"
    assert _cell_text(Cell(XL_CELL_TEXT, "Caso cliente"), 0) == "Caso cliente"


def test_the_posts_sheet_is_found_among_the_others() -> None:
    from scripts.linkedin_posts import _posts_sheet

    metrics = [["Data", "Impressioni (organiche)"], ["03/12/2026", "10"]]
    posts = EN_EXPORT.splitlines()
    import csv

    start, _, rows = _posts_sheet([metrics, list(csv.reader(posts))])
    assert rows[start][0] == "Post title"

"""Converte l'export dei post della pagina LinkedIn (.xls o CSV) nell'input della calibrazione.

Da LinkedIn: pagina Digitiamo → Analytics → Contenuti → Esporta; il file .xls va così com'è
in data/raw/ (non versionato): lo script trova da solo il foglio dei post. Poi, da backend/:
    python -m scripts.linkedin_posts ../data/raw/linkedin_posts.xls

Scrive data/processed/published_posts.json con solo testo, data e conteggi aggregati:
autore e link non escono mai. Restano fuori i post sponsorizzati (hanno una campagna,
quindi un pubblico pagato) e quelli senza impressioni.
"""

import argparse
import csv
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import xlrd

from app.config import REPO_ROOT

DEFAULT_OUT = REPO_ROOT / "data" / "processed" / "published_posts.json"
# Colonna dell'export → nomi possibili, in inglese e in italiano.
COLUMNS = {
    "text": ("post title", "titolo del post"),
    "link": ("post link", "link del post"),
    "date": ("created date", "data di creazione"),
    "campaign": ("campaign name", "nome della campagna", "nome campagna"),
    "impressions": ("impressions", "impressioni"),
    "reactions": ("likes", "reactions", "reazioni", "mi piace"),
    "comments": ("comments", "commenti"),
    "reposts": ("reposts", "shares", "diffusioni post", "condivisioni", "repost"),
}
_REQUIRED = ("text", "date", "impressions", "reactions", "comments", "reposts")
_REQUIRED_IT = {
    "text": "titolo del post",
    "date": "data di creazione",
    "impressions": "impressioni",
    "reactions": "reazioni",
    "comments": "commenti",
    "reposts": "diffusioni post",
}


def _cell_text(cell: xlrd.sheet.Cell, datemode: int) -> str:
    """Il testo che avrebbe la cella in un CSV: conteggi interi, date in formato ISO."""
    if cell.ctype == xlrd.XL_CELL_DATE:
        return xlrd.xldate_as_datetime(cell.value, datemode).date().isoformat()
    if cell.ctype == xlrd.XL_CELL_NUMBER and float(cell.value).is_integer():
        return str(int(cell.value))
    return str(cell.value)


def _sheets(source: Path) -> list[list[list[str]]]:
    """L'export di LinkedIn è un .xls con più fogli; un CSV è un foglio solo."""
    if source.suffix.lower() == ".xls":
        book = xlrd.open_workbook(source)
        return [
            [[_cell_text(c, book.datemode) for c in sheet.row(r)] for r in range(sheet.nrows)]
            for sheet in book.sheets()
        ]
    text = source.read_text("utf-8-sig")
    delimiter = ";" if text.count(";") > text.count(",") else ","
    return [list(csv.reader(text.splitlines(), delimiter=delimiter))]


def _posts_sheet(sheets: list[list[list[str]]]) -> tuple[int, dict[str, int], list[list[str]]]:
    """Il primo foglio con l'intestazione dei post (gli altri sono metriche giornaliere)."""
    for rows in sheets:
        try:
            start, columns = _header(rows)
        except ValueError as exc:
            if "Colonne mancanti" in str(exc):
                raise
            continue
        return start, columns, rows
    raise ValueError("Nessun foglio con i post nell'export: manca la colonna impressioni")


def _header(rows: list[list[str]]) -> tuple[int, dict[str, int]]:
    """La riga di intestazione è la prima che contiene la colonna delle impressioni."""
    for number, row in enumerate(rows):
        names = [cell.strip().lower() for cell in row]
        found = {
            key: names.index(alias)
            for key, aliases in COLUMNS.items()
            for alias in aliases
            if alias in names
        }
        if "impressions" in found:
            missing = [_REQUIRED_IT[k] for k in _REQUIRED if k not in found]
            if missing:
                raise ValueError(f"Colonne mancanti nell'export: {', '.join(missing)}")
            return number, found
    raise ValueError("Nessuna colonna impressioni nell'export: è il foglio dei post?")


def _count(value: str) -> int:
    """'1,840', '1.840' e '1 840' sono tutti 1840: i conteggi non hanno decimali."""
    digits = re.sub(r"[^\d]", "", value)
    return int(digits) if digits else 0


def _date(value: str, day_first: bool) -> date:
    value = value.strip().split(" ")[0]
    if "-" in value:
        return date.fromisoformat(value)
    return datetime.strptime(value, "%d/%m/%Y" if day_first else "%m/%d/%Y").date()


def _post_id(link: str, published_at: date, number: int) -> str:
    activity = re.search(r"(\d+)\D*$", link)
    return f"post-{activity.group(1)}" if activity else f"post-{published_at}-{number}"


def convert(source: Path) -> list[dict[str, Any]]:
    start, columns, rows = _posts_sheet(_sheets(source))
    day_first = rows[start][columns["impressions"]].strip().lower() == "impressioni"
    posts = []
    for number, row in enumerate(rows[start + 1 :]):
        cell = {
            key: row[index].strip() if index < len(row) else "" for key, index in columns.items()
        }
        impressions = _count(cell["impressions"])
        if cell.get("campaign") or impressions == 0 or not cell["text"]:
            continue
        published_at = _date(cell["date"], day_first)
        posts.append(
            {
                "id": _post_id(cell.get("link", ""), published_at, number),
                "text": cell["text"],
                "published_at": published_at.isoformat(),
                "impressions": impressions,
                "reactions": _count(cell["reactions"]),
                "comments": _count(cell["comments"]),
                "reposts": _count(cell["reposts"]),
            }
        )
    return posts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    posts = convert(args.source)
    args.out.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"{len(posts)} post organici scritti in {args.out}")
    print("Controlla i testi: se l'export li tronca, incolla il testo completo a mano.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

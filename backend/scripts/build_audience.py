"""Estrae le distribuzioni aggregate dagli export Analytics della pagina LinkedIn.

Legge i file .xls dei follower e dei visitatori e scrive data/processed/linkedin_audience.json:
solo conteggi per categoria, nessun dato personale. Richiede xlrd, che non è in
requirements.txt (serve solo qui): installarlo in un venv a parte.

    python backend/scripts/build_audience.py FOLLOWERS.xls VISITORS.xls
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import xlrd

SHEETS = {
    "seniority": "Seniority",
    "company_size": "Company size",
    "job_function": "Job function",
    "industry": "Industry",
    "location": "Location",
}
OUTPUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "linkedin_audience.json"


def _counts(book: xlrd.book.Book, sheet: str) -> dict[str, int]:
    rows = book.sheet_by_name(sheet)
    return {rows.cell_value(r, 0): int(rows.cell_value(r, 1)) for r in range(1, rows.nrows)}


def _period(book: xlrd.book.Book) -> tuple[str, str]:
    rows = book.sheet_by_index(0)
    days = [datetime.strptime(rows.cell_value(r, 0), "%m/%d/%Y") for r in range(1, rows.nrows)]
    return min(days).date().isoformat(), max(days).date().isoformat()


def main(followers_path: str, visitors_path: str) -> None:
    followers, visitors = xlrd.open_workbook(followers_path), xlrd.open_workbook(visitors_path)
    start, end = _period(followers)
    audience = {
        "source": f"Export Analytics pagina LinkedIn Digitiamo, {start} - {end}",
        "followers": {key: _counts(followers, name) for key, name in SHEETS.items()},
        "visitors": {key: _counts(visitors, name) for key, name in SHEETS.items()},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(audience, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Scritto {OUTPUT}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])

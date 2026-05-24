"""
Phase 2 of the NFL data pipeline.

Scrapes every Wikipedia NFL Draft page from 1936–2025 and extracts
player → college pairs. This fills in college data for essentially
every notable NFL player who was drafted (virtually all of them).

The NFL draft started in 1936. Wikipedia has a consistent table
structure for every year with 'Player' and 'College' columns.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/scrape_nfl_draft_colleges_wiki.py

Output: src/data/raw/nfl_draft_college_enrichment.csv

Resume: re-running skips years already in the output file.
"""

import requests
import pandas as pd
from io import StringIO
import re
import csv
import time
from pathlib import Path

START_YEAR = 1936
END_YEAR   = 2025
OUT_FILE   = "src/data/raw/nfl_draft_college_enrichment.csv"
DELAY      = 1.5   # seconds between Wikipedia requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )
}

# Terms that indicate a high school / junior college that isn't a 4-yr university
HS_TERMS = ["high school", " hs", " h.s.", "prep school", "academy"]

# Wikipedia sometimes uses multi-row headers or merges columns.
# These are all the column names we look for (case-insensitive).
PLAYER_COLS  = {"player"}
COLLEGE_COLS = {"college", "school", "college/university"}


# ─── Helpers ────────────────────────────────────────────────────────────────

def clean_cell(val) -> str:
    s = str(val).strip()
    # Remove Wikipedia footnote markers like [1], [R1 – 3], †, ‡, *
    s = re.sub(r"\[\w[^\]]*\]", "", s)
    s = re.sub(r"[†‡\*]", "", s)
    return s.strip()


def is_high_school(school: str) -> bool:
    low = school.lower()
    return any(t in low for t in HS_TERMS)


def find_col(columns: list, targets: set) -> str | None:
    for col in columns:
        if str(col).strip().lower() in targets:
            return col
    return None


# ─── Load already-processed years (for resume) ──────────────────────────────

done_years: set[int] = set()
rows: list[dict]     = []

if Path(OUT_FILE).exists():
    existing = pd.read_csv(OUT_FILE)
    done_years = set(existing["draft_year"].dropna().astype(int).tolist())
    rows = existing.to_dict("records")
    print(f"Resuming: {len(done_years)} years already done, {len(rows)} rows loaded")


# ─── Scrape each draft year ─────────────────────────────────────────────────

for year in range(START_YEAR, END_YEAR + 1):
    if year in done_years:
        continue

    url = f"https://en.wikipedia.org/wiki/{year}_NFL_draft"
    print(f"Scraping {year}…", end=" ", flush=True)

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        tables = pd.read_html(StringIO(r.text))
    except Exception as e:
        print(f"FAILED — {e}")
        time.sleep(DELAY)
        continue

    year_rows = 0

    for table in tables:
        # Flatten multi-level column headers (Wikipedia sometimes nests them)
        if isinstance(table.columns, pd.MultiIndex):
            table.columns = [" ".join(str(c) for c in col).strip() for col in table.columns]

        cols = list(table.columns)
        player_col  = find_col(cols, PLAYER_COLS)
        college_col = find_col(cols, COLLEGE_COLS)

        if not player_col or not college_col:
            continue

        for _, row in table.iterrows():
            player  = clean_cell(row[player_col])
            college = clean_cell(row[college_col])

            if not player or not college:
                continue
            if player.lower() in ("player", "nan", ""):
                continue
            if college.lower() in ("college", "school", "nan", ""):
                continue
            if is_high_school(college):
                continue

            rows.append({
                "player_name": player,
                "college":     college,
                "draft_year":  year,
                "source":      url,
            })
            year_rows += 1

    print(f"{year_rows} players found")
    time.sleep(DELAY)

# ─── Save ───────────────────────────────────────────────────────────────────

df = pd.DataFrame(rows).drop_duplicates(subset=["player_name", "college"])
df.to_csv(OUT_FILE, index=False)

print()
print("═" * 50)
print(f"Total rows:            {len(df):,}")
print(f"Unique players:        {df['player_name'].nunique():,}")
print(f"Draft years covered:   {df['draft_year'].min():.0f}–{df['draft_year'].max():.0f}")
print(f"Output: {OUT_FILE}")
print()

# Spot-checks
for name in ["Tom Brady", "Jerry Rice", "Lawrence Taylor", "Jim Brown",
             "Patrick Mahomes", "Joe Montana", "Peyton Manning"]:
    match = df[df["player_name"] == name]
    if not match.empty:
        row = match.iloc[0]
        print(f"  {name}: {row['college']}  (draft {int(row['draft_year'])})")
    else:
        print(f"  {name}: not found in draft data")

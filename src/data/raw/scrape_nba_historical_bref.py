"""
BRef historical roster scraper — fills all NBA seasons not covered by
all_seasons.csv (which starts from 1996-97).

Gaps being filled
─────────────────
  Charlotte Hornets  (CHH)  1989–1996   ← the scrape you couldn't finish
  Miami Heat         (MIA)  1989–1996
  Orlando Magic      (ORL)  1990–1996
  Minnesota T-Wolves (MIN)  1990–1996
  Toronto Raptors    (TOR)  1996        ← their first season only
  Vancouver Grizzlies(VAN)  1996        ← their first season only

Charlotte abbreviation map (BRef changes abbreviation as franchise moves):
  CHH  1989-2002  Original Charlotte Hornets
  NOH  2003-2013  New Orleans Hornets (moved 2002)
  NOK  2006       New Orleans/OKC Hornets (Katrina displacement)
  CHA  2005-2014  Charlotte Bobcats (new expansion franchise)
  CHO  2015-2026  Charlotte Hornets (Bobcats renamed)
  NOP  2014-2026  New Orleans Pelicans (Hornets renamed)
  → all_seasons.csv covers every NOH/NOK/NOP/CHA/CHO season already,
    so this script only scrapes the CHH 1989-1996 gap.

Resumable: already-scraped (team, year) pairs are skipped.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/scrape_nba_historical_bref.py

Output: src/data/raw/nba_historical_bref.csv
Then:   python3 src/data/raw/merge_nba_historical_bref.py
"""

import pandas as pd
import json
import time
import ssl
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

OUT_FILE      = "src/data/raw/nba_historical_bref.csv"
PROGRESS_FILE = "src/data/raw/nba_historical_bref_progress.json"
DELAY         = 3.5   # seconds between BRef requests

# ─── Scrape targets ──────────────────────────────────────────────────────────
# (bref_abbr, years_to_scrape, canonical_team_name)
# year = season-end year  (e.g. 1990 → 1989-90 season)
# Only seasons NOT already in all_seasons.csv (which starts 1996-97 = year 1997)

TARGETS = [
    # Charlotte Hornets — the ones you were missing
    ("CHH", list(range(1989, 1997)), "Charlotte Hornets"),

    # Other expansion teams missing their pre-1997 seasons
    ("MIA", list(range(1989, 1997)), "Miami Heat"),
    ("ORL", list(range(1990, 1997)), "Orlando Magic"),
    ("MIN", list(range(1990, 1997)), "Minnesota Timberwolves"),

    # Toronto and Vancouver only had one season before 1997
    ("TOR", [1996], "Toronto Raptors"),
    ("VAN", [1996], "Vancouver Grizzlies"),
]


# ─── Load progress ───────────────────────────────────────────────────────────

def load_progress():
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}   # {"{abbr}_{year}": True}

def save_progress(done: dict):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(done, f)

done = load_progress()
print(f"Already scraped: {len(done)} team-seasons")


# ─── Open output CSV ─────────────────────────────────────────────────────────

out_path = Path(OUT_FILE)
write_header = not out_path.exists() or out_path.stat().st_size == 0
out_f = open(OUT_FILE, "a", newline="", encoding="utf-8")

import csv
writer = csv.DictWriter(out_f, fieldnames=[
    "team", "season_end_year", "player_name", "number", "college"
])
if write_header:
    writer.writeheader()


# ─── Scrape ──────────────────────────────────────────────────────────────────

total_players = 0
skipped       = 0

for abbr, years, team_name in TARGETS:
    for year in years:
        key = f"{abbr}_{year}"

        if key in done:
            skipped += 1
            continue

        url = f"https://www.basketball-reference.com/teams/{abbr}/{year}.html"
        print(f"Scraping {team_name} {year-1}-{str(year)[-2:]} ({abbr})…", end=" ", flush=True)

        try:
            tables = pd.read_html(url)
            roster = tables[0]   # first table is always the roster

            season_count = 0
            for _, row in roster.iterrows():
                player = str(row.get("Player", "")).replace("*", "").strip()
                if not player or player.lower() in ("player", "nan", ""):
                    continue

                number  = str(row.get("No.", row.get("#", ""))).strip()
                college = str(row.get("College", "")).strip()

                number  = "" if number  in ("nan", "")  else number
                college = "" if college in ("nan", "nan", "") else college

                writer.writerow({
                    "team":            team_name,
                    "season_end_year": year,
                    "player_name":     player,
                    "number":          number,
                    "college":         college,
                })
                season_count += 1

            total_players += season_count
            done[key] = True
            save_progress(done)
            print(f"{season_count} players")

        except Exception as e:
            print(f"FAILED — {e}")
            # Don't mark done — will retry next run

        time.sleep(DELAY)

out_f.close()

print()
print("═" * 50)
print(f"New player-seasons scraped: {total_players:,}")
print(f"Team-seasons skipped (done): {skipped}")
print(f"Output: {OUT_FILE}")
print()
print("Next step:")
print("  python3 src/data/raw/merge_nba_historical_bref.py")

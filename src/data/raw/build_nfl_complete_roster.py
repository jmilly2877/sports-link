"""
Phase 1 of the NFL data pipeline.

Downloads ALL nflverse annual roster CSVs (1920–2025) and aggregates into a
single JSON: player → {teams, numbers, college (where nflverse has it)}.

nflverse has consistent coverage back to 1920 with: full_name, team,
jersey_number, college. College is reliable only from ~2010 onward, so
the Wikipedia draft script will fill the gaps.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/build_nfl_complete_roster.py

Output: src/data/raw/nfl_roster_complete.json
"""

import ssl
import json
import time
import pandas as pd
from collections import defaultdict

ssl._create_default_https_context = ssl._create_unverified_context

START_YEAR = 1920
END_YEAR   = 2025
OUT_FILE   = "src/data/raw/nfl_roster_complete.json"

# ─── Comprehensive team code → full name map ────────────────────────────────
# Where a code changed meaning over time, we use year-aware logic below.
# This covers the unambiguous codes:

TEAM_MAP = {
    # Current franchises
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",    # overridden for pre-1984 below
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB":  "Green Bay Packers",
    "HOU": "Houston Texans",      # overridden for Oilers era below
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "KC":  "Kansas City Chiefs",
    "LAC": "Los Angeles Chargers",
    "LA":  "Los Angeles Rams",    # overridden for 1960 below
    "LV":  "Las Vegas Raiders",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE":  "New England Patriots",
    "NO":  "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks",
    "SF":  "San Francisco 49ers",
    "TB":  "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",

    # Alternative codes used in certain nflverse years
    "ARZ": "Arizona Cardinals",
    "BLT": "Baltimore Ravens",
    "CLV": "Cleveland Browns",
    "HST": "Houston Texans",
    "SL":  "St. Louis Rams",

    # Historical / moved franchises
    "OAK": "Oakland Raiders",
    "RAI": "Los Angeles Raiders",
    "SD":  "San Diego Chargers",
    "STL": "St. Louis Rams",      # Cardinals left 1987; Rams arrived 1995
    "RAM": "Los Angeles Rams",
    "PHO": "Phoenix Cardinals",
    "CHC": "Chicago Cardinals",
    "CHB": "Chicago Bears",
    "CHR": "Chicago Rockets",     # AAFC
    "BOS": "Boston Patriots",     # overridden for earlier eras below
    "BRK": "Brooklyn Dodgers",
    "NYT": "New York Titans",
    "NYY": "New York Yanks",
    "NY":  "New York Giants",
    "TEX": "Dallas Texans",

    # Pre-merger / very old franchises
    "AKR": "Akron Pros",
    "CAN": "Canton Bulldogs",
    "COL": "Columbus Panhandles",
    "COW": "Dallas Cowboys",      # early AFL code
    "DAY": "Dayton Triangles",
    "DEC": "Decatur Staleys",
    "HAM": "Hammond Pros",
    "CHT": "Chicago Tigers",
    "MUN": "Muncie Flyers",
    "RI":  "Rock Island Independents",
    "ROC": "Rochester Jeffersons",
}


def resolve_team(code: str, year: int) -> str:
    """Year-aware team code resolution for codes that changed meaning."""
    code = str(code).strip()

    # Baltimore: Colts until 1983, then nothing, Ravens from 1996
    if code == "BAL":
        return "Baltimore Ravens" if year >= 1996 else "Baltimore Colts"

    # Houston: Oilers 1960-1996, Titans 1997-1998, then gone; new Texans 2002
    if code == "HOU":
        if year <= 1996:
            return "Houston Oilers"
        elif year <= 1998:
            return "Tennessee Oilers"
        else:
            return "Houston Texans"

    # Los Angeles: Rams played there 1946-1994 and 2016+; Chargers briefly in 1960
    if code == "LA":
        if year == 1960:
            return "Los Angeles Chargers"
        return "Los Angeles Rams"

    # STL: Cardinals were there until 1987 (→ PHO), Rams 1995-2015
    if code == "STL":
        return "St. Louis Cardinals" if year <= 1987 else "St. Louis Rams"

    # Boston: Redskins (1933-36), Yanks (1944-48), Patriots (1960-70)
    if code == "BOS":
        if year <= 1936:
            return "Boston Redskins"
        elif year <= 1948:
            return "Boston Yanks"
        else:
            return "Boston Patriots"

    # TEN: Oilers → Tennessee Oilers 1997-98 → Titans 1999+
    if code == "TEN":
        return "Tennessee Titans"

    return TEAM_MAP.get(code, code)   # fallback: return the raw code


# ─── Download and aggregate ─────────────────────────────────────────────────
#
# We aggregate in TWO passes to avoid name-collision bugs:
#
#   Pass 1: key by gsis_id (truly unique per player) — college stays tied
#           to the correct individual even when names collide.
#           Pre-2000 players have no gsis_id, so they fall back to name keying.
#
#   Pass 2: collapse gsis_id records → name records.
#           College is only carried over when it is UNAMBIGUOUS:
#           all same-name players attended the same school, OR only one of
#           them has a known college.  Genuine collisions (Jim Brown→UCLA
#           vs Jim Brown→Syracuse) get an empty college list rather than
#           a wrong one.

import re

def alpha_only(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())

# gsis_id-keyed records (modern, reliable)
# { gsis_id: {name, teams, numbers, college, espn_id} }
by_id: dict[str, dict] = {}

# name-keyed records (historical / no gsis_id)
# { name: {teams, numbers, college, espn_id} }
by_name: dict[str, dict] = defaultdict(lambda: {
    "teams": set(), "numbers": set(), "college": set(), "espn_id": None,
})

espn_ids: dict[str, int] = {}   # alpha_name → espn_id (for UDFA script)
failed_years = []

for year in range(START_YEAR, END_YEAR + 1):
    if year == END_YEAR:
        url = (
            "https://github.com/nflverse/nflverse-data/releases/download/"
            f"weekly_rosters/roster_weekly_{year}.csv"
        )
    else:
        url = (
            "https://github.com/nflverse/nflverse-data/releases/download/"
            f"rosters/roster_{year}.csv"
        )
    try:
        df = pd.read_csv(url, low_memory=False)
        count = 0

        for _, row in df.iterrows():
            name = str(row.get("full_name", "")).strip()
            if not name or name == "nan":
                continue

            team_code = str(row.get("team", "")).strip()
            team      = resolve_team(team_code, year) if team_code and team_code != "nan" else ""

            num = row.get("jersey_number")
            try:
                num = int(float(num)) if pd.notna(num) else None
            except (ValueError, TypeError):
                num = None

            college = str(row.get("college", "")).strip()
            college = college if college and college != "nan" else ""

            gsis_id = str(row.get("gsis_id", "")).strip()
            gsis_id = gsis_id if gsis_id and gsis_id != "nan" else ""

            espn_id = row.get("espn_id")
            espn_id = int(espn_id) if pd.notna(espn_id) else None

            if gsis_id:
                # Modern player — key by unique ID
                if gsis_id not in by_id:
                    by_id[gsis_id] = {
                        "name": name, "teams": set(), "numbers": set(),
                        "college": set(), "espn_id": None,
                    }
                entry = by_id[gsis_id]
                entry["name"] = name   # keep most recent name spelling
            else:
                # Historical player — fall back to name keying
                entry = by_name[name]

            if team:
                entry["teams"].add(team)
            if num is not None and num != 0:
                entry["numbers"].add(num)
            if college:
                entry["college"].add(college)
            if espn_id and entry["espn_id"] is None:
                entry["espn_id"] = espn_id
                espn_ids[alpha_only(name)] = espn_id

            count += 1

        print(f"{year}: {count:,} rows → {df['full_name'].dropna().nunique():,} unique players")

    except Exception as e:
        print(f"{year}: FAILED — {e}")
        failed_years.append(year)

    time.sleep(0.3)   # be polite to GitHub CDN

# ─── Pass 2: one output record per unique player ──────────────────────────────
#
# Every gsis_id → its own entry with full data (no blanking).
# Historical players (no gsis_id) → merged by name as before.
#
# Same-name players each keep all their own data.  Their `name` field stays
# identical (game logic uses it for linking), but `display_name` gets a team
# disambiguator appended:  "Josh Allen (BUF)" / "Josh Allen (JAX)".
#
# All collisions are also written to nfl_duplicate_names.csv for manual review.

from collections import defaultdict as _dd
import csv

# Team abbreviation to use in display_name disambiguator.
# Pick the "most notable" team per player = last team they played for.
CURRENT_TEAM_PRIORITY = [
    "Kansas City Chiefs","Buffalo Bills","San Francisco 49ers","Dallas Cowboys",
    "Philadelphia Eagles","Baltimore Ravens","Cincinnati Bengals","Miami Dolphins",
]

def primary_team_abbr(teams: set) -> str:
    """Return a short label for the most notable team in the set."""
    ABBR = {
        "Arizona Cardinals":"ARI","Atlanta Falcons":"ATL","Baltimore Ravens":"BAL",
        "Baltimore Colts":"BAL","Buffalo Bills":"BUF","Carolina Panthers":"CAR",
        "Chicago Bears":"CHI","Cincinnati Bengals":"CIN","Cleveland Browns":"CLE",
        "Dallas Cowboys":"DAL","Denver Broncos":"DEN","Detroit Lions":"DET",
        "Green Bay Packers":"GB","Houston Texans":"HOU","Houston Oilers":"HOU",
        "Indianapolis Colts":"IND","Jacksonville Jaguars":"JAX","Kansas City Chiefs":"KC",
        "Las Vegas Raiders":"LV","Los Angeles Chargers":"LAC","Los Angeles Rams":"LAR",
        "Miami Dolphins":"MIA","Minnesota Vikings":"MIN","New England Patriots":"NE",
        "New Orleans Saints":"NO","New York Giants":"NYG","New York Jets":"NYJ",
        "Oakland Raiders":"OAK","Philadelphia Eagles":"PHI","Pittsburgh Steelers":"PIT",
        "San Diego Chargers":"SD","Seattle Seahawks":"SEA","San Francisco 49ers":"SF",
        "Tampa Bay Buccaneers":"TB","Tennessee Titans":"TEN","Washington Commanders":"WAS",
        "St. Louis Rams":"STL","Phoenix Cardinals":"PHO","Boston Patriots":"BOS",
    }
    if not teams:
        return "?"
    # Prefer current/notable teams
    for t in CURRENT_TEAM_PRIORITY:
        if t in teams:
            return ABBR.get(t, t[:3].upper())
    # Fallback: alphabetically first team
    t = sorted(teams)[0]
    return ABBR.get(t, t[:3].upper())


# Group gsis_id records by name
name_groups: dict[str, list] = _dd(list)
for gsis_id, data in by_id.items():
    name_groups[alpha_only(data["name"])].append({**data, "_gsis": gsis_id})

# Historical players (no gsis_id) go in as a single merged record per name
for name, data in by_name.items():
    key = alpha_only(name)
    name_groups[key].append({**data, "name": name, "_gsis": None})

output        = []
duplicates    = []   # rows for the manual-review CSV

for alpha, group in name_groups.items():
    is_collision = len(group) > 1

    for d in group:
        name    = d["name"]
        teams   = d["teams"]
        numbers = d["numbers"]
        college = sorted(d["college"])
        espn_id = d.get("espn_id")
        gsis_id = d.get("_gsis", "")

        if is_collision:
            abbr         = primary_team_abbr(teams)
            display_name = f"{name} ({abbr})"
            duplicates.append({
                "name":         name,
                "display_name": display_name,
                "gsis_id":      gsis_id or "",
                "college":      "; ".join(college),
                "teams":        "; ".join(sorted(teams)),
                "numbers":      "; ".join(str(n) for n in sorted(numbers)),
            })
        else:
            display_name = name

        output.append({
            "name":         name,
            "display_name": display_name,
            "teams":        sorted(teams),
            "numbers":      sorted(int(n) for n in numbers if isinstance(n, (int, float))),
            "college":      college,
            "league":       "NFL",
            "espn_id":      espn_id,
        })

output.sort(key=lambda x: x["name"])

with open(OUT_FILE, "w") as f:
    json.dump(output, f, indent=2)

# Save espn_id lookup for the UDFA enrichment script
ESPNID_FILE = "src/data/raw/nfl_espn_ids.json"
with open(ESPNID_FILE, "w") as f:
    json.dump(espn_ids, f)

# Write duplicate-names report for manual review
DUP_FILE = "src/data/raw/nfl_duplicate_names.csv"
if duplicates:
    with open(DUP_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name","display_name","gsis_id","college","teams","numbers"
        ])
        writer.writeheader()
        writer.writerows(sorted(duplicates, key=lambda r: r["name"]))

collision_names = len(set(r["name"] for r in duplicates))
print()
print("═" * 50)
print(f"Total player entries:       {len(output):,}")
print(f"With college:               {sum(1 for p in output if p['college']):,}")
print(f"With numbers:               {sum(1 for p in output if p['numbers']):,}")
print(f"With ESPN ID:               {sum(1 for p in output if p.get('espn_id')):,}")
print(f"Name collisions found:      {collision_names:,}  → see {DUP_FILE}")
if failed_years:
    print(f"Failed years: {failed_years}")
print(f"Output:   {OUT_FILE}")
print(f"ESPN IDs: {ESPNID_FILE}")
print(f"Dupes:    {DUP_FILE}")

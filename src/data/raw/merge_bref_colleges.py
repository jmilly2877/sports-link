"""
Merge mlb_bref_colleges.csv into src/data/mlb_players.js.

Run this after scrape_mlb_colleges_comprehensive.py finishes.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/merge_bref_colleges.py

What it does:
  - Reads the scraped college results (player_name, college, bbref_id, source)
  - Matches each player by name to the MLB_PLAYERS array in mlb_players.js
  - Merges new colleges into the existing college[] array (no duplicates, stays sorted)
  - Writes mlb_players.js back in-place
  - Prints a summary of what changed
"""

import pandas as pd
import json
import re
from collections import defaultdict

MLB_FILE    = "src/data/mlb_players.js"
ENRICH_FILE = "src/data/raw/mlb_bref_colleges.csv"


# ─── Name normalization (same logic as the scraper) ──────────────────────────

def alpha_only(name: str) -> str:
    """Keep only letters, lowercase — handles A.J. vs AJ vs A. J. variants."""
    return re.sub(r"[^a-z]", "", name.lower())


# ─── Load mlb_players.js ────────────────────────────────────────────────────

with open(MLB_FILE) as f:
    raw = f.read()

players = json.loads(
    raw.replace("export const MLB_PLAYERS = ", "").rstrip(";\n")
)

print(f"Loaded {len(players):,} players from {MLB_FILE}")


# ─── Build enrichment map: alpha_name → set of colleges ─────────────────────

df = pd.read_csv(ENRICH_FILE)

# Drop blank rows
df = df.dropna(subset=["player_name", "college"])
df = df[df["player_name"].str.strip() != ""]
df = df[df["college"].str.strip() != ""]

college_map: dict[str, set[str]] = defaultdict(set)

for _, row in df.iterrows():
    name   = str(row["player_name"]).strip()
    college = str(row["college"]).strip()
    alpha  = alpha_only(name)
    college_map[alpha].add(college)

print(f"Loaded {len(df):,} rows from {ENRICH_FILE}")
print(f"Unique players with colleges: {len(college_map):,}")
print()


# ─── Merge into players ──────────────────────────────────────────────────────

updated = 0
new_colleges_added = 0
not_matched = []

for player in players:
    name  = player.get("name", "")
    alpha = alpha_only(name)

    if alpha not in college_map:
        continue

    new_colleges = college_map[alpha]
    existing     = set(player.get("college", []))
    before_count = len(existing)

    existing.update(new_colleges)
    player["college"] = sorted(existing)

    added = len(existing) - before_count
    if added > 0:
        updated += 1
        new_colleges_added += added

# Report players in enrichment file not matched in JS
for _, row in df.iterrows():
    name  = str(row["player_name"]).strip()
    alpha = alpha_only(name)
    if not any(alpha_only(p["name"]) == alpha for p in players):
        not_matched.append(name)

not_matched = list(dict.fromkeys(not_matched))  # deduplicate


# ─── Write mlb_players.js back ───────────────────────────────────────────────

with open(MLB_FILE, "w") as f:
    f.write("export const MLB_PLAYERS = ")
    json.dump(players, f, indent=2)
    f.write(";")

print(f"Players updated:        {updated:,}")
print(f"New college entries:    {new_colleges_added:,}")
if not_matched:
    print(f"Enrichment rows with no JS match: {len(not_matched)}")
    for n in not_matched[:10]:
        print(f"  - {n}")
    if len(not_matched) > 10:
        print(f"  … and {len(not_matched) - 10} more")
print()
print(f"Written: {MLB_FILE}")
print()


# ─── Spot-check a few known players ─────────────────────────────────────────

spot_checks = [
    "A.J. Achter",    # Michigan State — from our test run
    "A.J. Minter",    # Texas A&M
    "Aaron Judge",    # California State University, Fresno (if scraper found it)
    "AJ Pollock",     # Notre Dame
    "Clayton Kershaw",
]

print("Spot-checks:")
player_map = {p["name"]: p for p in players}
for name in spot_checks:
    p = player_map.get(name)
    if p:
        print(f"  {name}: {p.get('college', [])}")
    else:
        print(f"  {name}: NOT FOUND IN JS")

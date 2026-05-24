"""
Merges src/data/raw/nba_historical_bref.csv into src/data/nba_players.js.

Also fixes BRK → "Brooklyn Nets" and PHO → "Phoenix Suns" in
nba_recent_players.csv so those abbreviations don't creep back in if
the recent-players merge is re-run.

Safe to re-run (idempotent — uses sets internally).

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/merge_nba_historical_bref.py
"""

import json, csv, re
import pandas as pd
from pathlib import Path

NBA_FILE     = "src/data/nba_players.js"
BREF_FILE    = "src/data/raw/nba_historical_bref.csv"
RECENT_FILE  = "src/data/raw/nba_recent_players.csv"

# Abbreviations still raw in nba_recent_players.csv
RECENT_FIXES = {
    "BRK": "Brooklyn Nets",
    "PHO": "Phoenix Suns",
}

def alpha(name):
    return re.sub(r"[^a-z]", "", name.lower())


# ─── Load existing nba_players.js ────────────────────────────────────────────

with open(NBA_FILE) as f:
    raw = f.read()
players = json.loads(raw.replace("export const NBA_PLAYERS = ", "").rstrip(";\n"))
print(f"Loaded {len(players):,} existing players")

# Build dict keyed by alpha name for fast lookup
by_alpha: dict[str, dict] = {}
for p in players:
    key = alpha(p["name"])
    if key not in by_alpha:
        by_alpha[key] = p
    else:
        # Merge duplicate alpha-key entries (shouldn't happen but be safe)
        existing = by_alpha[key]
        existing["teams"]   = sorted(set(existing["teams"])   | set(p["teams"]))
        existing["college"] = sorted(set(existing["college"]) | set(p["college"]))
        existing["numbers"] = sorted(set(existing["numbers"]) | set(p.get("numbers", [])))


# ─── Merge historical BRef data ───────────────────────────────────────────────

if not Path(BREF_FILE).exists():
    print(f"No {BREF_FILE} found — run scrape_nba_historical_bref.py first")
else:
    bref_df = pd.read_csv(BREF_FILE)
    added_players = 0
    updated_players = 0

    for _, row in bref_df.iterrows():
        name    = str(row.get("player_name", "")).strip()
        team    = str(row.get("team", "")).strip()
        college = str(row.get("college", "")).strip()
        number  = str(row.get("number", "")).strip()

        if not name or name.lower() in ("nan", "player", ""):
            continue

        college = "" if college.lower() in ("nan", "") else college
        number  = "" if number.lower()  in ("nan", "") else number

        key = alpha(name)
        if key not in by_alpha:
            by_alpha[key] = {
                "name":    name,
                "teams":   [],
                "college": [],
                "numbers": [],
                "league":  "NBA",
            }
            added_players += 1
        else:
            updated_players += 1

        p = by_alpha[key]
        existing_teams   = set(p["teams"])
        existing_colleges = set(p["college"])
        existing_numbers  = set(p.get("numbers", []))

        if team:
            existing_teams.add(team)
        if college:
            existing_colleges.add(college)
        if number:
            # Convert to int if it's a clean jersey number
            try:
                existing_numbers.add(int(number))
            except ValueError:
                pass

        p["teams"]   = sorted(existing_teams)
        p["college"] = sorted(existing_colleges)
        p["numbers"] = sorted(existing_numbers)

    print(f"Historical BRef merge: {added_players} new players, {updated_players} updated")


# ─── Fix BRK / PHO in nba_recent_players.csv ─────────────────────────────────

if Path(RECENT_FILE).exists():
    recent_df = pd.read_csv(RECENT_FILE)
    changed = 0
    for old, new in RECENT_FIXES.items():
        mask = recent_df["team"] == old
        count = mask.sum()
        if count:
            recent_df.loc[mask, "team"] = new
            changed += count
            print(f"  Fixed {count} rows: {old!r} → {new!r} in nba_recent_players.csv")
    if changed:
        recent_df.to_csv(RECENT_FILE, index=False)
        print(f"  Saved nba_recent_players.csv ({changed} rows updated)")
    else:
        print("  nba_recent_players.csv already clean (no BRK/PHO found)")


# ─── Write output ─────────────────────────────────────────────────────────────

output = sorted(by_alpha.values(), key=lambda x: x["name"])

# Ensure every record has all fields
for p in output:
    p.setdefault("league", "NBA")
    p.setdefault("numbers", [])
    p.setdefault("display_name", p["name"])

with open(NBA_FILE, "w") as f:
    f.write("export const NBA_PLAYERS = ")
    json.dump(output, f, indent=2)
    f.write(";")

print(f"\nWrote {NBA_FILE}")
print(f"Total players: {len(output):,}")

# Spot-checks
checks = ["Alonzo Mourning", "Larry Johnson", "Muggsy Bogues",
          "Glen Rice", "Vlade Divac", "Baron Davis"]
print("\nCharlotte-era spot-checks:")
for name in checks:
    key = alpha(name)
    if key in by_alpha:
        p = by_alpha[key]
        cha_teams = [t for t in p["teams"] if "Charlotte" in t or "New Orleans" in t]
        print(f"  {name}: teams={cha_teams}, college={p['college'][:2]}")
    else:
        print(f"  {name}: NOT FOUND")

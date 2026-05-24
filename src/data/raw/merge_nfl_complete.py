"""
Phase 3 of the NFL data pipeline.

Merges all NFL data sources into src/data/nfl_players.js:

  Source A — nfl_roster_complete.json            (teams + numbers + some college)
  Source B — nfl_draft_college_enrichment.csv    (colleges for all drafted players)
  Source C — existing nfl_players.js             (preserves any manually curated data)
  Source D — nfl_espn_college_enrichment.csv     (UDFA colleges — optional)

Every player keeps their own full record — no data is blanked.
Same-name players each get a unique display_name like "Josh Allen (BUF)".
All name collisions are exported to nfl_duplicate_names.csv for manual review.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/merge_nfl_complete.py
"""

import json, re, csv
import pandas as pd
from pathlib import Path
from collections import defaultdict

ROSTER_FILE  = "src/data/raw/nfl_roster_complete.json"
DRAFT_FILE   = "src/data/raw/nfl_draft_college_enrichment.csv"
ESPN_FILE    = "src/data/raw/nfl_espn_college_enrichment.csv"
CURRENT_FILE = "src/data/nfl_players.js"
OUT_FILE     = "src/data/nfl_players.js"
DUP_FILE     = "src/data/raw/nfl_duplicate_names.csv"


# ─── Helpers ────────────────────────────────────────────────────────────────

def alpha(name: str) -> str:
    """Lowercase letters only — 'A.J. Cole' == 'AJ Cole' == 'ajcole'."""
    return re.sub(r"[^a-z]", "", name.lower())

def clean(c) -> str:
    c = re.sub(r"\[.*?\]", "", str(c))
    return re.sub(r"[†‡\*]", "", c).strip()

TEAM_ABBR = {
    "Arizona Cardinals":"ARI","Atlanta Falcons":"ATL","Baltimore Ravens":"BAL",
    "Baltimore Colts":"BAL","Buffalo Bills":"BUF","Carolina Panthers":"CAR",
    "Chicago Bears":"CHI","Cincinnati Bengals":"CIN","Cleveland Browns":"CLE",
    "Dallas Cowboys":"DAL","Denver Broncos":"DEN","Detroit Lions":"DET",
    "Green Bay Packers":"GB","Houston Texans":"HOU","Houston Oilers":"HOU",
    "Indianapolis Colts":"IND","Jacksonville Jaguars":"JAX",
    "Kansas City Chiefs":"KC","Las Vegas Raiders":"LV",
    "Los Angeles Chargers":"LAC","Los Angeles Rams":"LAR",
    "Miami Dolphins":"MIA","Minnesota Vikings":"MIN",
    "New England Patriots":"NE","New Orleans Saints":"NO",
    "New York Giants":"NYG","New York Jets":"NYJ",
    "Oakland Raiders":"OAK","Philadelphia Eagles":"PHI",
    "Pittsburgh Steelers":"PIT","San Diego Chargers":"SD",
    "Seattle Seahawks":"SEA","San Francisco 49ers":"SF",
    "St. Louis Rams":"STL","Tampa Bay Buccaneers":"TB",
    "Tennessee Titans":"TEN","Washington Commanders":"WAS",
    "Phoenix Cardinals":"PHO","Boston Patriots":"BOS",
    "New York Titans":"NYT",
}

def best_abbr(teams: set) -> str:
    if not teams:
        return "?"
    # prefer alphabetically last (roughly most recent in modern era)
    for t in sorted(teams, reverse=True):
        abbr = TEAM_ABBR.get(t)
        if abbr:
            return abbr
    return sorted(teams)[0][:3].upper()


# ─── Load sources ────────────────────────────────────────────────────────────

print("Loading sources…")

with open(ROSTER_FILE) as f:
    roster = json.load(f)
print(f"  Roster:  {len(roster):,} records")

draft_df = pd.read_csv(DRAFT_FILE)
draft_df["college"] = draft_df["college"].apply(clean)
print(f"  Draft:   {draft_df['player_name'].nunique():,} unique draft names")

with open(CURRENT_FILE) as f:
    raw = f.read()
current = json.loads(raw.replace("export const NFL_PLAYERS = ", "").rstrip(";\n"))
print(f"  Current: {len(current):,} existing JS players")

espn_df = None
if Path(ESPN_FILE).exists():
    espn_df = pd.read_csv(ESPN_FILE)
    espn_df["college"] = espn_df["college"].apply(clean)
    print(f"  ESPN:    {espn_df['player_name'].nunique():,} UDFA names")
else:
    print("  ESPN:    not found (run fetch_nfl_colleges_espn.py to add UDFA colleges)")


# ─── Build master record dict keyed by a stable unique key ──────────────────
# Key = alpha(name) + ":" + index within that name group (e.g. "joshallen:0")
# This lets us store same-name players as separate records.

# Step 1: group roster records by alpha name
alpha_groups: dict[str, list] = defaultdict(list)
for p in roster:
    alpha_groups[alpha(p["name"])].append(p)

# Also fold in any players from the current JS not in the roster
roster_alphas = set(alpha_groups.keys())
for p in current:
    a = alpha(p["name"])
    if a not in roster_alphas:
        alpha_groups[a].append(p)

# Step 2: build the working records dict
# records[uid] = {name, teams, numbers, college, _alpha}
records: dict[str, dict] = {}
counters: dict[str, int] = defaultdict(int)   # alpha → next index (O(1) uid gen)

for a, group in alpha_groups.items():
    # Deduplicate within a group: same gsis_id/espn_id = same player
    seen_ids: dict[str, str] = {}   # player id → uid
    for p in group:
        pid = str(p.get("gsis_id") or p.get("espn_id") or "")
        pid = pid if pid and pid != "nan" else ""

        if pid and pid in seen_ids:
            uid = seen_ids[pid]
        else:
            uid = f"{a}:{counters[a]}"
            counters[a] += 1
            if pid:
                seen_ids[pid] = uid

        if uid not in records:
            records[uid] = {
                "name":    p["name"],
                "teams":   set(p.get("teams",   [])),
                "numbers": set(p.get("numbers", [])),
                "college": set(p.get("college", [])),
                "_alpha":  a,
            }
        else:
            rec = records[uid]
            rec["teams"].update(p.get("teams", []))
            rec["numbers"].update(p.get("numbers", []))
            rec["college"].update(c for c in p.get("college", []) if c)

print(f"\nUnique player records after dedup: {len(records):,}")


# ─── Build fast alpha → [uid, …] lookup ─────────────────────────────────────

alpha_to_uids: dict[str, list] = defaultdict(list)
for uid, rec in records.items():
    alpha_to_uids[rec["_alpha"]].append(uid)


# ─── Apply college enrichment (O(1) per entry) ──────────────────────────────

def apply_colleges(name_col: pd.Series, college_col: pd.Series, label: str):
    """Add colleges from a Series pair into the matching records.

    For unambiguous players (unique name) → add directly.
    For same-name players → only add if the player already has that college
    (confirmation), or if exactly one same-name player has no college yet.
    Skips truly ambiguous cases to prevent cross-contamination.
    """
    added = 0
    new_stubs = 0
    skipped = 0
    for pname, college in zip(name_col, college_col):
        if not college or college == "nan":
            continue
        a = alpha(str(pname))
        uids = alpha_to_uids.get(a)
        if uids:
            if len(uids) == 1:
                # Unambiguous — only one player with this name
                records[uids[0]]["college"].add(college)
                added += 1
            else:
                # Multiple same-name players — be smart to avoid cross-contamination
                # Priority 1: add to any who already have this exact college
                matching = [uid for uid in uids if college in records[uid]["college"]]
                if matching:
                    for uid in matching:
                        records[uid]["college"].add(college)
                    added += len(matching)
                else:
                    # Priority 2: if exactly one player has no college yet, they're
                    # the most likely candidate (others already have known schools)
                    no_college_uids = [uid for uid in uids
                                       if not records[uid]["college"]]
                    if len(no_college_uids) == 1:
                        records[no_college_uids[0]]["college"].add(college)
                        added += 1
                    else:
                        # Truly ambiguous — skip rather than contaminate everyone
                        skipped += 1
        else:
            # Player not in any roster — create a stub
            uid = f"{a}:0"
            records[uid] = {
                "name":    str(pname).strip(),
                "teams":   set(),
                "numbers": set(),
                "college": {college},
                "_alpha":  a,
            }
            alpha_to_uids[a].append(uid)
            new_stubs += 1
    print(f"  {label}: enriched {added}, {new_stubs} new stubs, {skipped} skipped (ambiguous)")

apply_colleges(draft_df["player_name"], draft_df["college"], "Draft colleges")
if espn_df is not None:
    apply_colleges(espn_df["player_name"], espn_df["college"], "ESPN colleges")

# Carry over college data from existing JS — only reinforces colleges already
# confirmed by the roster or draft data.  Never spreads one player's college
# to a different same-name player.  (No-op until manual curation is done.)
for p in current:
    a = alpha(p["name"])
    uids = alpha_to_uids.get(a, [])
    if not uids:
        continue
    existing_colleges = [c for c in p.get("college", []) if c]
    # Always use smart per-college matching regardless of uid count —
    # this prevents contamination from historically merged records in the old JS.
    for college in existing_colleges:
        matching = [uid for uid in uids if college in records[uid]["college"]]
        if matching:
            for uid in matching:
                records[uid]["college"].add(college)


# ─── Assign display_name ─────────────────────────────────────────────────────

# Group uids by alpha name to find true same-name players
for a, uids in alpha_to_uids.items():
    if len(uids) == 1:
        uid = uids[0]
        records[uid]["display_name"] = records[uid]["name"]
    else:
        # Multiple real players share this name — disambiguate by primary team
        for uid in uids:
            rec   = records[uid]
            abbr  = best_abbr(rec["teams"])
            rec["display_name"] = f"{rec['name']} ({abbr})"


# ─── Build output list ───────────────────────────────────────────────────────

output      = []
duplicates  = []

for a, uids in alpha_to_uids.items():
    is_dup = len(uids) > 1
    for uid in uids:
        rec = records[uid]
        # Normalize colleges: split any "A; B" strings nflverse may have stored,
        # deduplicate, then sort.
        raw_colleges = (c for c in rec["college"] if c)
        split_colleges: set[str] = set()
        for c in raw_colleges:
            for part in c.split(";"):
                part = part.strip()
                if part:
                    split_colleges.add(part)

        entry = {
            "name":         rec["name"],
            "display_name": rec.get("display_name", rec["name"]),
            "teams":        sorted(rec["teams"]),
            "college":      sorted(split_colleges),
            "numbers":      sorted(int(n) for n in rec["numbers"]
                                   if isinstance(n, (int, float))),
            "league":       "NFL",
        }
        output.append(entry)

        if is_dup:
            duplicates.append({
                "name":         rec["name"],
                "display_name": rec.get("display_name", rec["name"]),
                "college":      "; ".join(sorted(c for c in rec["college"] if c)),
                "teams":        "; ".join(sorted(rec["teams"])),
                "numbers":      "; ".join(str(int(n)) for n in sorted(rec["numbers"])
                                          if isinstance(n, (int, float))),
            })

output.sort(key=lambda x: x["name"])


# ─── Write outputs ───────────────────────────────────────────────────────────

with open(OUT_FILE, "w") as f:
    f.write("export const NFL_PLAYERS = ")
    json.dump(output, f, indent=2)
    f.write(";")
print(f"\nWrote {OUT_FILE}")

with open(DUP_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "name", "display_name", "college", "teams", "numbers"
    ])
    writer.writeheader()
    writer.writerows(sorted(duplicates, key=lambda r: r["name"]))
print(f"Wrote {DUP_FILE}  ({len(duplicates)} duplicate entries, "
      f"{len(set(r['name'] for r in duplicates))} unique collision names)")


# ─── Summary ─────────────────────────────────────────────────────────────────

total        = len(output)
with_college = sum(1 for p in output if p["college"])
with_numbers = sum(1 for p in output if p["numbers"])

print()
print("═" * 50)
print(f"Total players:    {total:,}")
print(f"With college:     {with_college:,}  ({with_college/total*100:.1f}%)")
print(f"With numbers:     {with_numbers:,}  ({with_numbers/total*100:.1f}%)")
print(f"Name collisions:  {len(set(r['name'] for r in duplicates)):,}  → {DUP_FILE}")
print()

checks = ["Tom Brady", "Jerry Rice", "Jim Brown", "Patrick Mahomes",
          "Josh Allen", "Walter Payton", "Mike Williams", "Chris Jones"]
print("Spot-checks:")
for name in checks:
    matches = [p for p in output if p["name"] == name]
    for p in matches:
        print(f"  {p['display_name']}: college={p['college']}, #s={p['numbers'][:3]}")

"""
Phase 4 (optional) of the NFL data pipeline — UDFA college enrichment.

Run AFTER the main 3-script pipeline (build → wiki scrape → merge).

Targets players who still have no college data but have an ESPN ID in the
nflverse data. This catches:
  - Undrafted free agents (2010+) who weren't on Wikipedia draft pages
  - Any players the nflverse college field missed for 2010–2014

Sources:
  - nfl_espn_ids.json      (built by build_nfl_complete_roster.py)
  - nfl_players.js         (post-merge, to identify who is still missing)
  - ESPN Core API          (athlete profile → college $ref → college name)

The college name lookup is cached by ESPN college ID, so most players only
cost 1 API call each (the college name fetch happens once per ~500 unique
colleges, not once per player).

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/fetch_nfl_colleges_espn.py

  Re-running is safe: already-found players are skipped via the progress file.

Output: src/data/raw/nfl_espn_college_enrichment.csv
"""

import json
import re
import time
import csv
import requests
from pathlib import Path

ESPNID_FILE   = "src/data/raw/nfl_espn_ids.json"
NFL_JS_FILE   = "src/data/nfl_players.js"
OUT_FILE      = "src/data/raw/nfl_espn_college_enrichment.csv"
PROGRESS_FILE = "src/data/raw/nfl_espn_college_progress.json"

ATHLETE_URL   = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{id}?lang=en&region=us"
COLLEGE_URL   = "http://sports.core.api.espn.com/v2/colleges/{id}?lang=en&region=us"

DELAY         = 0.25   # seconds between ESPN requests (very permissive API)
BACKOFF       = 10.0

HEADERS = {"User-Agent": "Mozilla/5.0"}


# ─── Helpers ────────────────────────────────────────────────────────────────

def alpha_only(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


# ─── Load ESPN ID lookup ─────────────────────────────────────────────────────

with open(ESPNID_FILE) as f:
    espn_ids: dict[str, int] = json.load(f)   # alpha_name → espn_id

print(f"ESPN IDs available: {len(espn_ids):,} players")


# ─── Load current nfl_players.js to find who is missing college ──────────────

with open(NFL_JS_FILE) as f:
    raw = f.read()
players = json.loads(raw.replace("export const NFL_PLAYERS = ", "").rstrip(";\n"))

missing_college = [
    p for p in players
    if not p.get("college") or len(p["college"]) == 0
]
print(f"Players missing college in JS: {len(missing_college):,}")

# Filter to only those we have an ESPN ID for
targets = []
for p in missing_college:
    key = alpha_only(p["name"])
    if key in espn_ids:
        targets.append((p["name"], espn_ids[key]))

print(f"Of those, have ESPN ID:        {len(targets):,}")
print()


# ─── Load progress ───────────────────────────────────────────────────────────

def load_progress() -> dict:
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}

def save_progress(p: dict) -> None:
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f)

progress = load_progress()
print(f"Already processed: {len(progress):,}")


# ─── College name cache (college_id → name) ──────────────────────────────────

college_cache: dict[str, str] = {}

def get_college_name(college_ref_url: str) -> str | None:
    """Resolve a college $ref URL to a college name, cached by college ID."""
    # Extract ID from URL like http://…/colleges/221?lang=…
    m = re.search(r"/colleges/(\d+)", college_ref_url)
    if not m:
        return None
    college_id = m.group(1)

    if college_id in college_cache:
        return college_cache[college_id]

    try:
        r = requests.get(COLLEGE_URL.format(id=college_id), headers=HEADERS, timeout=10)
        if r.status_code == 200:
            name = r.json().get("name", "").strip()
            college_cache[college_id] = name
            time.sleep(DELAY)
            return name
    except Exception:
        pass
    return None


# ─── Open output CSV ─────────────────────────────────────────────────────────

out_path = Path(OUT_FILE)
write_header = not out_path.exists() or out_path.stat().st_size == 0
out_f = open(OUT_FILE, "a", newline="", encoding="utf-8")
writer = csv.DictWriter(out_f, fieldnames=["player_name", "college", "espn_id", "source"])
if write_header:
    writer.writeheader()


# ─── Main loop ───────────────────────────────────────────────────────────────

found = 0
no_college = 0
errors = 0
total = len(targets)

for i, (name, espn_id) in enumerate(targets):
    if name in progress:
        if progress[name].get("college"):
            found += 1
        continue

    athlete_url = ATHLETE_URL.format(id=espn_id)

    try:
        r = requests.get(athlete_url, headers=HEADERS, timeout=10)

        if r.status_code == 429:
            print(f"  [429] backing off {BACKOFF}s…")
            time.sleep(BACKOFF)
            r = requests.get(athlete_url, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            progress[name] = {"college": None, "espn_id": espn_id, "error": r.status_code}
            errors += 1
            time.sleep(DELAY)
            continue

        athlete = r.json()
        college_ref = athlete.get("college", {})
        time.sleep(DELAY)

    except Exception as e:
        print(f"  ERROR fetching {name} (id={espn_id}): {e}")
        progress[name] = {"college": None, "espn_id": espn_id, "error": str(e)}
        errors += 1
        time.sleep(DELAY)
        continue

    # Resolve college name
    college = None
    if isinstance(college_ref, dict) and "$ref" in college_ref:
        college = get_college_name(college_ref["$ref"])

    if college:
        found += 1
        writer.writerow({
            "player_name": name,
            "college":     college,
            "espn_id":     espn_id,
            "source":      athlete_url,
        })
        out_f.flush()
        if (i % 25) == 0 or found <= 10:
            print(f"[{i+1}/{total}] {name} → {college}")
    else:
        no_college += 1
        if (i % 100) == 0:
            print(f"[{i+1}/{total}] {name} → (no college in ESPN)")

    progress[name] = {"college": college, "espn_id": espn_id}

    if len(progress) % 50 == 0:
        save_progress(progress)

save_progress(progress)
out_f.close()

print()
print("═" * 50)
print(f"Total targeted:  {total:,}")
print(f"College found:   {found:,}")
print(f"No college:      {no_college:,}")
print(f"Errors:          {errors:,}")
print(f"Output:          {OUT_FILE}")
print()
print("Next: re-run merge_nfl_complete.py to fold these into nfl_players.js")
print("  (add nfl_espn_college_enrichment.csv as Source D in the merge script)")

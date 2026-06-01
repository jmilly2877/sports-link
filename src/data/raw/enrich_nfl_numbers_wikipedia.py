"""
Enriches NFL jersey numbers via the Wikipedia API.

For each player in nfl_players.js that currently has no jersey number,
this script:
  1. Searches Wikipedia for "{name} NFL football player"
  2. Validates the result title contains BOTH the first and last name
  3. Fetches the article wikitext
  4. Validates it's about an NFL player (NFL-related keywords)
  5. Validates article mentions at least one of the player's known teams
  6. Extracts |number = XX from the infobox

Safe to re-run — uses a progress cache to skip already-checked players.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/enrich_nfl_numbers_wikipedia.py

Runtime:
  Processes ~50 players/min with polite rate limiting.
  ~8,900 candidates → ~3 hours. Resumable with Ctrl-C.
"""

import json, re, ssl, time, urllib.request, urllib.parse
from pathlib import Path

ctx = ssl._create_unverified_context()

NFL_FILE = "src/data/nfl_players.js"
PROGRESS_FILE = "src/data/raw/wiki_nfl_progress.json"

HEADERS = {"User-Agent": "sports-link-research/1.0 (educational non-commercial project)"}

NFL_KEYWORDS = re.compile(
    r"National Football League|NFL Draft|quarterback|linebacker|running back"
    r"|wide receiver|defensive end|cornerback|safety|offensive lineman"
    r"|tight end|fullback|halfback|nose tackle|defensive tackle",
    re.IGNORECASE
)

# Short team name tokens for fuzzy team matching in wikitext
TEAM_TOKENS = {
    "Chicago Bears": ["Bears"],
    "New York Giants": ["Giants"],
    "Green Bay Packers": ["Packers"],
    "San Francisco 49ers": ["49ers"],
    "Dallas Cowboys": ["Cowboys"],
    "Miami Dolphins": ["Dolphins"],
    "Pittsburgh Steelers": ["Steelers"],
    "Minnesota Vikings": ["Vikings"],
    "Los Angeles Rams": ["Rams"],
    "Washington Commanders": ["Washington", "Redskins"],
    "New England Patriots": ["Patriots"],
    "Oakland Raiders": ["Raiders"],
    "Las Vegas Raiders": ["Raiders"],
    "Los Angeles Raiders": ["Raiders"],
    "Denver Broncos": ["Broncos"],
    "Kansas City Chiefs": ["Chiefs"],
    "Cleveland Browns": ["Browns"],
    "Philadelphia Eagles": ["Eagles"],
    "New Orleans Saints": ["Saints"],
    "Atlanta Falcons": ["Falcons"],
    "Seattle Seahawks": ["Seahawks"],
    "San Diego Chargers": ["Chargers"],
    "Los Angeles Chargers": ["Chargers"],
    "Indianapolis Colts": ["Colts"],
    "Baltimore Colts": ["Colts"],
    "New York Jets": ["Jets"],
    "Tampa Bay Buccaneers": ["Buccaneers"],
    "Detroit Lions": ["Lions"],
    "Houston Oilers": ["Oilers"],
    "Tennessee Oilers": ["Oilers"],
    "Tennessee Titans": ["Titans"],
    "Arizona Cardinals": ["Cardinals"],
    "St. Louis Cardinals": ["Cardinals"],
    "Chicago Cardinals": ["Cardinals"],
    "Cincinnati Bengals": ["Bengals"],
    "Buffalo Bills": ["Bills"],
    "Jacksonville Jaguars": ["Jaguars"],
    "Carolina Panthers": ["Panthers"],
    "Baltimore Ravens": ["Ravens"],
}


def alpha(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


LAST_429 = [0.0]

def wiki_get(url: str, retries: int = 5):
    for attempt in range(retries):
        wait_needed = LAST_429[0] + 30 - time.time()
        if wait_needed > 0:
            time.sleep(wait_needed)
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
                return json.loads(r.read())
        except Exception as e:
            msg = str(e)
            if "429" in msg:
                LAST_429[0] = time.time()
                wait = 30 * (attempt + 1)
                print(f"\n  Rate limited — waiting {wait}s...", flush=True)
                time.sleep(wait)
            elif attempt < retries - 1:
                time.sleep(3)
            else:
                raise


def name_in_title(player_name: str, wiki_title: str) -> bool:
    """Both first and last name must appear in the wiki title."""
    parts = player_name.strip().split()
    if len(parts) < 2:
        return False
    first = re.sub(r"[^a-z]", "", parts[0].lower())
    last = re.sub(r"[^a-z]", "", parts[-1].lower())
    title_a = re.sub(r"[^a-z]", "", wiki_title.lower())
    # Handle A.J. -> aj style matching
    return last in title_a and (first in title_a or len(first) <= 2)


def team_in_wikitext(player_teams: list, wikitext: str) -> bool:
    """Return True if at least one of the player's teams appears in the article."""
    if not player_teams:
        return True  # can't validate, accept
    for team in player_teams:
        tokens = TEAM_TOKENS.get(team, [team.split()[-1]])
        for tok in tokens:
            if tok in wikitext[:8000]:
                return True
    return False


# ─── Load players ─────────────────────────────────────────────────────────────

with open(NFL_FILE) as f:
    raw = f.read()
players = json.loads(raw.replace("export const NFL_PLAYERS = ", "").rstrip(";\n"))
by_alpha = {alpha(p["name"]): p for p in players}
print(f"Loaded {len(players):,} players")

# ─── Load progress cache ───────────────────────────────────────────────────────

progress: dict = {}
if Path(PROGRESS_FILE).exists():
    with open(PROGRESS_FILE) as f:
        progress = json.load(f)
print(f"Progress cache: {len(progress):,} players already processed")

# ─── Candidates: has college + teams, no number, not yet checked ──────────────

to_process = [
    p for p in players
    if not p.get("numbers")
    and p.get("college")            # has college data (more likely notable)
    and p.get("teams")              # has at least one team
    and p["name"] not in progress
    and len(p["name"].split()) >= 2
]
print(f"Players to look up: {len(to_process):,}")
if not to_process:
    print("All candidates already processed — nothing to do.")
    exit(0)

# ─── Main enrichment loop ─────────────────────────────────────────────────────

found = 0
checked = 0
save_every = 100

try:
    for i, player in enumerate(to_process):
        name = player["name"]
        teams = player.get("teams", [])
        checked += 1

        # Live progress counter (overwrites same line)
        print(f"\r  [{checked:,}/{len(to_process):,}] found {found} so far...  ", end="", flush=True)

        # ── Step 1: Search ──
        try:
            q = urllib.parse.quote(f"{name} NFL football player")
            url = (f"https://en.wikipedia.org/w/api.php"
                   f"?action=query&list=search&format=json&srlimit=1&srsearch={q}")
            data = wiki_get(url)
            results = data.get("query", {}).get("search", [])
        except Exception as e:
            progress[name] = f"search_error:{e}"
            time.sleep(2)
            continue

        if not results:
            progress[name] = "no_results"
            time.sleep(0.5)
            continue

        title = results[0]["title"]

        # Strict name match: both first AND last name must be in the title
        if not name_in_title(name, title):
            progress[name] = f"name_mismatch:{title}"
            time.sleep(0.5)
            continue

        time.sleep(0.8)  # between the two API calls

        # ── Step 2: Fetch wikitext ──
        try:
            q2 = urllib.parse.quote(title)
            url2 = (f"https://en.wikipedia.org/w/api.php"
                    f"?action=query&prop=revisions&rvprop=content&format=json&titles={q2}")
            data2 = wiki_get(url2)
            pages = data2.get("query", {}).get("pages", {})
            page = next(iter(pages.values()))
            wikitext = page.get("revisions", [{}])[0].get("*", "")
        except Exception as e:
            progress[name] = f"wikitext_error:{e}"
            time.sleep(2)
            continue

        # ── Step 3: Validate NFL context ──
        if not NFL_KEYWORDS.search(wikitext[:5000]):
            progress[name] = f"not_nfl:{title}"
            time.sleep(1)
            continue

        # ── Step 4: Validate team matches ──
        if not team_in_wikitext(teams, wikitext):
            progress[name] = f"team_mismatch:{title}"
            time.sleep(1)
            continue

        # ── Step 5: Extract jersey number ──
        m = re.search(
            r'\|\s*(?:jersey_number|number)\s*=\s*([0-9]+)',
            wikitext, re.IGNORECASE
        )
        if not m:
            progress[name] = f"no_number:{title}"
            time.sleep(1)
            continue

        num = int(m.group(1))
        if num == 0:
            progress[name] = f"number_zero:{title}"
            time.sleep(1)
            continue

        # ── Step 6: Apply ──
        key = alpha(name)
        if key in by_alpha:
            p = by_alpha[key]
            existing = set(p.get("numbers", []))
            if num not in existing:
                p["numbers"] = sorted(existing | {num})
                progress[name] = num
                found += 1
                print(f"  ✓ {name}: #{num}  ({title})")
            else:
                progress[name] = num  # already had it

        time.sleep(1)

        # ── Periodic save ──
        if checked % save_every == 0:
            with open(PROGRESS_FILE, "w") as f:
                json.dump(progress, f)
            total_hits = len([v for v in progress.values() if isinstance(v, int)])
            print(f"  [{checked:,}/{len(to_process):,}] new this run: {found}, "
                  f"total wiki hits: {total_hits}")

except KeyboardInterrupt:
    print("\nInterrupted — saving progress...")

# ─── Save progress ────────────────────────────────────────────────────────────

with open(PROGRESS_FILE, "w") as f:
    json.dump(progress, f)
print(f"Saved progress ({len(progress):,} entries)")

# ─── Write output ─────────────────────────────────────────────────────────────

if found > 0:
    players.sort(key=lambda x: x["name"])
    with open(NFL_FILE, "w") as f:
        f.write("export const NFL_PLAYERS = ")
        json.dump(players, f, indent=2)
        f.write(";")

    total_with_numbers = sum(1 for p in players if p.get("numbers"))
    print(f"\nWrote {NFL_FILE}")
    print(f"New numbers added this run: {found}")
    print(f"Players with numbers: {total_with_numbers:,} / {len(players):,} "
          f"({total_with_numbers/len(players)*100:.1f}%)")
else:
    print("\nNo new numbers found — file unchanged.")

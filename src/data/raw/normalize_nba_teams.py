"""
NBA team name normalization script.

Cleans up nba_players.js in place:
  1. Expands abbreviations  (BRK, PHO, NOK, CHH …)
  2. Expands single-word partial names  (Hawks, Knicks, Rockets …)
  3. Removes junk entries  (All-Star game team names, player name leaks,
     international clubs that snuck in from box-score data)
  4. Deduplicates teams per player after normalization

Safe to re-run — idempotent.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/normalize_nba_teams.py
"""

import json, re

NBA_FILE = "src/data/nba_players.js"

# ─── Canonical mapping ────────────────────────────────────────────────────────
# Every known non-canonical team string → canonical full name.
# Order doesn't matter; all keys are checked for every team string.

NORMALIZE = {
    # ── Abbreviations that slipped through team_map ──
    "BRK":  "Brooklyn Nets",
    "BKN":  "Brooklyn Nets",
    "PHO":  "Phoenix Suns",
    "PHX":  "Phoenix Suns",
    "Phoenix": "Phoenix Suns",
    "NOK":  "New Orleans Hornets",      # 2005-06 displaced to OKC; same franchise
    "CHH":  "Charlotte Hornets",
    "CHA":  "Charlotte Hornets",
    "CHO":  "Charlotte Hornets",
    "NOH":  "New Orleans Hornets",
    "NJN":  "New Jersey Nets",
    "SEA":  "Seattle SuperSonics",
    "VAN":  "Vancouver Grizzlies",
    "NOP":  "New Orleans Pelicans",
    "GSW":  "Golden State Warriors",
    "SAS":  "San Antonio Spurs",
    "NYK":  "New York Knicks",
    "OKC":  "Oklahoma City Thunder",
    "ORL":  "Orlando Magic",
    "POR":  "Portland Trail Blazers",
    "SAC":  "Sacramento Kings",
    "TOR":  "Toronto Raptors",
    "UTA":  "Utah Jazz",
    "WAS":  "Washington Wizards",
    "MIL":  "Milwaukee Bucks",
    "MIN":  "Minnesota Timberwolves",
    "MEM":  "Memphis Grizzlies",
    "MIA":  "Miami Heat",
    "LAC":  "Los Angeles Clippers",
    "LAL":  "Los Angeles Lakers",
    "IND":  "Indiana Pacers",
    "HOU":  "Houston Rockets",
    "DET":  "Detroit Pistons",
    "DEN":  "Denver Nuggets",
    "DAL":  "Dallas Mavericks",
    "CLE":  "Cleveland Cavaliers",
    "CHI":  "Chicago Bulls",
    "ATL":  "Atlanta Hawks",
    "BOS":  "Boston Celtics",

    # ── Single-word partial names (from box-score data) ──
    # Modern franchises
    "76ers":        "Philadelphia 76ers",
    "Bobcats":      "Charlotte Bobcats",
    "Bucks":        "Milwaukee Bucks",
    "Bulls":        "Chicago Bulls",
    "Cavaliers":    "Cleveland Cavaliers",
    "Celtics":      "Boston Celtics",
    "Clippers":     "Los Angeles Clippers",
    "Grizzlies":    "Memphis Grizzlies",
    "Hawks":        "Atlanta Hawks",
    "Heat":         "Miami Heat",
    "Hornets":      "Charlotte Hornets",
    "Jazz":         "Utah Jazz",
    "Kings":        "Sacramento Kings",
    "Knicks":       "New York Knicks",
    "Lakers":       "Los Angeles Lakers",
    "Magic":        "Orlando Magic",
    "Mavericks":    "Dallas Mavericks",
    "Nets":         "Brooklyn Nets",
    "Nuggets":      "Denver Nuggets",
    "Pacers":       "Indiana Pacers",
    "Pelicans":     "New Orleans Pelicans",
    "Pistons":      "Detroit Pistons",
    "Raptors":      "Toronto Raptors",
    "Rockets":      "Houston Rockets",
    "Spurs":        "San Antonio Spurs",
    "SuperSonics":  "Seattle SuperSonics",
    "Thunder":      "Oklahoma City Thunder",
    "Timberwolves": "Minnesota Timberwolves",
    "Trailblazers": "Portland Trail Blazers",
    "Trail Blazers": "Portland Trail Blazers",
    "Suns":         "Phoenix Suns",
    "Warriors":     "Golden State Warriors",
    "Wizards":      "Washington Wizards",

    # Historical franchises (keep distinct from modern city names)
    "Blackhawks":   "Tri-Cities Blackhawks",
    "Braves":       "Buffalo Braves",
    "Bullets":      "Washington Bullets",
    "Nationals":    "Syracuse Nationals",
    "Packers":      "Chicago Packers",
    "Royals":       "Cincinnati Royals",
    "Zephyrs":      "Chicago Zephyrs",
    "Capitols":     "Washington Capitols",
    "Stags":        "Chicago Stags",
    "Steamrollers": "Providence Steamrollers",
}

# ─── Junk to remove entirely ──────────────────────────────────────────────────
# All-Star game team names and player-name leaks from box-score scrapes.
# International clubs are also stripped — the game links NBA careers only.

REMOVE = {
    # Player name leaks from All-Star game data
    "Durant", "Giannis", "Stephen", "LeBron", "Barkley",
    # All-Star game named teams (older format)
    "Team Melo", "Team T-Mac", "Team Vince", "Team Austin",
    "Team LeBron", "Team Curry", "Team Durant", "Team Giannis",
    "Team Stephen", "Team Barkley",
    # Rising Stars / rookie game teams
    "Global Stars", "Young Stars", "World Stars",
    # International clubs that leaked in
    "Jerusalem B.C.", "Loong-Lions", "United",
}


# ─── Load ─────────────────────────────────────────────────────────────────────

with open(NBA_FILE) as f:
    raw = f.read()
players = json.loads(raw.replace("export const NBA_PLAYERS = ", "").rstrip(";\n"))
print(f"Loaded {len(players):,} players")


# ─── Normalize ────────────────────────────────────────────────────────────────

changed_players = 0
total_replacements = 0
total_removed = 0

for player in players:
    original = list(player.get("teams", []))
    cleaned: set[str] = set()

    for team in original:
        if team in REMOVE:
            total_removed += 1
            continue
        canonical = NORMALIZE.get(team, team)   # expand or leave as-is
        if canonical != team:
            total_replacements += 1
        cleaned.add(canonical)

    new_teams = sorted(cleaned)
    if new_teams != player.get("teams", []):
        player["teams"] = new_teams
        changed_players += 1

print(f"  Replacements:   {total_replacements:,}")
print(f"  Removed (junk): {total_removed:,}")
print(f"  Players changed:{changed_players:,}")


# ─── Verify no abbreviations remain ──────────────────────────────────────────

all_team_strings: set[str] = set()
for p in players:
    all_team_strings.update(p.get("teams", []))

remaining_abbrevs = sorted(
    t for t in all_team_strings
    if re.match(r'^[A-Z]{2,4}$', t)
)
if remaining_abbrevs:
    print(f"\n⚠️  Unexpanded abbreviations still present: {remaining_abbrevs}")
else:
    print("\n✓  No raw abbreviations remaining")

remaining_partials = sorted(
    t for t in all_team_strings
    if " " not in t and len(t) > 4 and t not in {"76ers"}
)
if remaining_partials:
    print(f"⚠️  Single-word partials still present: {remaining_partials}")
else:
    print("✓  No single-word partials remaining")


# ─── Write ────────────────────────────────────────────────────────────────────

players.sort(key=lambda x: x["name"])

with open(NBA_FILE, "w") as f:
    f.write("export const NBA_PLAYERS = ")
    json.dump(players, f, indent=2)
    f.write(";")

print(f"\nWrote {NBA_FILE}")

# ─── Summary ─────────────────────────────────────────────────────────────────

all_teams_final: set[str] = set()
for p in players:
    all_teams_final.update(p.get("teams", []))

print(f"\nFinal unique team strings: {len(all_teams_final)}")
print("All team values:")
for t in sorted(all_teams_final):
    print(f"  {t}")

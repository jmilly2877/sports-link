import json

CURRENT_FILE = "src/data/nfl_players.js"
HISTORICAL_FILE = "src/data/raw/nfl_historical_players.json"
OUT_FILE = "src/data/nfl_players.js"

TEAM_MAP = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB": "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs",
    "LV": "Las Vegas Raiders",
    "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE": "New England Patriots",
    "NO": "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",

    # historical
    "OAK": "Oakland Raiders",
    "SD": "San Diego Chargers",
    "STL": "St. Louis Rams",
    "SDG": "San Diego Chargers",
    "RAI": "Los Angeles Raiders",
    "PHO": "Phoenix Cardinals",
    "LA": "Los Angeles Rams",
}

# -------------------------
# Load current NFL data
# -------------------------

with open(CURRENT_FILE) as f:
    text = f.read()

current_players = json.loads(
    text.replace("export const NFL_PLAYERS = ", "").rstrip(";\n")
)

# -------------------------
# Load historical data
# -------------------------

with open(HISTORICAL_FILE) as f:
    historical_players = json.load(f)

# -------------------------
# Merge
# -------------------------

merged = {}

def normalize_name(name):
    return name.strip().lower()

for p in current_players + historical_players:
    key = normalize_name(p["name"])

    if key not in merged:
        merged[key] = {
            "name": p["name"],
            "teams": set(),
            "college": set(),
            "numbers": set(),
            "league": "NFL"
        }

    for team in p.get("teams", []):
        mapped = TEAM_MAP.get(team, team)

        if mapped and mapped != "nan":
            merged[key]["teams"].add(mapped)

    merged[key]["college"].update(p.get("college", []))
    merged[key]["numbers"].update(p.get("numbers", []))

# -------------------------
# Convert back
# -------------------------

output = []

for p in merged.values():
    output.append({
        "name": p["name"],
        "teams": sorted(list(p["teams"])),
        "college": sorted(list(p["college"])),
        "numbers": sorted(list(p["numbers"])),
        "league": "NFL"
    })

output = sorted(output, key=lambda x: x["name"])

# -------------------------
# Save
# -------------------------

with open(OUT_FILE, "w") as f:
    f.write("export const NFL_PLAYERS = ")
    json.dump(output, f, indent=2)
    f.write(";")

print("Merged NFL players:", len(output))

for name in [
    "Tom Brady",
    "Peyton Manning",
    "Jerry Rice",
    "Barry Sanders",
    "Patrick Mahomes"
]:
    match = next((p for p in output if p["name"] == name), None)

    print("\n", name)
    print(match)
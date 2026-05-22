import json

CURRENT_FILE = "src/data/nba_players.js"
HISTORICAL_FILE = "src/data/raw/nba_historical_expansion.json"
OUT_FILE = "src/data/nba_players.js"

TEAM_NAME_MAP = {
    "Bulls": "Chicago Bulls",
    "Wizards": "Washington Wizards",
    "Cavaliers": "Cleveland Cavaliers",
    "Heat": "Miami Heat",
    "Lakers": "Los Angeles Lakers",
    "Celtics": "Boston Celtics",
    "Bucks": "Milwaukee Bucks",
}

# -------------------------
# Load current NBA data
# -------------------------

with open(CURRENT_FILE) as f:
    text = f.read()

current_players = json.loads(
    text.replace("export const NBA_PLAYERS = ", "").rstrip(";\n")
)

# -------------------------
# Load historical expansion
# -------------------------

with open(HISTORICAL_FILE) as f:
    historical_players = json.load(f)

# -------------------------
# Merge players
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
            "league": "NBA"
        }

    for team in p.get("teams", []):
        mapped = TEAM_NAME_MAP.get(team, team)

        if mapped not in {"LeBron", "East", "West", "OGs", "Stripes"}:
            merged[key]["teams"].add(mapped)

    merged[key]["college"].update(p.get("college", []))
    merged[key]["numbers"].update(p.get("numbers", []))

# -------------------------
# Convert back to JSON
# -------------------------

output = []

for p in merged.values():
    output.append({
        "name": p["name"],
        "teams": sorted(list(p["teams"])),
        "college": sorted(list(p["college"])),
        "numbers": sorted(list(p["numbers"])),
        "league": "NBA"
    })


output = sorted(output, key=lambda x: x["name"])

# -------------------------
# Save JS file
# -------------------------

with open(OUT_FILE, "w") as f:
    f.write("export const NBA_PLAYERS = ")
    json.dump(output, f, indent=2)
    f.write(";")

print("Merged NBA players:", len(output))

for name in [
    "Michael Jordan",
    "Magic Johnson",
    "Larry Bird",
    "Kareem Abdul-Jabbar",
    "LeBron James",
]:
    match = next((p for p in output if p["name"] == name), None)
    print("\n", name)
    print(match)
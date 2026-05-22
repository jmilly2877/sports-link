import pandas as pd
import json
import math

PLAYERS_FILE = "src/data/raw/nba_historical_players.csv"
BOX_FILE = "src/data/raw/nba_box_scores_all.csv"
OUT_FILE = "src/data/raw/nba_historical_expansion.json"

BAD_TEAMS = {
    "",
    "East",
    "West",
    "Team LeBron",
    "Team Giannis",
    "Team Durant",
    "Team Stephen",
    "Team Shaq",
    "Team Chuck",
    "OGs",
    "Rising Stars",
    "Rookies",
    "Sophomores",
    "Elam Ending",
    "USA",
    "World",
    "Stripes",
    "Stars",
}

def clean_value(v):
    if pd.isna(v):
        return ""

    if isinstance(v, float) and v.is_integer():
        return str(int(v))

    return str(v).strip()

def clean_number(v):
    if pd.isna(v):
        return None

    try:
        n = int(float(v))
        return n
    except:
        return None

# -------------------------
# Load historical player master
# -------------------------

players_df = pd.read_csv(PLAYERS_FILE)

people = {}

for _, row in players_df.iterrows():
    person_id = clean_value(row["personId"])
    first = clean_value(row["firstName"])
    last = clean_value(row["lastName"])

    if not person_id or not first or not last:
        continue

    name = f"{first} {last}".strip()

    school = clean_value(row.get("school", ""))
    number = clean_number(row.get("jersey", None))

    people[person_id] = {
        "name": name,
        "teams": set(),
        "college": set(),
        "numbers": set(),
        "league": "NBA"
    }

    if school:
        people[person_id]["college"].add(school)

    if number is not None:
        people[person_id]["numbers"].add(number)

print("Loaded historical players:", len(people))

# -------------------------
# Load box score teams
# -------------------------

box_df = pd.read_csv(BOX_FILE, usecols=["personId", "playerteamName"])

for _, row in box_df.iterrows():
    person_id = clean_value(row["personId"])
    team = clean_value(row["playerteamName"])

    if not person_id or not team:
        continue

    if person_id not in people:
        continue

    if team not in BAD_TEAMS:
        people[person_id]["teams"].add(team)

print("Added teams from box scores")

# -------------------------
# Convert sets to lists
# -------------------------

output = []

for p in people.values():
    output.append({
        "name": p["name"],
        "teams": sorted(list(p["teams"])),
        "college": sorted(list(p["college"])),
        "numbers": sorted(list(p["numbers"])),
        "league": "NBA"
    })

output = sorted(output, key=lambda x: x["name"])

with open(OUT_FILE, "w") as f:
    json.dump(output, f, indent=2)

print("Created:", OUT_FILE)
print("Historical players:", len(output))

for name in ["Michael Jordan", "Magic Johnson", "Larry Bird", "Kareem Abdul-Jabbar", "LeBron James"]:
    match = next((p for p in output if p["name"] == name), None)
    print("\n", name)
    print(match)
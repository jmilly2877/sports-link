import pandas as pd
import json

# ------------------------
# LOAD LAHMAN FILES
# ------------------------

college_playing = pd.read_csv("src/data/raw/mlb/CollegePlaying.csv")
schools = pd.read_csv("src/data/raw/mlb/Schools.csv")
people = pd.read_csv("src/data/raw/mlb/People.csv")

# ------------------------
# BUILD SCHOOL LOOKUP
# ------------------------

school_lookup = {}

for _, row in schools.iterrows():
    school_id = str(row["schoolID"]).strip()

    name = (
        row.get("name_full")
        or row.get("schoolName")
        or row.get("name")
    )

    if pd.notna(name):
        school_lookup[school_id] = str(name).strip()

# ------------------------
# BUILD PLAYERID -> NAME
# ------------------------

people_lookup = {}

for _, row in people.iterrows():
    player_id = str(row["playerID"]).strip()

    first = str(row.get("nameFirst", "")).strip()
    last = str(row.get("nameLast", "")).strip()

    full_name = f"{first} {last}".strip()

    if full_name:
        people_lookup[player_id] = full_name

# ------------------------
# BUILD COLLEGE MAP
# ------------------------

college_map = {}

for _, row in college_playing.iterrows():
    player_id = str(row["playerID"]).strip()
    school_id = str(row["schoolID"]).strip()

    if player_id not in people_lookup:
        continue

    if school_id not in school_lookup:
        continue

    player_name = people_lookup[player_id]
    school_name = school_lookup[school_id]

    if player_name not in college_map:
        college_map[player_name] = set()

    college_map[player_name].add(school_name)

# ------------------------
# LOAD MLB PLAYERS
# ------------------------

with open("src/data/mlb_players.js", "r") as f:
    text = f.read()

json_text = text.replace("export const MLB_PLAYERS = ", "").rstrip(";\n")

players = json.loads(json_text)

# ------------------------
# MERGE COLLEGES
# ------------------------

updated = 0

for player in players:
    name = player["name"]

    if name not in college_map:
        continue

    existing = set(player.get("college", []))

    merged = existing.union(college_map[name])

    player["college"] = sorted(list(merged))

    updated += 1

# ------------------------
# SAVE
# ------------------------

with open("src/data/mlb_players.js", "w") as f:
    f.write("export const MLB_PLAYERS = ")
    f.write(json.dumps(players, indent=2))
    f.write(";\n")

print("Updated players:", updated)

sample_names = [
    "Evan Longoria",
    "Aaron Judge",
    "Mookie Betts",
    "Mark Teixeira"
]

for name in sample_names:
    matches = [p for p in players if p["name"] == name]

    if matches:
        print("\n", name)
        print(matches[0].get("college"))
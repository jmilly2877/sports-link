import pandas as pd
import json

MLB_FILE = "src/data/mlb_players.js"
ENRICH_FILE = "src/data/raw/mlb_college_enrichment.csv"

with open(MLB_FILE) as f:
    text = f.read()

players = json.loads(
    text.replace("export const MLB_PLAYERS = ", "").rstrip(";\n")
)

df = pd.read_csv(ENRICH_FILE)

college_map = {}

for _, row in df.iterrows():

    name = str(row["player_name"]).strip()
    college = str(row["college"]).strip()

    if not name or not college:
        continue

    college_map.setdefault(name, set()).add(college)

updated = 0

for p in players:

    name = p["name"]

    if name not in college_map:
        continue

    existing = set(p.get("college", []))

    before = len(existing)

    existing.update(college_map[name])

    p["college"] = sorted(existing)

    if len(existing) > before:
        updated += 1

with open(MLB_FILE, "w") as f:
    f.write("export const MLB_PLAYERS = ")
    json.dump(players, f, indent=2)
    f.write(";")

print("Updated MLB players:", updated)

for test in [
    "Mark Teixeira",
    "Gerrit Cole",
    "Alex Bregman",
    "Dansby Swanson"
]:
    found = next((p for p in players if p["name"] == test), None)
    print("\n", test)
    print(found)
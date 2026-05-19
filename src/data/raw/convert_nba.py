import pandas as pd
import json
from team_map import NBA_TEAM_MAP

df = pd.read_csv("src/data/raw/all_seasons.csv")

# Remove junk index column if present
df = df.drop(columns=["Unnamed: 0"], errors="ignore")

players = {}

for _, row in df.iterrows():
    name = str(row["player_name"]).strip()
    abbr = str(row["team_abbreviation"]).strip()
    team = NBA_TEAM_MAP.get(abbr, abbr)
    college = str(row["college"]).strip()

    if not name or name == "nan":
        continue

    if name not in players:
        players[name] = {
            "name": name,
            "teams": set(),
            "college": set(),
            "numbers": set()
        }

    if team and team != "nan":
        players[name]["teams"].add(team)

    if college and college != "nan" and college.lower() != "none":
        players[name]["college"].add(college)

output = []

for p in players.values():
    output.append({
    "name": p["name"],
    "teams": sorted(list(p["teams"])),
    "college": sorted(list(p["college"])),
    "numbers": sorted(list(p["numbers"])),
    "league": "NBA"
})

output = sorted(output, key=lambda x: x["name"])

with open("src/data/raw/nba_players_converted.js", "w") as f:
    f.write("export const NBA_PLAYERS = ")
    f.write(json.dumps(output, indent=2))
    f.write(";\n")

print("Created nba_players_converted.js")
print("Total players:", len(output))
print("First 3 players:")
print(output[:3])
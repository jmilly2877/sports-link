import json
import pandas as pd

NBA_FILE = "src/data/nba_players.js"
RECENT_FILE = "src/data/raw/nba_recent_players.csv"

def clean_js_export(text):
    text = text.replace("export const NBA_PLAYERS = ", "")
    text = text.rstrip().rstrip(";")
    return text

with open(NBA_FILE, "r") as f:
    text = f.read()

players = json.loads(clean_js_export(text))

df = pd.read_csv(RECENT_FILE)

players_by_name = {}

for p in players:
    players_by_name[p["name"]] = p

added_players = 0
updated_players = 0

for _, row in df.iterrows():
    name = str(row["player_name"]).strip()
    team = str(row["team"]).strip()
    college_raw = str(row["college"]).strip()

    colleges = []

    if (
        college_raw
        and college_raw.lower() != "nan"
        and college_raw != ""
    ):
        colleges = [c.strip() for c in college_raw.split(",")]

    if name not in players_by_name:
        players_by_name[name] = {
            "name": name,
            "teams": [],
            "college": [],
            "numbers": []
        }
        added_players += 1

    player = players_by_name[name]

    existing_teams = set(player.get("teams", []))
    existing_colleges = set(player.get("college", []))

    existing_teams.add(team)

    for c in colleges:
        if c:
            existing_colleges.add(c)

    player["teams"] = sorted(list(existing_teams))
    player["college"] = sorted(list(existing_colleges))

    updated_players += 1

final_players = sorted(
    list(players_by_name.values()),
    key=lambda x: x["name"]
)

with open(NBA_FILE, "w") as f:
    f.write("export const NBA_PLAYERS = ")
    f.write(json.dumps(final_players, indent=2))
    f.write(";\n")

print("Added new players:", added_players)
print("Updated players:", updated_players)
print("Total NBA players:", len(final_players))
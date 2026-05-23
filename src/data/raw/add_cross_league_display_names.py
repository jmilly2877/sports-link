import json
from collections import defaultdict

FILES = [
    ("NBA", "src/data/nba_players.js", "NBA_PLAYERS"),
    ("NFL", "src/data/nfl_players.js", "NFL_PLAYERS"),
    ("MLB", "src/data/mlb_players.js", "MLB_PLAYERS"),
]

name_to_leagues = defaultdict(set)

for league, path, export_name in FILES:
    with open(path) as f:
        text = f.read()
    players = json.loads(text.replace(f"export const {export_name} = ", "").rstrip(";\n"))

    for p in players:
        name_to_leagues[p["name"]].add(league)

for league, path, export_name in FILES:
    with open(path) as f:
        text = f.read()
    players = json.loads(text.replace(f"export const {export_name} = ", "").rstrip(";\n"))

    tagged = 0

    for p in players:
        if len(name_to_leagues[p["name"]]) > 1:
            p["display_name"] = f'{p["name"]} ({league})'
            tagged += 1
        else:
            p["display_name"] = p["name"]

    with open(path, "w") as f:
        f.write(f"export const {export_name} = ")
        json.dump(players, f, indent=2)
        f.write(";")

    print(path, "tagged:", tagged)
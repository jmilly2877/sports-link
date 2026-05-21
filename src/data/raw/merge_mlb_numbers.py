import pandas as pd
import json

MLB_FILE = "src/data/mlb_players.js"
NUMBERS_FILE = "src/data/raw/mlb_numbers_api.csv"

with open(MLB_FILE, "r") as f:
    text = f.read()

json_text = text.replace("export const MLB_PLAYERS = ", "").rstrip(";\n")
players = json.loads(json_text)

df = pd.read_csv(NUMBERS_FILE)

players_by_name = {p["name"]: p for p in players}

updated_numbers = 0
updated_teams = 0
added_players = 0

for _, row in df.iterrows():
    name = str(row["player_name"]).strip()
    team = str(row["team"]).strip()
    number = str(row["number"]).replace(".0", "").strip()

    if not name or name == "nan":
        continue

    if name not in players_by_name:
        players_by_name[name] = {
            "name": name,
            "teams": [],
            "college": [],
            "numbers": [],
            "league": "MLB"
        }
        added_players += 1

    player = players_by_name[name]

    teams = set(player.get("teams", []))
    numbers = set(str(n).replace(".0", "").strip() for n in player.get("numbers", []))

    if team and team != "nan" and team not in teams:
        teams.add(team)
        updated_teams += 1

    if number and number != "nan" and number not in numbers:
        numbers.add(number)
        updated_numbers += 1

    player["teams"] = sorted(list(teams))
    player["numbers"] = sorted(list(numbers), key=lambda x: int(x) if x.isdigit() else 999)

final_players = sorted(players_by_name.values(), key=lambda x: x["name"])

with open(MLB_FILE, "w") as f:
    f.write("export const MLB_PLAYERS = ")
    f.write(json.dumps(final_players, indent=2))
    f.write(";\n")

print("Added players:", added_players)
print("Updated team links:", updated_teams)
print("Updated number links:", updated_numbers)
print("Total MLB players:", len(final_players))

for name in ["Burch Smith", "Shohei Ohtani", "Aaron Judge", "Mike Trout"]:
    p = players_by_name.get(name)
    print(name, p)
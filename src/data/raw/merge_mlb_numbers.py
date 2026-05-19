import pandas as pd
import json

# LOAD CURRENT MLB PLAYERS
with open("src/data/mlb_players.js", "r") as f:
    text = f.read()

json_text = text.replace("export const MLB_PLAYERS = ", "").rstrip(";\n")

players = json.loads(json_text)

# LOAD MLB NUMBERS
df = pd.read_csv("src/data/raw/mlb_numbers_api.csv")

# BUILD NUMBER MAP
number_map = {}

for _, row in df.iterrows():

    name = str(row["player_name"]).strip()
    number = str(row["number"]).replace(".0", "").strip()

    if not name or number == "nan":
        continue

    if name not in number_map:
        number_map[name] = set()

    number_map[name].add(number)

# MERGE
updated = 0

for player in players:

    name = player["name"]

    if name in number_map:

        player["numbers"] = sorted(list(number_map[name]))
        updated += 1

# SAVE
with open("src/data/mlb_players.js", "w") as f:
    f.write("export const MLB_PLAYERS = ")
    f.write(json.dumps(players, indent=2))
    f.write(";\n")

print("Updated players:", updated)
print("Total MLB players:", len(players))
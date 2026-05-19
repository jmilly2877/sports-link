import json
import re
import pandas as pd

NBA_FILE = "src/data/nba_players.js"
NUMBERS_FILE = "src/data/raw/nba_numbers.csv"

def clean_js_export(text):
    text = text.replace("export const NBA_PLAYERS = ", "")
    text = text.rstrip().rstrip(";")
    return text

with open(NBA_FILE, "r") as f:
    text = f.read()

players = json.loads(clean_js_export(text))

numbers_df = pd.read_csv(NUMBERS_FILE)

numbers_by_player = {}

for _, row in numbers_df.iterrows():
    name = str(row["player_name"]).replace("*", "").strip()
    raw_number = str(row["number"]).strip()

    if not name or name == "nan":
        continue

    # only allow normal jersey numbers
    if not re.fullmatch(r"\d{1,2}", raw_number):
        continue

    num = int(raw_number)

    if name not in numbers_by_player:
        numbers_by_player[name] = set()

    numbers_by_player[name].add(num)

updated = 0

for player in players:
    name = player["name"]

    existing = set(player.get("numbers", []))
    scraped = numbers_by_player.get(name, set())

    combined = sorted(existing | scraped)

    if combined != sorted(existing):
        updated += 1

    player["numbers"] = combined

with open(NBA_FILE, "w") as f:
    f.write("export const NBA_PLAYERS = ")
    f.write(json.dumps(players, indent=2))
    f.write(";\n")

print("Updated players:", updated)
print("Total NBA players:", len(players))
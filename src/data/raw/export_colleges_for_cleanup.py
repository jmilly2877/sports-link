import json
from collections import Counter

FILES = [
    ("NBA", "src/data/nba_players.js", "NBA_PLAYERS"),
    ("NFL", "src/data/nfl_players.js", "NFL_PLAYERS"),
    ("MLB", "src/data/mlb_players.js", "MLB_PLAYERS"),
]

counts = Counter()

for league, path, export_name in FILES:
    with open(path) as f:
        text = f.read()

    players = json.loads(
        text.replace(f"export const {export_name} = ", "").rstrip(";\n")
    )

    for p in players:
        for c in p.get("college", []):
            if c:
                counts[c.strip()] += 1

with open("src/data/raw/college_cleanup_list.csv", "w") as f:
    f.write("college,count,suggested_canonical\n")

    for college, count in counts.most_common():
        f.write(f'"{college}",{count},""\n')

print("Created src/data/raw/college_cleanup_list.csv")
print("Unique colleges:", len(counts))
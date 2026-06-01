import json
import csv
from collections import Counter

FILES = [
    ("MLB", "src/data/mlb_players.js", "MLB_PLAYERS"),
    ("NBA", "src/data/nba_players.js", "NBA_PLAYERS"),
    ("NFL", "src/data/nfl_players.js", "NFL_PLAYERS"),
]

counts = Counter()
examples = {}

for league, path, export_name in FILES:
    with open(path) as f:
        text = f.read()

    players = json.loads(
        text.replace(f"export const {export_name} = ", "").rstrip(";\n")
    )

    for p in players:
        for c in p.get("college", []):
            college = str(c).strip()

            if not college:
                continue

            counts[college] += 1
            examples.setdefault(college, set()).add(p["name"])

with open("src/data/raw/college_canonical_review.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "raw_college",
        "count",
        "example_players",
        "canonical_college"
    ])

    for college, count in counts.most_common():
        ex = "; ".join(sorted(list(examples[college]))[:5])
        writer.writerow([college, count, ex, ""])

print("Created src/data/raw/college_canonical_review.csv")
print("Unique colleges:", len(counts))
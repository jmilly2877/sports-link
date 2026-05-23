import json
import csv

with open("src/data/mlb_players.js") as f:
    text = f.read()

players = json.loads(
    text.replace("export const MLB_PLAYERS = ", "").rstrip(";\n")
)

modern_teams = {
    "Los Angeles Dodgers",
    "New York Yankees",
    "Boston Red Sox",
    "Atlanta Braves",
    "Houston Astros",
    "Philadelphia Phillies",
    "New York Mets",
    "San Diego Padres",
    "Chicago Cubs",
    "St. Louis Cardinals",
    "Texas Rangers",
    "Toronto Blue Jays",
    "Seattle Mariners",
    "San Francisco Giants",
    "Milwaukee Brewers",
    "Baltimore Orioles",
    "Tampa Bay Rays",
    "Cleveland Guardians",
    "Detroit Tigers",
    "Minnesota Twins",
    "Arizona Diamondbacks",
    "Cincinnati Reds",
    "Pittsburgh Pirates",
    "Miami Marlins",
    "Colorado Rockies",
    "Kansas City Royals",
    "Chicago White Sox",
    "Los Angeles Angels",
    "Washington Nationals",
    "Oakland Athletics"
}

missing = []

for p in players:
    if p.get("college"):
        continue

    teams = set(p.get("teams", []))
    numbers = p.get("numbers", [])

    if teams & modern_teams and numbers:
        missing.append(p)

with open("src/data/raw/mlb_modern_missing_colleges.csv", "w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "name",
        "teams",
        "numbers"
    ])

    for p in missing:
        writer.writerow([
            p["name"],
            "; ".join(p.get("teams", [])),
            "; ".join(map(str, p.get("numbers", [])))
        ])

print("Modern-ish MLB missing colleges:", len(missing))
print("Created src/data/raw/mlb_modern_missing_colleges.csv")
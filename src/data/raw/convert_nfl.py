import pandas as pd
import json

TEAM_MAP = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB": "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs",
    "LA": "Los Angeles Rams",
    "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE": "New England Patriots",
    "NO": "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",
}

df = pd.read_csv("src/data/raw/nfl_rosters_raw.csv")

players = {}

for _, row in df.iterrows():
    name = str(row["full_name"]).strip()
    team_abbr = str(row["team"]).strip()
    team = TEAM_MAP.get(team_abbr, team_abbr)
    college = str(row["college"]).strip()
    jersey = str(row["jersey_number"]).strip()

    if not name or name == "nan":
        continue

    if name not in players:
        players[name] = {
            "name": name,
            "teams": set(),
            "college": set(),
            "numbers": set(),
            "league": "NFL"
        }

    if team and team != "nan":
        players[name]["teams"].add(team)

    if college and college != "nan":
        players[name]["college"].add(college)

    try:
        if jersey and jersey != "nan":
            num = int(float(jersey))
            if 0 <= num <= 99:
                players[name]["numbers"].add(num)
    except:
        pass

output = []

for p in players.values():
    output.append({
        "name": p["name"],
        "teams": sorted(list(p["teams"])),
        "college": sorted(list(p["college"])),
        "numbers": sorted(list(p["numbers"])),
        "league": "NFL"
    })

output = sorted(output, key=lambda x: x["name"])

with open("src/data/nfl_players.js", "w") as f:
    f.write("export const NFL_PLAYERS = ")
    f.write(json.dumps(output, indent=2))
    f.write(";\n")

print("Created src/data/nfl_players.js")
print("Players:", len(output))

for name in ["Patrick Mahomes", "Tanner McKee", "Tom Brady"]:
    player = next((p for p in output if p["name"] == name), None)
    print(name, player)
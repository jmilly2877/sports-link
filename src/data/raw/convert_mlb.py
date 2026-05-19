import pandas as pd
import json

people = pd.read_csv("src/data/raw/mlb/People.csv")
appearances = pd.read_csv("src/data/raw/mlb/Appearances.csv")
college = pd.read_csv("src/data/raw/mlb/CollegePlaying.csv")
schools = pd.read_csv("src/data/raw/mlb/Schools.csv")

TEAM_MAP = {
    "ANA": "Anaheim Angels",
    "ARI": "Arizona Diamondbacks",
    "ATL": "Atlanta Braves",
    "BAL": "Baltimore Orioles",
    "BOS": "Boston Red Sox",
    "CHA": "Chicago White Sox",
    "CHN": "Chicago Cubs",
    "CHC": "Chicago Cubs",
    "CHW": "Chicago White Sox",
    "CIN": "Cincinnati Reds",
    "CLE": "Cleveland Guardians",
    "COL": "Colorado Rockies",
    "DET": "Detroit Tigers",
    "FLO": "Florida Marlins",
    "FLA": "Florida Marlins",
    "HOU": "Houston Astros",
    "KCA": "Kansas City Royals",
    "KCR": "Kansas City Royals",
    "LAA": "Los Angeles Angels",
    "LAN": "Los Angeles Dodgers",
    "LAD": "Los Angeles Dodgers",
    "MIA": "Miami Marlins",
    "MIL": "Milwaukee Brewers",
    "MIN": "Minnesota Twins",
    "ML4": "Milwaukee Brewers",
    "MON": "Montreal Expos",
    "NYA": "New York Yankees",
    "NYY": "New York Yankees",
    "NYN": "New York Mets",
    "NYM": "New York Mets",
    "OAK": "Oakland Athletics",
    "PHI": "Philadelphia Phillies",
    "PIT": "Pittsburgh Pirates",
    "SDN": "San Diego Padres",
    "SDP": "San Diego Padres",
    "SEA": "Seattle Mariners",
    "SFN": "San Francisco Giants",
    "SFG": "San Francisco Giants",
    "SLN": "St. Louis Cardinals",
    "STL": "St. Louis Cardinals",
    "TBA": "Tampa Bay Rays",
    "TBD": "Tampa Bay Rays",
    "TBR": "Tampa Bay Rays",
    "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",
    "WAS": "Washington Nationals",
    "WSN": "Washington Nationals",
}

people["full_name"] = (
    people["nameFirst"].fillna("").astype(str).str.strip()
    + " "
    + people["nameLast"].fillna("").astype(str).str.strip()
)

name_map = dict(zip(people["playerID"], people["full_name"]))

school_name_col = "name_full" if "name_full" in schools.columns else "schoolName"
school_map = dict(zip(schools["schoolID"], schools[school_name_col]))

college_map = {}

for _, row in college.iterrows():
    pid = row["playerID"]
    school_id = str(row["schoolID"]).strip()

    school_name = school_map.get(school_id, school_id)

    if school_name and school_name != "nan":
        if pid not in college_map:
            college_map[pid] = set()
        college_map[pid].add(school_name)

players = {}

for _, row in appearances.iterrows():
    pid = row["playerID"]

    if pid not in name_map:
        continue

    name = name_map[pid].strip()

    if not name:
        continue

    team_abbr = str(row["teamID"]).strip()
    team = TEAM_MAP.get(team_abbr, team_abbr)

    if name not in players:
        players[name] = {
            "name": name,
            "teams": set(),
            "college": set(),
            "numbers": set(),
            "league": "MLB"
        }

    if team and team != "nan":
        players[name]["teams"].add(team)

    if pid in college_map:
        for school in college_map[pid]:
            players[name]["college"].add(school)

output = []

for p in players.values():
    output.append({
        "name": p["name"],
        "teams": sorted(list(p["teams"])),
        "college": sorted(list(p["college"])),
        "numbers": [],
        "league": "MLB"
    })

output = sorted(output, key=lambda x: x["name"])

with open("src/data/mlb_players.js", "w") as f:
    f.write("export const MLB_PLAYERS = ")
    f.write(json.dumps(output, indent=2))
    f.write(";\n")

print("Created src/data/mlb_players.js")
print("Players:", len(output))

for name in ["Bryce Harper", "Aaron Judge", "Barry Zito", "Buster Posey"]:
    player = next((p for p in output if p["name"] == name), None)
    print(name, player)
import requests
import pandas as pd
import time

TEAM_IDS = {
    108: "Los Angeles Angels",
    109: "Arizona Diamondbacks",
    110: "Baltimore Orioles",
    111: "Boston Red Sox",
    112: "Chicago Cubs",
    113: "Cincinnati Reds",
    114: "Cleveland Guardians",
    115: "Colorado Rockies",
    116: "Detroit Tigers",
    117: "Houston Astros",
    118: "Kansas City Royals",
    119: "Los Angeles Dodgers",
    120: "Washington Nationals",
    121: "New York Mets",
    133: "Oakland Athletics",
    134: "Pittsburgh Pirates",
    135: "San Diego Padres",
    136: "Seattle Mariners",
    137: "San Francisco Giants",
    138: "St. Louis Cardinals",
    139: "Tampa Bay Rays",
    140: "Texas Rangers",
    141: "Toronto Blue Jays",
    142: "Minnesota Twins",
    143: "Philadelphia Phillies",
    144: "Atlanta Braves",
    145: "Chicago White Sox",
    146: "Miami Marlins",
    147: "New York Yankees",
    158: "Milwaukee Brewers",
}

rows = []

for team_id, team_name in TEAM_IDS.items():

    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster/40Man"

    try:
        data = requests.get(url).json()

        roster = data.get("roster", [])

        for p in roster:

            player = p.get("person", {}).get("fullName", "").strip()
            number = str(p.get("jerseyNumber", "")).strip()

            if player:
                rows.append({
                    "team": team_name,
                    "player_name": player,
                    "number": number
                })

        print(f"OK {team_name}: {len(roster)} players")

        time.sleep(1)

    except Exception as e:
        print(f"SKIP {team_name}: {e}")

df = pd.DataFrame(rows)

df.to_csv("src/data/raw/mlb_numbers_api.csv", index=False)

print("\nCreated src/data/raw/mlb_numbers_api.csv")
print("Rows:", len(df))
print("Unique players:", df['player_name'].nunique())

print("\nSample:")
print(df.head())
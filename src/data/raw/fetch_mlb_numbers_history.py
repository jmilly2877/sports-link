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
    149: "Montreal Expos",
    158: "Milwaukee Brewers",
}

# Start smaller first. If this works, we can go back further.
YEARS = range(1965, 2027)

rows = []

for year in YEARS:
    print(f"\n=== YEAR {year} ===")

    for team_id, team_name in TEAM_IDS.items():
        url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster/fullSeason?season={year}"

        try:
            data = requests.get(url, timeout=20).json()
            roster = data.get("roster", [])

            for p in roster:
                player = p.get("person", {}).get("fullName", "").strip()
                number = str(p.get("jerseyNumber", "")).replace(".0", "").strip()

                if player and number and number != "nan":
                    rows.append({
                        "season": year,
                        "team": team_name,
                        "player_name": player,
                        "number": number,
                    })

            print(f"OK {team_name} {year}: {len(roster)} players")
            time.sleep(0.4)

        except Exception as e:
            print(f"SKIP {team_name} {year}: {e}")
            time.sleep(0.4)

df = pd.DataFrame(rows)
df = df.drop_duplicates()

df.to_csv("src/data/raw/mlb_numbers_history.csv", index=False)

print("\nCreated src/data/raw/mlb_numbers_history.csv")
print("Rows:", len(df))
print("Unique players:", df["player_name"].nunique())
print("Unique numbers:", df["number"].nunique())

print("\nSample:")
print(df.head())
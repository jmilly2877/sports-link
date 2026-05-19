import requests
from io import StringIO
import pandas as pd
import time
import ssl
from nfl_team_map import NFL_TEAM_MAP

ssl._create_default_https_context = ssl._create_unverified_context

# TEST SMALL FIRST
YEARS = list(range(2021, 2024))

TEAMS = list(NFL_TEAM_MAP.keys())

rows = []

for year in YEARS:
    for team_code in TEAMS:

        url = f"https://www.pro-football-reference.com/teams/{team_code}/{year}_roster.htm"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            tables = pd.read_html(StringIO(response.text))

            roster = tables[0]
            full_team = NFL_TEAM_MAP.get(team_code, team_code)

            for _, r in roster.iterrows():

                player = str(r.get("Player", "")).replace("*", "").replace("+", "").strip()

                number = str(r.get("No.", "")).strip()

                college = str(r.get("College/Univ", "")).strip()

                if player and player != "nan":

                    rows.append({
                        "season_end_year": year,
                        "team": full_team,
                        "player_name": player,
                        "college": college if college != "nan" else "",
                        "number": number if number != "nan" else ""
                    })

            print(f"OK {team_code} {year}")
            time.sleep(3)

        except Exception as e:
            print(f"SKIP {team_code} {year}: {e}")
            time.sleep(3)

df = pd.DataFrame(rows)

df.to_csv("src/data/raw/nfl_players_raw.csv", index=False)

print("Created src/data/raw/nfl_players_raw.csv")
print("Rows:", len(df))
print("Unique players:", df["player_name"].nunique())
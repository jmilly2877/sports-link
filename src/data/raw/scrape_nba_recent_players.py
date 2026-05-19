import pandas as pd
import time
import ssl
from team_map import NBA_TEAM_MAP

ssl._create_default_https_context = ssl._create_unverified_context

YEARS = list(range(2023, 2027))

TEAMS = [
    "ATL","BOS","BRK","CHI","CLE","DAL","DEN","DET","GSW",
    "HOU","IND","LAC","LAL","MEM","MIA","MIL","MIN","NOP",
    "NYK","OKC","ORL","PHI","PHO","POR","SAC","SAS","TOR",
    "UTA","WAS","CHO"
]

rows = []

for year in YEARS:
    for team in TEAMS:
        url = f"https://www.basketball-reference.com/teams/{team}/{year}.html"

        try:
            tables = pd.read_html(url)
            roster = tables[0]
            full_team = NBA_TEAM_MAP.get(team, team)

            for _, r in roster.iterrows():
                player = str(r.get("Player", "")).replace("*", "").strip()
                college = str(r.get("College", "")).strip()

                if player and player != "nan":
                    rows.append({
                        "season_end_year": year,
                        "team": full_team,
                        "player_name": player,
                        "college": college if college != "nan" else ""
                    })

            print(f"OK {team} {year}")
            time.sleep(3)

        except Exception as e:
            print(f"SKIP {team} {year}: {e}")
            time.sleep(3)

df = pd.DataFrame(rows)
df.to_csv("src/data/raw/nba_recent_players.csv", index=False)

print("Created src/data/raw/nba_recent_players.csv")
print("Rows:", len(df))
print("Unique players:", df["player_name"].nunique())
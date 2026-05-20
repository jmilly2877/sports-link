import pandas as pd
import time
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

YEARS = list(range(1996, 2027))  # your dataset goes 1996-97 through 2021-22

TEAMS = [
    "ATL","BOS","BRK","CHH","CHI","CLE","DAL","DEN","DET","GSW",
    "HOU","IND","LAC","LAL","MEM","MIA","MIL","MIN","NJN","NOH",
    "NOP","NYK","OKC","ORL","PHI","PHO","POR","SAC","SAS","SEA",
    "TOR","UTA","VAN","WAS"
]

rows = []

for year in YEARS:
    for team in TEAMS:
        url = f"https://www.basketball-reference.com/teams/{team}/{year}.html"
        try:
            tables = pd.read_html(url)
            roster = tables[0]

            for _, r in roster.iterrows():
                number = str(r.get("No.", "")).strip()
                player = str(r.get("Player", "")).strip()

                if player and player != "nan":
                    rows.append({
                        "season_end_year": year,
                        "team_abbreviation": team,
                        "player_name": player.replace("*", "").strip(),
                        "number": number
                    })

            print(f"OK {team} {year}")
            time.sleep(3)

        except Exception as e:
            print(f"SKIP {team} {year}: {e}")
            time.sleep(3)

df = pd.DataFrame(rows)
df.to_csv("src/data/raw/nba_numbers.csv", index=False)

print("Created src/data/raw/nba_numbers.csv")
print("Rows:", len(df))
import pandas as pd
import time
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# SMALL TEST FIRST
YEARS = list(range(2021, 2024))

TEAMS = [
    "ARI","ATL","BAL","BOS","CHC","CHW","CIN","CLE","COL","DET",
    "HOU","KCR","LAA","LAD","MIA","MIL","MIN","NYM","NYY","OAK",
    "PHI","PIT","SDP","SEA","SFG","STL","TBR","TEX","TOR","WSN"
]

rows = []

for year in YEARS:
    for team in TEAMS:
        url = f"https://www.baseball-reference.com/teams/{team}/{year}-roster.shtml"

        try:
            tables = pd.read_html(url)
            roster = tables[0]

            for _, r in roster.iterrows():
                player = str(r.get("Name", "")).replace("*", "").replace("#", "").strip()
                number = str(r.get("Uniform Number", "")).strip()

                if player and player != "nan":
                    rows.append({
                        "season": year,
                        "team": team,
                        "player_name": player,
                        "number": number
                    })

            print(f"OK {team} {year}")
            time.sleep(3)

        except Exception as e:
            print(f"SKIP {team} {year}: {e}")
            time.sleep(3)

df = pd.DataFrame(rows)
df.to_csv("src/data/raw/mlb_numbers.csv", index=False)

print("Created src/data/raw/mlb_numbers.csv")
print("Rows:", len(df))
print("Unique players:", df["player_name"].nunique())
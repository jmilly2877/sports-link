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

YEARS = range(1970, 2027)

rows = []
seen = set()

for year in YEARS:
    print(f"\n=== YEAR {year} ===")

    for team_id, team_name in TEAM_IDS.items():
        url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster/fullSeason?season={year}"

        try:
            data = requests.get(url, timeout=20).json()
            roster = data.get("roster", [])

            print(f"{team_name} {year}: {len(roster)} players")

            for p in roster:
                person = p.get("person", {})
                player_id = person.get("id")
                player_name = person.get("fullName", "").strip()

                if not player_id or not player_name:
                    continue

                if player_id in seen:
                    continue

                seen.add(player_id)

                player_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"

                try:
                    pdata = requests.get(player_url, timeout=20).json()

                    people = pdata.get("people", [])

                    if not people:
                        continue

                    person_data = people[0]

                    college = (
                        person_data.get("college")
                        or person_data.get("education", "")
                        or ""
                    )

                    if college:
                        rows.append({
                            "player_name": player_name,
                            "college": str(college).strip()
                        })

                    print(player_name, "->", college)

                    time.sleep(0.15)

                except Exception as e:
                    print("PLAYER ERROR", player_name, e)
                    time.sleep(0.15)

            time.sleep(0.4)

        except Exception as e:
            print("TEAM ERROR", team_name, year, e)
            time.sleep(0.4)

df = pd.DataFrame(rows)
df = df.drop_duplicates()

df.to_csv("src/data/raw/mlb_colleges.csv", index=False)

print("\nDONE")
print("Rows:", len(df))
print("Unique players:", df["player_name"].nunique())

print(df.head())
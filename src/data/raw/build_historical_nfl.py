import ssl
import pandas as pd
import json

ssl._create_default_https_context = ssl._create_unverified_context

START_YEAR = 1990
END_YEAR = 2025

players = {}

for year in range(START_YEAR, END_YEAR + 1):
    try:
        url = f"https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{year}.csv"

        print("Loading", year)

        df = pd.read_csv(url)

        for _, row in df.iterrows():
            name = str(row.get("full_name", "")).strip()

            if not name or name == "nan":
                continue

            team = str(row.get("team", "")).strip()
            college = str(row.get("college", "")).strip()

            number = row.get("jersey_number")

            try:
                if pd.notna(number):
                    number = int(float(number))
                else:
                    number = None
            except:
                number = None

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

            if number is not None:
                players[name]["numbers"].add(number)

        print(year, "players:", len(df))

    except Exception as e:
        print(year, "FAILED:", e)

# -------------------------
# Convert sets to lists
# -------------------------

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

with open("src/data/raw/nfl_historical_players.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nTOTAL NFL PLAYERS:", len(output))

for name in [
    "Tom Brady",
    "Peyton Manning",
    "Jerry Rice",
    "Barry Sanders",
    "Patrick Mahomes"
]:
    match = next((p for p in output if p["name"] == name), None)

    print("\n", name)
    print(match)
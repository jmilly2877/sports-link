import requests
import json

team_id = 119  # Dodgers
year = 2023

for roster_type in ["active", "40Man", "fullSeason"]:
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster/{roster_type}?season={year}"
    print("\nTRYING:", roster_type)
    print(url)

    data = requests.get(url).json()
    roster = data.get("roster", [])

    print("count:", len(roster))

    for p in roster[:5]:
        print(
            p.get("person", {}).get("fullName"),
            p.get("jerseyNumber"),
            p.get("position", {}).get("abbreviation")
        )
import json
import csv

MLB_FILE = "src/data/mlb_players.js"
OUT_FILE = "src/data/raw/mlb_2000_present_missing_colleges.csv"

with open(MLB_FILE) as f:
    text = f.read()

players = json.loads(
    text.replace("export const MLB_PLAYERS = ", "").rstrip(";\n")
)

missing = []

for p in players:
    colleges = p.get("college", [])
    numbers = p.get("numbers", [])
    teams = p.get("teams", [])

    # no college listed
    if colleges:
        continue

    # modern-ish proxy: has jersey numbers from your 2000-present/modern scraping
    if not numbers:
        continue

    missing.append(p)

missing = sorted(missing, key=lambda x: x["name"])

with open(OUT_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "teams", "numbers"])

    for p in missing:
        writer.writerow([
            p["name"],
            "; ".join(p.get("teams", [])),
            "; ".join(map(str, p.get("numbers", [])))
        ])

print("MLB 2000-present-ish players missing colleges:", len(missing))
print("Created:", OUT_FILE)

print("\nSample:")
for p in missing[:50]:
    print(p["name"], p.get("teams", []), p.get("numbers", []))
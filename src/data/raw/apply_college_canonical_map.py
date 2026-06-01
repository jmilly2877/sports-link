import json
import csv

MAP_FILE = "src/data/raw/college_canonical_review.csv"

FILES = [
    ("src/data/mlb_players.js", "MLB_PLAYERS"),
    ("src/data/nba_players.js", "NBA_PLAYERS"),
    ("src/data/nfl_players.js", "NFL_PLAYERS"),
]

canonical_map = {}

with open(MAP_FILE, newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        raw = str(row.get("raw_college", "")).strip()
        canonical = str(row.get("canonical_college", "")).strip()

        if raw and canonical:
            canonical_map[raw.lower()] = canonical

print("Canonical mappings:", len(canonical_map))

def canonicalize_college(value):
    if not value:
        return []

    parts = []

    # split transfer strings
    for piece in str(value).split(";"):
        for subpiece in piece.split(" and "):
            cleaned = subpiece.strip()
            if cleaned:
                parts.append(cleaned)

    output = []

    for part in parts:
        key = part.lower().strip()
        canonical = canonical_map.get(key, part)

        if canonical and canonical not in output:
            output.append(canonical)

    return output

for path, export_name in FILES:
    print("\nUpdating:", path)

    with open(path) as f:
        text = f.read()

    players = json.loads(
        text.replace(f"export const {export_name} = ", "").rstrip(";\n")
    )

    updated = 0

    for p in players:
        original = p.get("college", [])

        if not isinstance(original, list):
            original = [original]

        new_colleges = []

        for college in original:
            new_colleges.extend(canonicalize_college(college))

        new_colleges = sorted(list(dict.fromkeys(new_colleges)))

        if new_colleges != p.get("college", []):
            p["college"] = new_colleges
            updated += 1

    with open(path, "w") as f:
        f.write(f"export const {export_name} = ")
        json.dump(players, f, indent=2)
        f.write(";")

    print("Updated players:", updated)

print("\nDone.")
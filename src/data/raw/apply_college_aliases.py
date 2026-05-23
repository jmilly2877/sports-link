import json

FILES = [
    ("src/data/mlb_players.js", "MLB_PLAYERS"),
    ("src/data/nba_players.js", "NBA_PLAYERS"),
    ("src/data/nfl_players.js", "NFL_PLAYERS"),
]

with open("src/data/raw/college_aliases.json") as f:
    aliases = json.load(f)

def normalize_college(college):
    if not college:
        return []

    # split transfers
    parts = [p.strip() for p in str(college).split(";")]

    cleaned = []

    for part in parts:
        key = part.lower().strip()

        canonical = aliases.get(key, part)

        if canonical and canonical not in cleaned:
            cleaned.append(canonical)

    return cleaned

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
            continue

        new_colleges = []

        for c in original:
            new_colleges.extend(normalize_college(c))

        # dedupe
        new_colleges = sorted(list(set(new_colleges)))

        if new_colleges != original:
            p["college"] = new_colleges
            updated += 1

    with open(path, "w") as f:
        f.write(f"export const {export_name} = ")
        json.dump(players, f, indent=2)
        f.write(";")

    print("Updated players:", updated)

print("\nDone.")
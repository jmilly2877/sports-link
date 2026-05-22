import json
import re

MLB_FILE = "src/data/mlb_players.js"

def clean_js_export(text):
    return text.replace("export const MLB_PLAYERS = ", "").rstrip().rstrip(";")

def canonical_name(name):
    name = str(name).strip()
    name = re.sub(r"\s+", " ", name)

    # Normalize spaced initials: A. J. Burnett -> A.J. Burnett
    name = re.sub(r"\b([A-Z])\.\s+([A-Z])\.\s+", r"\1.\2. ", name)

    # Normalize unpunctuated two-letter initials: AJ Burnett -> A.J. Burnett
    parts = name.split(" ")
    if len(parts) >= 2 and re.fullmatch(r"[A-Z]{2}", parts[0]):
        initials = ".".join(list(parts[0])) + "."
        name = " ".join([initials] + parts[1:])

    return name

with open(MLB_FILE, "r") as f:
    players = json.loads(clean_js_export(f.read()))

merged = {}
duplicates_found = 0

for p in players:
    cname = canonical_name(p["name"])

    if cname not in merged:
        merged[cname] = {
            "name": cname,
            "teams": set(),
            "college": set(),
            "numbers": set(),
            "league": "MLB"
        }
    else:
        duplicates_found += 1

    merged[cname]["teams"].update(p.get("teams", []))
    merged[cname]["college"].update(p.get("college", []))
    merged[cname]["numbers"].update(str(n).replace(".0", "").strip() for n in p.get("numbers", []))

output = []

for p in merged.values():
    output.append({
        "name": p["name"],
        "teams": sorted(p["teams"]),
        "college": sorted(c for c in p["college"] if c),
        "numbers": sorted(
            [n for n in p["numbers"] if n and n != "nan"],
            key=lambda x: int(x) if str(x).isdigit() else 999
        ),
        "league": "MLB"
    })

output = sorted(output, key=lambda x: x["name"])

with open(MLB_FILE, "w") as f:
    f.write("export const MLB_PLAYERS = ")
    f.write(json.dumps(output, indent=2))
    f.write(";\n")

print("Original players:", len(players))
print("Final players:", len(output))
print("Duplicates merged:", duplicates_found)

for name in ["A.J. Burnett", "A.J. Puk", "A.J. Minter", "A.J. Pierzynski"]:
    match = next((p for p in output if p["name"] == name), None)
    print(name, match)
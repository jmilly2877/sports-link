import pandas as pd
import json

df = pd.read_csv("src/data/raw/college_aliases.csv")

aliases = {}

for _, row in df.iterrows():
    raw = str(row["college"]).strip()
    canonical = str(row["suggested_canonical"]).strip()

    if not raw or raw == "nan":
        continue

    if canonical and canonical != "nan":
        aliases[raw.lower()] = canonical

print("Aliases:", len(aliases))

with open("src/data/raw/college_aliases.json", "w") as f:
    json.dump(aliases, f, indent=2)

print("Created src/data/raw/college_aliases.json")
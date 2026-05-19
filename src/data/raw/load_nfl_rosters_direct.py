import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import pandas as pd

# Start small. Once this works, expand to 2002–2025/2026.
YEARS = list(range(2002, 2026))

frames = []

for year in YEARS:
    url = f"https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_{year}.csv"
    print("Loading", year)

    df = pd.read_csv(url)
    df["season"] = year
    frames.append(df)

all_df = pd.concat(frames, ignore_index=True)

print("Rows:", len(all_df))
print("Columns:")
print(all_df.columns.tolist())

print("\nFirst 5 rows:")
print(all_df.head())

all_df.to_csv("src/data/raw/nfl_rosters_raw.csv", index=False)

print("\nSaved src/data/raw/nfl_rosters_raw.csv")
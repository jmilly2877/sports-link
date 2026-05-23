import pandas as pd
import requests
from io import StringIO
import time

MISSING_FILE = "src/data/raw/mlb_modern_missing_colleges.csv"
OUT_FILE = "src/data/raw/mlb_draft_college_enrichment.csv"

START_YEAR = 2002
END_YEAR = 2026

missing = pd.read_csv(MISSING_FILE)
missing_names = set(missing["name"].astype(str).str.strip())

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

def clean_school(s):
    if pd.isna(s):
        return ""

    s = str(s).strip()
    s = pd.Series([s]).str.replace(r"\[[^\]]*\]", "", regex=True).iloc[0].strip()
    return s

def is_high_school(s):
    low = str(s).lower()

    high_school_terms = [
        "high school",
        " hs",
        "prep",
        "academy",
        "secondary school",
        "christian school",
        "catholic high",
    ]

    return any(term in low for term in high_school_terms)

rows = []

for year in range(START_YEAR, END_YEAR + 1):
    url = f"https://en.wikipedia.org/wiki/{year}_Major_League_Baseball_draft"
    print("Loading", year)

    try:
        html = requests.get(url, headers=headers, timeout=30).text
        tables = pd.read_html(StringIO(html))
    except Exception as e:
        print("FAILED", year, e)
        continue

    for table in tables:
        table.columns = [str(c).strip() for c in table.columns]

        cols = list(table.columns)

        player_col = next((c for c in cols if c.lower() == "player"), None)
        school_col = next((c for c in cols if c.lower() in ["school", "school/club team", "school/club"]), None)

        if not player_col or not school_col:
            continue

        for _, row in table.iterrows():
            player = str(row[player_col]).strip()
            school = clean_school(row[school_col])

            if not player or not school or player == "nan" or school == "nan":
                continue

            if player not in missing_names:
                continue

            if is_high_school(school):
                continue

            rows.append({
                "player_name": player,
                "college": school,
                "draft_year": year,
                "source": url
            })

    time.sleep(1)

df = pd.DataFrame(rows)

if len(df) > 0:
    df = df.drop_duplicates()
else:
    df = pd.DataFrame(columns=["player_name", "college", "draft_year", "source"])

df.to_csv(OUT_FILE, index=False)

print("\nDONE")
print("Rows:", len(df))
print("Created:", OUT_FILE)

for test in ["Alex Bregman", "Dansby Swanson", "Aaron Judge", "Buster Posey", "Paul Goldschmidt"]:
    print("\n", test)
    print(df[df["player_name"] == test])
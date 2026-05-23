import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import csv

MISSING_FILE = "src/data/raw/mlb_modern_missing_colleges.csv"
OUT_FILE = "src/data/raw/mlb_college_enrichment.csv"

missing_df = pd.read_csv(MISSING_FILE)
missing_names = set(missing_df["name"].astype(str).str.strip())

SCHOOL_INDEX_URL = "https://www.baseball-reference.com/schools/"

rows = []

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("Loading school index...")
html = requests.get(SCHOOL_INDEX_URL, headers=headers, timeout=20).text
soup = BeautifulSoup(html, "html.parser")

school_links = []

for a in soup.find_all("a", href=True):
    href = a["href"]
    text = a.get_text(strip=True)

    if href.startswith("/schools/") and href.endswith(".shtml") and text:
        school_links.append((text, "https://www.baseball-reference.com" + href))

school_links = list(dict(school_links).items())

print("School pages found:", len(school_links))

for school_name, url in school_links:
    try:
        print("Checking:", school_name)

        page = requests.get(url, headers=headers, timeout=20).text
        psoup = BeautifulSoup(page, "html.parser")

        links = psoup.find_all("a", href=True)

        for a in links:
            player_name = a.get_text(strip=True)

            if player_name in missing_names:
                rows.append({
                    "player_name": player_name,
                    "college": school_name,
                    "source": url
                })
                print("FOUND:", player_name, "->", school_name)

        time.sleep(3)

    except Exception as e:
        print("SKIP:", school_name, e)
        time.sleep(3)

df = pd.DataFrame(rows).drop_duplicates()

df.to_csv(OUT_FILE, index=False)

print("\nDONE")
print("Matches:", len(df))
print("Created:", OUT_FILE)
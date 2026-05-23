import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

OUT_FILE = "src/data/raw/mlb_college_enrichment.csv"

headers = {
    "User-Agent": "Mozilla/5.0"
}

url = "https://www.baseball-almanac.com/college/colleges.shtml"

print("Loading page...")

html = requests.get(url, headers=headers, timeout=30).text

print("HTML length:", len(html))

soup = BeautifulSoup(html, "html.parser")

text_lines = soup.get_text("\n").splitlines()

text_lines = [x.strip() for x in text_lines if x.strip()]

rows = []

current_college = None

college_pattern = re.compile(r"^(.*) Baseball Players$")

player_pattern = re.compile(r"^[A-Z][a-z]+(?: [A-Z][a-z\.\-']+)+$")

for line in text_lines:

    college_match = college_pattern.match(line)

    if college_match:
        current_college = college_match.group(1).strip()
        continue

    if not current_college:
        continue

    if player_pattern.match(line):

        rows.append({
            "player_name": line,
            "college": current_college,
            "source": url
        })

df = pd.DataFrame(rows).drop_duplicates()

df.to_csv(OUT_FILE, index=False)

print("\nDONE")
print("Rows:", len(df))
print(df.head(50).to_string())
print("Created:", OUT_FILE)
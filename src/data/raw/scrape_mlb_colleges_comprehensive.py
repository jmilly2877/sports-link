"""
Comprehensive MLB college scraper.

Sources (in order):
  1. Baseball Reference player pages (via Lahman bbrefID lookup)
  2. Baseball Reference player search (for players not in Lahman)

The script is resumable: progress is saved to a JSON file after each player.
Results are written to mlb_bref_colleges.csv as they're found.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/scrape_mlb_colleges_comprehensive.py

  # Resume from where it left off (skips already-processed players):
  python3 src/data/raw/scrape_mlb_colleges_comprehensive.py
"""

import pandas as pd
import requests
import re
import time
import json
import csv
import sys
from bs4 import BeautifulSoup
from collections import defaultdict
from pathlib import Path

# ─── Config ─────────────────────────────────────────────────────────────────

MISSING_FILE   = "src/data/raw/mlb_2000_present_missing_colleges.csv"
PEOPLE_FILE    = "src/data/raw/mlb/People.csv"
OUT_FILE       = "src/data/raw/mlb_bref_colleges.csv"
PROGRESS_FILE  = "src/data/raw/mlb_bref_colleges_progress.json"

# Seconds between BRef requests (they rate-limit aggressively)
DELAY_SECONDS  = 4.0
# Extra delay after a 429 or connection error
BACKOFF_SECONDS = 30.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

HS_TERMS = [
    "high school", " hs", " h.s.", "prep", "academy",
    "secondary school", "christian school", "catholic high",
]


# ─── Helpers ────────────────────────────────────────────────────────────────

def alpha_only(name: str) -> str:
    """Strip everything except letters and lowercase."""
    return re.sub(r"[^a-z]", "", name.lower())


def is_high_school(school: str) -> bool:
    low = school.lower()
    return any(t in low for t in HS_TERMS)


def extract_school_from_soup(soup: BeautifulSoup) -> str | None:
    """
    Parse the BRef player page for a college School: entry.
    Returns the school name (without city/state) or None.
    """
    info = soup.find("div", {"id": "info"})
    if not info:
        return None
    for p in info.find_all("p"):
        text = p.get_text(" ", strip=True)
        # Must contain 'School:' but NOT 'High School:'
        if re.search(r"(?<!High )School:", text):
            m = re.search(r"(?<!High )School:\s*(.+?)(?:\s*\([^)]*\))?\s*$", text)
            if m:
                school = m.group(1).strip()
                if not is_high_school(school):
                    return school
    return None


def fetch_bref_player(bbref_id: str) -> tuple[str | None, str]:
    """Fetch a BRef player page and return (school, url)."""
    url = (
        f"https://www.baseball-reference.com/players/"
        f"{bbref_id[0]}/{bbref_id}.shtml"
    )
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    school = extract_school_from_soup(soup)
    return school, url


def search_bref_for_player(name: str) -> str | None:
    """
    Search BRef and return a bbrefID if exactly one player matches.
    """
    search_url = (
        "https://www.baseball-reference.com/search/search.fcgi"
        f"?search={requests.utils.quote(name)}"
    )
    r = requests.get(search_url, headers=HEADERS, timeout=20, allow_redirects=True)
    r.raise_for_status()

    # If BRef redirected directly to a player page, extract bbrefID from URL
    if "/players/" in r.url and r.url.endswith(".shtml"):
        m = re.search(r"/players/[a-z]/([^/]+)\.shtml", r.url)
        if m:
            return m.group(1)

    # Otherwise parse search results for exactly one player link
    soup = BeautifulSoup(r.text, "html.parser")
    player_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.match(r"^/players/[a-z]/[a-z0-9.]+\.shtml$", href):
            player_links.append(href)

    if len(player_links) == 1:
        m = re.search(r"/players/[a-z]/([^/]+)\.shtml", player_links[0])
        if m:
            return m.group(1)

    return None


# ─── Build Lahman name → bbrefID lookup ────────────────────────────────────

def build_lahman_lookup(people_file: str) -> tuple[dict, dict]:
    """
    Returns:
      unique_map:   alpha_name -> bbrefID   (only when exactly one player matches)
      ambig_map:    alpha_name -> [bbrefID, ...]
    """
    people = pd.read_csv(people_file)
    people["full_name"] = (
        people["nameFirst"].fillna("") + " " + people["nameLast"].fillna("")
    ).str.strip()
    people["alpha"] = people["full_name"].apply(alpha_only)

    alpha_to_ids: dict[str, list[str]] = defaultdict(list)
    for _, row in people.iterrows():
        bbref = str(row.get("bbrefID", "")).strip()
        if bbref and bbref != "nan":
            alpha_to_ids[row["alpha"]].append(bbref)

    unique_map = {k: v[0] for k, v in alpha_to_ids.items() if len(v) == 1}
    ambig_map  = {k: v    for k, v in alpha_to_ids.items() if len(v) > 1}
    return unique_map, ambig_map


# ─── Load progress ──────────────────────────────────────────────────────────

def load_progress(path: str) -> dict:
    if Path(path).exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_progress(path: str, progress: dict) -> None:
    with open(path, "w") as f:
        json.dump(progress, f)


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Process only N players (for testing)")
    args = parser.parse_args()

    missing = pd.read_csv(MISSING_FILE)
    missing["alpha"] = missing["name"].apply(alpha_only)
    if args.limit:
        missing = missing.head(args.limit)

    unique_map, ambig_map = build_lahman_lookup(PEOPLE_FILE)

    progress = load_progress(PROGRESS_FILE)
    # progress keys: player names already processed
    # progress values: {"college": str|null, "source": str, "bbrefID": str}

    # Open output CSV (append mode if resuming)
    out_path = Path(OUT_FILE)
    write_header = not out_path.exists() or out_path.stat().st_size == 0
    out_f = open(OUT_FILE, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=["player_name", "college", "bbref_id", "source"])
    if write_header:
        writer.writeheader()

    total   = len(missing)
    skipped = 0
    found   = 0
    not_found_no_bbref = 0
    no_college = 0
    errors  = 0

    print(f"Total players to process: {total}")
    print(f"Already processed: {len(progress)}")
    print()

    for i, row in missing.iterrows():
        name  = str(row["name"]).strip()
        alpha = row["alpha"]
        teams = str(row.get("teams", "")).strip()

        # Skip if already processed
        if name in progress:
            skipped += 1
            if progress[name].get("college"):
                found += 1
            continue

        # ── Resolve bbrefID ───────────────────────────────────────────────
        bbref_id = None

        if alpha in unique_map:
            bbref_id = unique_map[alpha]
        elif alpha in ambig_map:
            # Ambiguous: can't safely pick — fall through to search
            pass

        # ── Fetch BRef player page ────────────────────────────────────────
        school = None
        source_url = None

        if bbref_id:
            try:
                school, source_url = fetch_bref_player(bbref_id)
                time.sleep(DELAY_SECONDS)
            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"  [429 rate limit] backing off {BACKOFF_SECONDS}s …")
                    time.sleep(BACKOFF_SECONDS)
                    try:
                        school, source_url = fetch_bref_player(bbref_id)
                        time.sleep(DELAY_SECONDS)
                    except Exception as e2:
                        print(f"  ERROR (retry) {name}: {e2}")
                        errors += 1
                        progress[name] = {"college": None, "source": "error", "bbrefID": bbref_id}
                        save_progress(PROGRESS_FILE, progress)
                        continue
                else:
                    print(f"  HTTP {e.response.status_code} for {name} ({bbref_id})")
                    errors += 1
                    progress[name] = {"college": None, "source": f"http_{e.response.status_code}", "bbrefID": bbref_id}
                    save_progress(PROGRESS_FILE, progress)
                    continue
            except Exception as e:
                print(f"  ERROR {name}: {e}")
                errors += 1
                progress[name] = {"college": None, "source": "error", "bbrefID": bbref_id or ""}
                save_progress(PROGRESS_FILE, progress)
                time.sleep(DELAY_SECONDS)
                continue
        else:
            # No bbrefID — try BRef search
            try:
                bbref_id = search_bref_for_player(name)
                time.sleep(DELAY_SECONDS)
                if bbref_id:
                    school, source_url = fetch_bref_player(bbref_id)
                    time.sleep(DELAY_SECONDS)
                else:
                    not_found_no_bbref += 1
                    progress[name] = {"college": None, "source": "not_found", "bbrefID": ""}
                    save_progress(PROGRESS_FILE, progress)
                    continue
            except Exception as e:
                print(f"  SEARCH ERROR {name}: {e}")
                errors += 1
                progress[name] = {"college": None, "source": "error", "bbrefID": ""}
                save_progress(PROGRESS_FILE, progress)
                time.sleep(DELAY_SECONDS)
                continue

        # ── Record result ─────────────────────────────────────────────────
        if school:
            found += 1
            writer.writerow({
                "player_name": name,
                "college": school,
                "bbref_id": bbref_id or "",
                "source": source_url or "",
            })
            out_f.flush()
            print(f"[{i+1}/{total}] {name} -> {school}")
        else:
            no_college += 1
            if (i % 50) == 0:
                print(f"[{i+1}/{total}] {name} -> (no college found)")

        progress[name] = {
            "college": school,
            "source": source_url or "",
            "bbrefID": bbref_id or "",
        }
        # Save progress every 10 players
        if len(progress) % 10 == 0:
            save_progress(PROGRESS_FILE, progress)

    save_progress(PROGRESS_FILE, progress)
    out_f.close()

    print()
    print("═" * 50)
    print(f"Total:          {total}")
    print(f"Skipped (done): {skipped}")
    print(f"College found:  {found}")
    print(f"No college:     {no_college}")
    print(f"No BRef ID:     {not_found_no_bbref}")
    print(f"Errors:         {errors}")
    print(f"Output:         {OUT_FILE}")


if __name__ == "__main__":
    main()

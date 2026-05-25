"""
Normalizes all raw Lahman/Retrosheet team codes in mlb_players.js to full
human-readable team names.

The Lahman Appearances.csv uses historical Retrosheet franchise codes that
weren't in convert_mlb.py's TEAM_MAP, so they passed through as-is.
This script expands all of them in-place on the final mlb_players.js.

Also deduplicates teams per player after normalization (e.g. "NYA" and
"New York Yankees" both becoming "New York Yankees").

Safe to re-run — idempotent.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/normalize_mlb_teams.py
"""

import json, re

MLB_FILE = "src/data/mlb_players.js"

# ─── Comprehensive Lahman / Retrosheet team code map ─────────────────────────

NORMALIZE = {
    # ── American League franchises ───────────────────────────────────────────
    "NYA": "New York Yankees",
    "NYY": "New York Yankees",
    "BOS": "Boston Red Sox",
    "CHA": "Chicago White Sox",
    "CHW": "Chicago White Sox",
    "CLE": "Cleveland Guardians",     # franchise (was Indians, Naps, Blues)
    "DET": "Detroit Tigers",
    "PHA": "Philadelphia Athletics",   # moved to KC then Oakland
    "SLA": "St. Louis Browns",         # became Baltimore Orioles 1954
    "SLB": "St. Louis Browns",
    "WS1": "Washington Senators",      # first franchise → Minnesota Twins
    "WA1": "Washington Senators",
    "WA2": "Washington Senators",
    "WS2": "Washington Senators",      # expansion franchise → Texas Rangers
    "BAL": "Baltimore Orioles",
    "BLA": "Baltimore Orioles",        # early AL Baltimore Orioles (1901-02)
    "BL2": "Baltimore Orioles",
    "BL3": "Baltimore Orioles",
    "KC1": "Kansas City Athletics",    # Philadelphia A's moved to KC 1955
    "KCA": "Kansas City Royals",
    "KCR": "Kansas City Royals",
    "KCM": "Kansas City Royals",       # Lahman alternate code
    "SEP": "Seattle Pilots",           # 1969 only → became Brewers
    "MIL": "Milwaukee Brewers",
    "ML4": "Milwaukee Brewers",        # alternate code
    "MIN": "Minnesota Twins",
    "CAL": "California Angels",
    "ANA": "Anaheim Angels",
    "LAA": "Los Angeles Angels",
    "OAK": "Oakland Athletics",
    "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",
    "SEA": "Seattle Mariners",
    "TBA": "Tampa Bay Rays",
    "TBR": "Tampa Bay Rays",
    "TBD": "Tampa Bay Rays",           # Devil Rays early code
    "HOU": "Houston Astros",           # also HO1 in some datasets

    # ── National League franchises ───────────────────────────────────────────
    "CHN": "Chicago Cubs",
    "CHC": "Chicago Cubs",
    "SLN": "St. Louis Cardinals",
    "STL": "St. Louis Cardinals",
    "PIT": "Pittsburgh Pirates",
    "CIN": "Cincinnati Reds",
    "CN1": "Cincinnati Reds",          # very early code
    "NY1": "New York Giants",          # NL Giants → SF Giants
    "SFN": "San Francisco Giants",
    "SFG": "San Francisco Giants",
    "BRO": "Brooklyn Dodgers",         # Brooklyn Superbas/Robins/Dodgers
    "BRK": "Brooklyn Dodgers",
    "LAN": "Los Angeles Dodgers",
    "LAD": "Los Angeles Dodgers",
    "BSN": "Boston Braves",            # was Bees, Rustlers, Doves → Milwaukee
    "BSE": "Boston Braves",
    "ML1": "Milwaukee Braves",         # NL Braves in Milwaukee 1953-65
    "ATL": "Atlanta Braves",
    "PHI": "Philadelphia Phillies",
    "PH1": "Philadelphia Phillies",    # very early NL
    "PH4": "Philadelphia Phillies",
    "MON": "Montreal Expos",
    "WAS": "Washington Nationals",
    "WSN": "Washington Nationals",
    "NYN": "New York Mets",
    "NYM": "New York Mets",
    "SDN": "San Diego Padres",
    "SDP": "San Diego Padres",
    "COL": "Colorado Rockies",
    "ARI": "Arizona Diamondbacks",
    "FLO": "Florida Marlins",
    "FLA": "Florida Marlins",
    "MIA": "Miami Marlins",

    # ── Historical NL / AA / PL franchises (pre-1900 era) ───────────────────
    "LS1": "Louisville Colonels",
    "LS2": "Louisville Colonels",
    "LS3": "Louisville Colonels",
    "CL1": "Cleveland Blues",
    "CL2": "Cleveland Blues",
    "CL3": "Cleveland Spiders",
    "CL4": "Cleveland Spiders",
    "CL5": "Cleveland Blues",
    "SL1": "St. Louis Browns",         # AA franchise
    "SL2": "St. Louis Browns",
    "SL3": "St. Louis Browns",
    "SL4": "St. Louis Browns",
    "SL5": "St. Louis Maroons",
    "BL1": "Baltimore Orioles",        # NL/AA early
    "BL4": "Baltimore Orioles",
    "CH1": "Chicago Cubs",             # early NL White Stockings
    "CH2": "Houston Colt .45s",        # Astros' original name
    "CH3": "Chicago Cubs",
    "BF1": "Buffalo Bisons",           # NL/AA Buffalo
    "BFN": "Buffalo Bisons",
    "BFP": "Buffalo Bisons",
    "BR1": "Brooklyn Atlantics",       # very early
    "BR2": "Brooklyn Dodgers",
    "BR3": "Brooklyn Dodgers",
    "BR4": "Brooklyn Dodgers",
    "CN2": "Cincinnati Reds",
    "CN3": "Cincinnati Reds",
    "DTN": "Detroit Tigers",           # NL Detroit
    "HR1": "Hartford Dark Blues",
    "IN1": "Indianapolis Blues",
    "IN2": "Indianapolis Hoosiers",
    "IN3": "Indianapolis Hoosiers",
    "KC2": "Kansas City Cowboys",      # UA
    "MU1": "Milwaukee Grays",
    "NH1": "New Haven Elm Citys",
    "NH2": "New Haven Elm Citys",
    "PH2": "Philadelphia Athletics",   # AA Athletics
    "PH3": "Philadelphia Athletics",
    "PR1": "Providence Grays",
    "RC1": "Rockford Forest Citys",
    "SR1": "Syracuse Stars",
    "TL1": "Troy Trojans",
    "TL2": "Troy Trojans",
    "WN1": "Washington Nationals",     # early NL
    "WN2": "Washington Nationals",
    "WO1": "Worcester Ruby Legs",
    "ALT": "Altoona Mountain Citys",   # UA 1884
    "BAL": "Baltimore Orioles",
    "BEG": "Baltimore Egrets",
    "BE":  "Baltimore Egrets",
    "BM1": "Baltimore Marylands",
    "NE":  "Newark Eagles",            # actually this might be Newark Eagles Negro League

    # ── Negro Leagues (Lahman added these in v2021+) ─────────────────────────
    "ABCs": "Indianapolis ABCs",
    "ABC":  "Indianapolis ABCs",
    "AC1":  "Atlantic City Bacharach Giants",
    "AC2":  "Atlantic City Bacharach Giants",
    "ACB":  "Atlantic City Bacharach Giants",
    "ACG":  "Atlantic City Bacharach Giants",
    "BBB":  "Birmingham Black Barons",
    "BBS":  "Baltimore Black Sox",
    "BRG":  "Brooklyn Royal Giants",
    "CAG":  "Cuban Giants",
    "CAS":  "Cuban Stars",
    "CAB":  "Cuban Stars",
    "CBS":  "Cuban Stars",
    "CHG":  "Chicago American Giants",
    "CLI":  "Cleveland Buckeyes",
    "CLS":  "Cleveland Stars",
    "DS":   "Detroit Stars",
    "DS2":  "Detroit Stars",
    "HG":   "Homestead Grays",
    "INE":  "Indianapolis ABCs",
    "JRC":  "Jersey City Cubans",
    "KC2":  "Kansas City Monarchs",
    "KCM2": "Kansas City Monarchs",
    "MRS":  "Memphis Red Sox",
    "NBA":  "Newark Eagles",
    "NBY":  "Newark Eagles",
    "NE2":  "Newark Eagles",
    "NLG":  "New York Lincoln Giants",
    "NYC":  "New York Cubans",
    "NYC2": "New York Cubans",
    "NYG2": "New York Lincoln Giants",
    "PHH":  "Philadelphia Hilldale",
    "PHS":  "Philadelphia Stars",
    "PS":   "Pittsburgh Crawfords",
    "SCB":  "St. Louis Stars",
    "SLM":  "St. Louis Stars",
    "SLS":  "St. Louis Stars",
    "SUM":  "Sunbury Indians",
    "WMG":  "Washington Elite Giants",

    # ── More Negro League teams ───────────────────────────────────────────────
    "HIL":  "Philadelphia Hilldale",   # Philadelphia Hilldale Daisies — Lahman NLG
    "PC":   "Pittsburgh Crawfords",    # Pittsburgh Crawfords (Satchel Paige, Josh Gibson)
    "HBG":  "Harrisburg Giants",
    "SLG":  "St. Louis Giants",
    "NY4":  "New York Black Yankees",
    "BLN":  "Baltimore Elite Giants",
    "NEG":  "Newark Giants",
    "NWB":  "Newark Bears",
    "NLS":  "Newark Stars",
    "SOX":  "Chicago American Giants", # alternate code
    "COG":  "Columbus Buckeyes",
    "DM":   "Des Moines Boosters",
    "PG":   "Pittsburgh Giants",
    "AC":   "Atlantic City Bacharach Giants",
    "CSW":  "Cuban Stars (West)",
    "CSE":  "Cuban Stars (East)",
    "CSH":  "Cuban Stars",
    "CS":   "Cuban Stars",
    "CBG":  "Cuban Giants",
    "CBN":  "Cuban Giants",
    "CBB":  "Cuban Giants",
    "CBR":  "Cuban Giants",
    "CBE":  "Cuban Stars (East)",
    "CCG":  "Chicago Columbia Giants",
    "CCB":  "Chicago Columbia Giants",
    "CC":   "Chicago Columbia Giants",
    "CC2":  "Chicago Columbia Giants",
    "CCU":  "Cuban Stars",
    "CU":   "Cuban Stars",
    "CUP":  "Cuban Stars",
    "CXG":  "Chicago X-Giants",
    "CTG":  "Chicago Union Giants",
    "CT":   "Chicago Unions",
    "CHG2": "Chicago American Giants",
    "CHF":  "Chicago Giants",
    "CHP":  "Chicago Panthers",
    "CHT":  "Chicago Tigers",
    "CHU":  "Chicago Unions",
    "CIC":  "Cincinnati Tigers",
    "COB":  "Columbus Blue Birds",
    "CRS":  "Columbus Red Birds",
    "CL6":  "Cleveland Elites",
    "CLP":  "Cleveland Tate Stars",
    "CNU":  "Cincinnati Clowns",
    "LEL":  "Louisville-Nashville Elite Giants",
    "CEL":  "Cincinnati-Indianapolis Clowns",
    "CEG":  "Cincinnati Clowns",
    "LOW":  "Louisville Elite Giants",
    "LRG":  "Louisville Red Caps",
    "LVB":  "Las Vegas Bears",
    "MB":   "Mobile Bears",
    "MGS":  "Montgomery Grey Sox",
    "MID":  "Midland West Texas",
    "MLA":  "Milwaukee Bears",
    "ML2":  "Milwaukee Bears",
    "ML3":  "Milwaukee Bears",
    "MLU":  "Milwaukee Bears",
    "MOH":  "Monroe Monarchs",
    "MRM":  "Memphis Red Sox",         # alternate code
    "ND":   "Norfolk Diamonds",
    "NEW":  "Newark Peppers",          # Federal League
    "NS":   "Nashville Standards",
    "NY2":  "New York Giants",         # very early NL
    "NY3":  "New York Metropolitans",
    "NYB":  "New York Bacharach Giants",
    "NYP":  "New York Nationals",
    "OKM":  "Oklahoma Monarchs",
    "PBG":  "Petersburg Goobers",
    "PC2":  "Pittsburgh Crawfords",
    "PFG":  "Philadelphia Giants",     # 1902-1910 era
    "PHH":  "Philadelphia Hilldale",
    "PHP":  "Philadelphia Pythians",   # earliest Black pro team
    "PHN":  "Philadelphia Nationals",
    "PHU":  "Philadelphia Quakers",    # UA
    "PK":   "Pittsburgh Keys",
    "PT1":  "Pittsburgh Crawfords",
    "PTF":  "Pittsburgh Keystones",
    "PTG":  "Pittsburgh Giants",
    "PTP":  "Pittsburgh Stars",
    "QG":   "Quaker Giants",
    "RC2":  "Rock Island Independents",
    "RIC":  "Richmond Giants",
    "SC1":  "St. Louis Cuban Stars",
    "SE1":  "Seattle Steelheads",
    "SEN":  "Senators",
    "SLF":  "St. Louis Giants",
    "SLU":  "St. Louis Union Giants",
    "SNS":  "Somerville Stars",
    "SPG":  "Springfield Stars",
    "SPU":  "St. Paul Gophers",
    "SR2":  "Syracuse Stars",
    "TC":   "Twin Cities",
    "TC2":  "Twin Cities",
    "TIC":  "Toledo Tigers",
    "TRN":  "Trenton Cuban Giants",
    "TRO":  "Troy Haymakers",
    "TT":   "Toledo Tigers",
    "WAP":  "Washington Potomacs",
    "WBS":  "Wilkes-Barre Bears",
    "WEG":  "Washington Elite Giants",
    "WIL":  "Wilmington Giants",
    "WMP":  "Wilmington Potomacs",
    "WOR":  "Worcester Ruby Legs",
    "WP":   "Washington Pilots",
    "WS3":  "Washington Senators",
    "WS4":  "Washington Senators",
    "WS5":  "Washington Senators",
    "WS6":  "Washington Senators",
    "WS7":  "Washington Senators",
    "WS8":  "Washington Senators",
    "WS9":  "Washington Senators",
    "WSU":  "Washington University",
    "BLF":  "Baltimore Terrapins",     # Federal League
    "BLU":  "Baltimore Monumentals",   # UA 1884
    "BRF":  "Brooklyn Tip-Tops",       # Federal League
    "BRP":  "Brooklyn Wonders",        # PL 1890
    "BS1":  "Boston Reds",             # PL/AA
    "BS2":  "Boston Braves",
    "BSP":  "Boston Pilgrims",         # early Red Sox name
    "BSU":  "Boston Reds",             # UA
    "BUF":  "Buffalo Bisons",
    "DTS":  "Detroit Tigers",          # alternate
    "DW":   "Detroit Wolves",
    "ELI":  "Elgin Whigs",
    "FLP":  "Baltimore Terrapins",
    "FW1":  "Fort Wayne Kekiongas",    # very first pro game
    "GOR":  "Gorham Stars",
    "HAR":  "Hartford Dark Blues",
    "HSS":  "Harrisburg Stars",
    "IA":   "Indianapolis Clowns",
    "IAB":  "Indianapolis ABCs",
    "IC":   "Indianapolis Clowns",
    "ID":   "Indianapolis Diamonds",
    "IND":  "Indianapolis Hoosiers",
    "KCF":  "Kansas City Monarchs",
    "KCG":  "Kansas City Giants",
    "KCN":  "Kansas City Monarchs",
    "KCU":  "Kansas City Blues",
    "KEO":  "Keokuk Westerns",
    "KRG":  "Kansas City Royal Giants",
    "ATH":  "Philadelphia Athletics",  # alternate Lahman code
    "PRO":  "Providence Grays",        # NL 1878-1885
    "CTS":  "Cuban Stars",             # alternate code

    # ── Miscellaneous ─────────────────────────────────────────────────────────
    "AB":   "Albuquerque Dukes",
    "AB2":  "Albuquerque Dukes",
    "AB3":  "Albuquerque Dukes",
    "BCA":  "Binghamton Crickets",
}

# ─── Load ─────────────────────────────────────────────────────────────────────

with open(MLB_FILE) as f:
    raw = f.read()
players = json.loads(raw.replace("export const MLB_PLAYERS = ", "").rstrip(";\n"))
print(f"Loaded {len(players):,} players")

# ─── Normalize ────────────────────────────────────────────────────────────────

all_teams_before: set[str] = set()
for p in players:
    all_teams_before.update(p.get("teams", []))

replacements = 0
removed      = 0
changed      = 0

for player in players:
    original = list(player.get("teams", []))
    cleaned: set[str] = set()

    for team in original:
        canonical = NORMALIZE.get(team, team)
        if canonical != team:
            replacements += 1
        cleaned.add(canonical)

    new_teams = sorted(cleaned)
    if new_teams != player.get("teams", []):
        player["teams"] = new_teams
        changed += 1

# ─── Report remaining raw codes ───────────────────────────────────────────────

all_teams_after: set[str] = set()
for p in players:
    all_teams_after.update(p.get("teams", []))

still_raw = sorted(
    t for t in all_teams_after
    if " " not in t and len(t) <= 4 and t == t.upper()
)
print(f"Replacements made:    {replacements:,}")
print(f"Players changed:      {changed:,}")

if still_raw:
    print(f"\n⚠️  Still-raw codes ({len(still_raw)}): {still_raw}")
else:
    print("\n✓  No raw codes remaining")

# ─── Write ────────────────────────────────────────────────────────────────────

players.sort(key=lambda x: x["name"])

with open(MLB_FILE, "w") as f:
    f.write("export const MLB_PLAYERS = ")
    json.dump(players, f, indent=2)
    f.write(";")

print(f"\nWrote {MLB_FILE}")
print(f"\nFinal unique team strings: {len(all_teams_after)}")
print("\nAll team values:")
for t in sorted(all_teams_after):
    print(f"  {t}")

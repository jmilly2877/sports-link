"""
Enriches MLB jersey numbers in mlb_players.js using two sources:

  1. Curated historical list — famous players whose numbers are universally
     documented (Hall of Famers, retired numbers, household names).

  2. Wikipedia API — for broader coverage of notable players.

Numbers are only ever ADDED, never overwritten — safe to re-run.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/enrich_mlb_numbers.py
"""

import json, re, ssl, time, urllib.request, urllib.parse
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

MLB_FILE = "src/data/mlb_players.js"
PROGRESS_FILE = "src/data/raw/wiki_mlb_progress.json"
HEADERS = {"User-Agent": "sports-link-research/1.0 (educational non-commercial project)"}

def alpha(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


# ─── Curated historical jersey numbers ───────────────────────────────────────
# Canonical number listed first (most associated). Players who wore different
# numbers across teams have all significant ones listed.

CURATED = {
    # ── All-Time Legends ─────────────────────────────────────────────────────
    "Babe Ruth":            [3],
    "Lou Gehrig":           [4],
    "Joe DiMaggio":         [5],
    "Mickey Mantle":        [7],
    "Yogi Berra":           [8],
    "Ted Williams":         [9],
    "Stan Musial":          [6],
    "Willie Mays":          [24],
    "Hank Aaron":           [44],
    "Jackie Robinson":      [42],
    "Roberto Clemente":     [21],
    "Bob Gibson":           [45],
    "Sandy Koufax":         [32],
    "Don Drysdale":         [53],
    "Whitey Ford":          [16],
    "Warren Spahn":         [21],
    "Roy Campanella":       [39],
    "Duke Snider":          [4],
    "Pee Wee Reese":        [1],
    "Phil Rizzuto":         [10],
    "Joe Gordon":           [4],
    "Enos Slaughter":       [9],
    "Red Schoendienst":     [2],
    "Richie Ashburn":       [1],
    "Ralph Kiner":          [4],
    "Early Wynn":           [24],
    "Bob Lemon":            [21],

    # ── Hall of Famers (1960s-1990s) ─────────────────────────────────────────
    "Ernie Banks":          [14],
    "Billy Williams":       [26],
    "Ron Santo":            [10],
    "Fergie Jenkins":       [31],
    "Lou Brock":            [20],
    "Bob Gibson":           [45],
    "Orlando Cepeda":       [30],
    "Juan Marichal":        [27],
    "Willie McCovey":       [44],
    "Willie Stargell":      [8],
    "Roberto Clemente":     [21],
    "Richie Allen":         [15],
    "Carl Yastrzemski":     [8],
    "Tony Conigliaro":      [25],
    "Jim Lonborg":          [16],
    "Harmon Killebrew":     [3],
    "Tony Oliva":           [6],
    "Rod Carew":            [29],
    "Bert Blyleven":        [28],
    "Frank Robinson":       [20],
    "Brooks Robinson":      [5],
    "Boog Powell":          [26],
    "Jim Palmer":           [22],
    "Luis Aparicio":        [11],
    "Nellie Fox":           [2],
    "Early Wynn":           [24],
    "Minnie Minoso":        [9],
    "Al Kaline":            [6],
    "Norm Cash":            [25],
    "Denny McLain":         [17],
    "Mickey Lolich":        [29],
    "Roger Maris":          [9],
    "Whitey Herzog":        [24],
    "Johnny Bench":         [5],
    "Pete Rose":            [14],
    "Joe Morgan":           [8],
    "Tony Perez":           [24],
    "Ken Griffey Sr.":      [30],
    "Tom Seaver":           [41],
    "Jerry Koosman":        [36],
    "Tommie Agee":          [20],
    "Bud Harrelson":        [3],
    "Tug McGraw":           [45],
    "Mike Schmidt":         [20],
    "Steve Carlton":        [32],
    "Greg Luzinski":        [19],
    "Larry Bowa":           [10],
    "Bob Boone":            [7],
    "Mike Stargell":        [8],
    "Dave Parker":          [39],
    "Rich Gossage":         [54],
    "Reggie Jackson":       [44, 9],
    "Catfish Hunter":       [27],
    "Vida Blue":            [14],
    "Joe Rudi":             [20],
    "Sal Bando":            [6],
    "Bert Campaneris":      [19],
    "Gene Tenace":          [18],
    "Rollie Fingers":       [34],
    "Nolan Ryan":           [30, 34],
    "Jim Bibby":            [40],
    "George Brett":         [5],
    "Frank White":          [20],
    "Amos Otis":            [26],
    "Hal McRae":            [11],
    "Dan Quisenberry":      [29],
    "Robin Yount":          [19],
    "Paul Molitor":         [4],
    "Gorman Thomas":        [25],
    "Ted Simmons":          [23],
    "Mike Caldwell":        [32],
    "Rod Carew":            [29],
    "Bert Blyleven":        [28],
    "Larry Hisle":          [4],
    "Lyman Bostock":        [24],
    "Don Mattingly":        [23],
    "Dave Winfield":        [31],
    "Rickey Henderson":     [24, 22, 35],
    "Ron Guidry":           [49],
    "Tommy John":           [25],
    "Graig Nettles":        [9],
    "Chris Chambliss":      [10],
    "Willie Randolph":      [30],
    "Thurman Munson":       [15],
    "Reggie Jackson":       [44, 9],
    "Mike Torrez":          [37],
    "Cal Ripken Jr.":       [8],
    "Eddie Murray":         [33],
    "Mike Flanagan":        [46],
    "Ken Singleton":        [29],
    "Dennis Martinez":      [32],
    "Scott McGregor":       [23],
    "Rick Dempsey":         [24],
    "Gary Carter":          [8],
    "Andre Dawson":         [8, 10],
    "Tim Raines":           [30],
    "Steve Rogers":         [45],
    "Warren Cromartie":     [20],
    "Al Oliver":            [16],
    "Ellis Valentine":      [17],
    "Keith Hernandez":      [17, 37],
    "Dwight Gooden":        [16],
    "Darryl Strawberry":    [18],
    "Mookie Wilson":        [1],
    "Len Dykstra":          [4],
    "Ron Darling":          [12],
    "Sid Fernandez":        [50],
    "Gary Carter":          [8],
    "Rafael Santana":       [3],
    "Lee Mazzilli":         [16],
    "Howard Johnson":       [20],
    "Ryne Sandberg":        [23],
    "Mark Grace":           [17],
    "Andre Dawson":         [8, 10],
    "Rick Sutcliffe":       [40],
    "Lee Smith":            [46],
    "Shawon Dunston":       [12],
    "Jody Davis":           [7],
    "Keith Moreland":       [4],
    "Scott Sanderson":      [21],
    "Mike Marshall":        [28],
    "Tony Gwynn":           [19],
    "Steve Garvey":         [6],
    "Dave Winfield":        [31],
    "Alan Wiggins":         [24],
    "Ozzie Smith":          [1],
    "Jack Clark":           [22],
    "Vince Coleman":        [29],
    "Willie McGee":         [51],
    "Terry Pendleton":      [9],
    "Tom Herr":             [28],
    "John Tudor":           [37],
    "Joaquin Andujar":      [47],
    "Todd Worrell":         [38],
    "Dale Murphy":          [3],
    "Chris Chambliss":      [10],
    "Bob Horner":           [5],
    "Phil Niekro":          [35],
    "Bruce Sutter":         [42],
    "Claudell Washington":  [19],
    "Alan Trammell":        [3],
    "Lou Whitaker":         [1],
    "Kirk Gibson":          [23],
    "Jack Morris":          [47],
    "Dan Petry":            [46],
    "Larry Herndon":        [31],
    "Lance Parrish":        [13],
    "Dave Bergman":         [17],
    "Roger Clemens":        [21],
    "Wade Boggs":           [26],
    "Jim Rice":             [14],
    "Fred Lynn":            [19],
    "Dwight Evans":         [24],
    "Bob Stanley":          [46],
    "Bruce Hurst":          [47],
    "Dennis Eckersley":     [43],
    "Marty Barrett":        [17],
    "Dave Henderson":       [42],
    "Don Baylor":           [25],
    "Mike Boddicker":       [14],

    # ── 1990s Stars ──────────────────────────────────────────────────────────
    "Ken Griffey Jr.":      [24],
    "Frank Thomas":         [35],
    "Jeff Bagwell":         [5],
    "Craig Biggio":         [7],
    "Greg Maddux":          [31, 36],
    "Tom Glavine":          [47],
    "John Smoltz":          [29],
    "Chipper Jones":        [10],
    "David Justice":        [23],
    "Ron Gant":             [23, 10],
    "Fred McGriff":         [27],
    "Barry Bonds":          [24, 25],
    "Bobby Bonilla":        [24, 25],
    "Andy Van Slyke":       [18],
    "Jay Bell":             [5],
    "Doug Drabek":          [34],
    "Roberto Alomar":       [12],
    "Joe Carter":           [29],
    "Dave Steib":           [37],
    "Devon White":          [25],
    "John Olerud":          [9],
    "Pat Borders":          [10],
    "Juan Guzman":          [66],
    "Jack Morris":          [47],
    "David Cone":           [44, 36],
    "Jimmy Key":            [22],
    "Cal Ripken Jr.":       [8],
    "Brady Anderson":       [9],
    "Rafael Palmeiro":      [25],
    "Mike Mussina":         [35],
    "B.J. Surhoff":         [6],
    "Harold Baines":        [3],
    "Ivan Rodriguez":       [7],
    "Juan Gonzalez":        [19],
    "Ruben Sierra":         [21],
    "Nolan Ryan":           [34],
    "Rafael Palmeiro":      [25],
    "Kevin Brown":          [27],
    "Kenny Lofton":         [7],
    "Albert Belle":         [8],
    "Jim Thome":            [25],
    "Manny Ramirez":        [24],
    "Sandy Alomar Jr.":     [15],
    "Carlos Baerga":        [9],
    "Belle Albert":         [8],
    "Omar Vizquel":         [13],
    "Charles Nagy":         [41],
    "Orel Hershiser":       [55],
    "Dennis Martinez":      [32],
    "Jeff Kent":            [21, 12],
    "Matt Williams":        [9],
    "Robby Thompson":       [11],
    "Will Clark":           [22],
    "Mike Piazza":          [31],
    "Raul Mondesi":         [43],
    "Eric Karros":          [23],
    "Ramon Martinez":       [52],
    "Hideo Nomo":           [16],
    "Pedro Martinez":       [45],
    "Larry Walker":         [33],
    "Dante Bichette":       [10],
    "Vinny Castilla":       [9],
    "Andres Galarraga":     [14],
    "Ellis Burks":          [25],
    "Moises Alou":          [18],
    "Larry Walker":         [33],
    "Marquis Grissom":      [3],
    "Rondell White":        [12],
    "Mark Wohlers":         [49],
    "Ryan Klesko":          [28],
    "Javy Lopez":           [8],
    "Edgar Martinez":       [11],
    "Jay Buhner":           [19],
    "Tino Martinez":        [23],
    "Randy Johnson":        [51, 41],
    "Mark Langston":        [12],
    "Tim Salmon":           [15],
    "Jim Edmonds":          [15],
    "Mo Vaughn":            [42],
    "John Valentin":        [13],
    "Tom Gordon":           [36],
    "Curt Schilling":       [38],
    "Lenny Dykstra":        [4],
    "Darren Daulton":       [10],
    "John Kruk":            [29],
    "Terry Mulholland":     [23],
    "Tony Pena":            [23],
    "Jeff Conine":          [18],
    "Gary Sheffield":       [11, 10],
    "Charles Johnson":      [12],
    "Pat Rapp":             [30],
    "Devon White":          [25],
    "Alex Fernandez":       [32],
    "Liván Hernandez":      [35],
    "Chad Ogea":            [49],
    "Dante Bichette":       [10],
    "Roger Clemens":        [21, 22],
    "Mike Hampton":         [18],
    "Larry Bigbie":         [27],
    "Shawn Green":          [15],
    "Paul O'Neill":         [21],
    "Tino Martinez":        [23],
    "Scott Brosius":        [18],
    "Bernie Williams":      [51],
    "Chuck Knoblauch":      [11],
    "David Cone":           [36],
    "Andy Pettitte":        [46],
    "Jorge Posada":         [20],
    "Mariano Rivera":       [42],
    "Derek Jeter":          [2],
    "Orlando Hernandez":    [26],
    "Homer Bush":           [16],
    "Chad Curtis":          [9],
    "Darryl Strawberry":    [39],
    "David Justice":        [28],
    "Mike Stanton":         [30],
}


# ─── Load MLB players ─────────────────────────────────────────────────────────

with open(MLB_FILE) as f:
    raw = f.read()
players = json.loads(raw.replace("export const MLB_PLAYERS = ", "").rstrip(";\n"))
by_alpha = {alpha(p["name"]): p for p in players}
print(f"Loaded {len(players):,} players")


# ─── Source 1: Apply curated list ────────────────────────────────────────────

curated_applied = 0
curated_missing = []
for name, numbers in CURATED.items():
    key = alpha(name)
    if key not in by_alpha:
        curated_missing.append(name)
        continue
    p = by_alpha[key]
    existing = set(p.get("numbers", []))
    # Store as strings to match existing format
    new_nums = existing | {str(n) for n in numbers}
    if new_nums != existing:
        p["numbers"] = sorted(new_nums, key=lambda x: int(x))
        curated_applied += 1

print(f"Curated list: updated {curated_applied} players")
if curated_missing:
    print(f"  Not found in data: {curated_missing[:10]}{'...' if len(curated_missing) > 10 else ''}")


# ─── Source 2: Wikipedia API ──────────────────────────────────────────────────

ctx = ssl._create_default_https_context()

BASEBALL_KEYWORDS = re.compile(
    r"Major League Baseball|MLB|pitcher|catcher|outfielder|infielder|shortstop"
    r"|first baseman|second baseman|third baseman|left fielder|right fielder"
    r"|center fielder|American League|National League|World Series",
    re.IGNORECASE
)

TEAM_TOKENS = {
    "New York Yankees": ["Yankees"],
    "Boston Red Sox": ["Red Sox"],
    "Chicago Cubs": ["Cubs"],
    "Chicago White Sox": ["White Sox"],
    "Los Angeles Dodgers": ["Dodgers"],
    "San Francisco Giants": ["Giants"],
    "New York Mets": ["Mets"],
    "Oakland Athletics": ["Athletics", "A's"],
    "Kansas City Royals": ["Royals"],
    "Baltimore Orioles": ["Orioles"],
    "Minnesota Twins": ["Twins"],
    "Detroit Tigers": ["Tigers"],
    "Cleveland Indians": ["Indians", "Guardians"],
    "Cincinnati Reds": ["Reds"],
    "Pittsburgh Pirates": ["Pirates"],
    "St. Louis Cardinals": ["Cardinals"],
    "Philadelphia Phillies": ["Phillies"],
    "Houston Astros": ["Astros"],
    "Atlanta Braves": ["Braves"],
    "Seattle Mariners": ["Mariners"],
    "Texas Rangers": ["Rangers"],
    "California Angels": ["Angels"],
    "Milwaukee Brewers": ["Brewers"],
    "San Diego Padres": ["Padres"],
    "Montreal Expos": ["Expos"],
    "Toronto Blue Jays": ["Blue Jays"],
    "Colorado Rockies": ["Rockies"],
    "Florida Marlins": ["Marlins"],
    "Tampa Bay Devil Rays": ["Devil Rays", "Rays"],
    "Arizona Diamondbacks": ["Diamondbacks"],
    "Washington Nationals": ["Nationals"],
}

progress: dict = {}
if Path(PROGRESS_FILE).exists():
    with open(PROGRESS_FILE) as f:
        progress = json.load(f)
print(f"Wikipedia progress cache: {len(progress):,} already processed")

to_process = [
    p for p in players
    if not p.get("numbers")
    and p.get("teams")
    and p["name"] not in progress
    and len(p["name"].split()) >= 2
]
print(f"Wikipedia candidates: {len(to_process):,}")

LAST_429 = [0.0]  # track when we last hit a rate limit

def wiki_get(url, retries=5):
    for attempt in range(retries):
        # If we recently hit a 429, honour a cooldown
        wait_needed = LAST_429[0] + 30 - time.time()
        if wait_needed > 0:
            time.sleep(wait_needed)
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except Exception as e:
            msg = str(e)
            if "429" in msg:
                LAST_429[0] = time.time()
                wait = 30 * (attempt + 1)
                print(f"\n  Rate limited — waiting {wait}s...", flush=True)
                time.sleep(wait)
            elif attempt < retries - 1:
                time.sleep(3)
            else:
                raise

def name_in_title(player_name, wiki_title):
    parts = player_name.strip().split()
    if len(parts) < 2:
        return False
    first = re.sub(r"[^a-z]", "", parts[0].lower())
    last = re.sub(r"[^a-z]", "", parts[-1].lower())
    title_a = re.sub(r"[^a-z]", "", wiki_title.lower())
    return last in title_a and (first in title_a or len(first) <= 2)

# Team validation is skipped for MLB — historical team names are too varied
# (Brooklyn Dodgers, Philadelphia Athletics, etc.) and cause false negatives.
# Name match + baseball keyword check is sufficient guard against wrong articles.

wiki_found = 0
checked = 0
save_every = 100

try:
    for player in to_process:
        name = player["name"]
        checked += 1

        # Live progress counter (overwrites same line)
        print(f"\r  [{checked:,}/{len(to_process):,}] found {wiki_found} so far...  ", end="", flush=True)

        try:
            q = urllib.parse.quote(f"{name} baseball player")
            url = (f"https://en.wikipedia.org/w/api.php"
                   f"?action=query&list=search&format=json&srlimit=1&srsearch={q}")
            data = wiki_get(url)
            results = data.get("query", {}).get("search", [])
        except Exception as e:
            progress[name] = "search_error"
            continue

        if not results:
            progress[name] = "no_results"
            time.sleep(0.5)
            continue

        title = results[0]["title"]
        if not name_in_title(name, title):
            progress[name] = "name_mismatch"
            time.sleep(0.5)
            continue

        time.sleep(0.8)

        try:
            q2 = urllib.parse.quote(title)
            url2 = (f"https://en.wikipedia.org/w/api.php"
                    f"?action=query&prop=revisions&rvprop=content&format=json&titles={q2}")
            data2 = wiki_get(url2)
            pages = data2.get("query", {}).get("pages", {})
            page = next(iter(pages.values()))
            wikitext = page.get("revisions", [{}])[0].get("*", "")
        except Exception as e:
            progress[name] = "wikitext_error"
            continue

        if not BASEBALL_KEYWORDS.search(wikitext[:5000]):
            progress[name] = "not_baseball"
            time.sleep(0.5)
            continue

        m = re.search(
            r'\|\s*(?:jersey_number|number)\s*=\s*([0-9]+)',
            wikitext, re.IGNORECASE
        )
        if not m:
            progress[name] = f"no_number"
            time.sleep(1)
            continue

        num_str = m.group(1)
        num = int(num_str)
        if num == 0:
            progress[name] = f"number_zero"
            time.sleep(1)
            continue

        key = alpha(name)
        if key in by_alpha:
            p = by_alpha[key]
            existing = set(p.get("numbers", []))
            if num_str not in existing:
                p["numbers"] = sorted(existing | {num_str}, key=lambda x: int(x))
                progress[name] = num
                wiki_found += 1
                print(f"  ✓ {name}: #{num}  ({title})")
            else:
                progress[name] = num

        time.sleep(1)

        if checked % save_every == 0:
            with open(PROGRESS_FILE, "w") as f:
                json.dump(progress, f)
            print(f"  [{checked:,}/{len(to_process):,}] new this run: {wiki_found}")

except KeyboardInterrupt:
    print("\nInterrupted — saving progress...")

with open(PROGRESS_FILE, "w") as f:
    json.dump(progress, f)
print(f"Saved Wikipedia progress ({len(progress):,} entries)")


# ─── Write output ─────────────────────────────────────────────────────────────

players.sort(key=lambda x: x["name"])
with open(MLB_FILE, "w") as f:
    f.write("export const MLB_PLAYERS = ")
    json.dump(players, f, indent=2)
    f.write(";")

total_with_numbers = sum(1 for p in players if p.get("numbers"))
print(f"\nWrote {MLB_FILE}")
print(f"Curated additions: {curated_applied}")
print(f"Wikipedia additions: {wiki_found}")
print(f"Players with numbers: {total_with_numbers:,} / {len(players):,} "
      f"({total_with_numbers/len(players)*100:.1f}%)")

# Spot-checks
print("\nSpot-checks:")
checks = ["Don Mattingly", "Cal Ripken Jr.", "George Brett", "Mike Schmidt",
          "Reggie Jackson", "Nolan Ryan", "Robin Yount", "Johnny Bench",
          "Pete Rose", "Tom Seaver", "Ken Griffey Jr.", "Derek Jeter"]
for name in checks:
    p = by_alpha.get(alpha(name))
    if p:
        print(f"  {name}: #{p.get('numbers', [])}")
    else:
        print(f"  {name}: not found")

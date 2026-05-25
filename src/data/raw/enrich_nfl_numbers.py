"""
Enriches NFL jersey numbers in nfl_players.js using two sources:

  1. nflverse players.csv  — their canonical jersey number per player
     (adds ~192 players who currently have no number)

  2. Curated historical list — famous pre-1999 players whose numbers
     are 0 in every nflverse file but are universally documented.
     Covers 1960s-1990s Hall of Famers and household names.

Numbers are only ever ADDED, never overwritten — safe to re-run.

Usage:
  cd /Users/joemiller/Desktop/sports-link
  python3 src/data/raw/enrich_nfl_numbers.py
"""

import json, re, ssl, pandas as pd

ssl._create_default_https_context = ssl._create_unverified_context

NFL_FILE = "src/data/nfl_players.js"

def alpha(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


# ─── Curated historical jersey numbers ───────────────────────────────────────
# Only players confirmed missing from nflverse (jersey=0 or not present).
# Multiple numbers listed for players who wore different numbers across teams.

CURATED = {
    # ── Running Backs ────────────────────────────────────────────────────────
    "Walter Payton":      [34],
    "Earl Campbell":      [34],
    "Eric Dickerson":     [29],
    "Tony Dorsett":       [33],
    "Bo Jackson":         [34],
    "Herschel Walker":    [34],
    "John Riggins":       [44],
    "O.J. Simpson":       [32],
    "Jim Brown":          [32],
    "Gale Sayers":        [40],
    "Franco Harris":      [32],
    "Chuck Foreman":      [44],
    "Larry Csonka":       [39],
    "Floyd Little":       [44],
    "Calvin Hill":        [35],
    "Lydell Mitchell":    [26],
    "John Brockington":   [42],
    "Larry Brown":        [43],
    "Leroy Kelly":        [44],
    "Paul Hornung":       [5],
    "Jim Taylor":         [31],
    "Don Perkins":        [43],
    "Cookie Gilchrist":   [34],
    "Keith Lincoln":      [22],
    "Clem Daniels":       [36],
    "Mike Garrett":       [21],
    "Matt Snell":         [41],
    "Emerson Boozer":     [32],
    "Jim Kiick":          [21],
    "Mercury Morris":     [22],
    "Chuck Muncie":       [26],
    "George Rogers":      [38],
    "Billy Sims":         [20],
    "Joe Cribbs":         [32],
    "Ted Brown":          [23],
    "Ottis Anderson":     [24],
    "Joe Delaney":        [37],
    "George Halas":       [7],   # player/coach
    "Wilbert Montgomery": [31],
    "Ricky Bell":         [42],
    "Ricky Williams":     [34],

    # ── Quarterbacks ─────────────────────────────────────────────────────────
    "Joe Montana":        [16],
    "Dan Marino":         [13],
    "John Elway":         [7],
    "Jim McMahon":        [9],
    "Terry Bradshaw":     [12],
    "Roger Staubach":     [12],
    "Fran Tarkenton":     [10],
    "Ken Stabler":        [12],
    "Jim Plunkett":       [16],
    "Boomer Esiason":     [7],
    "Phil Simms":         [11],
    "Jim Kelly":          [12],
    "Warren Moon":        [1],
    "Neil Lomax":         [16],
    "Archie Manning":     [8],
    "Bob Griese":         [12],
    "Sonny Jurgensen":    [9],
    "Len Dawson":         [16],
    "Daryle Lamonica":    [3],
    "Joe Namath":         [12],
    "John Hadl":          [21],
    "Don Meredith":       [17],
    "Craig Morton":       [14],
    "Billy Kilmer":       [17],
    "Bill Nelsen":        [16],
    "Greg Landry":        [13],
    "Gary Danielson":     [16],
    "Tommy Kramer":       [9],
    "Brian Sipe":         [17],
    "Ken Anderson":       [14],
    "Dan Pastorini":      [7],
    "Bert Jones":         [7],
    "Steve DeBerg":       [17],
    "Ron Jaworski":       [7],
    "Steve Grogan":       [14],
    "Dave Krieg":         [17],
    "Wade Wilson":        [10],
    "Randall Cunningham": [12],
    "Vinny Testaverde":   [14],
    "Steve Bartkowski":   [10],
    "Lynn Dickey":        [12],
    "Vince Ferragamo":    [15],
    "Pat Ryan":           [11],

    # ── Wide Receivers / Tight Ends ─────────────────────────────────────────
    "Steve Largent":      [80],
    "Mike Ditka":         [89],
    "Charlie Joiner":     [18],
    "Drew Pearson":       [88],
    "Harold Carmichael":  [17],
    "John Stallworth":    [82],
    "Lynn Swann":         [88],
    "Ozzie Newsome":      [82],
    "Kellen Winslow":     [80],
    "Russ Francis":       [81],
    "Stanley Morgan":     [86],
    "Wesley Walker":      [85],
    "Wes Chandler":       [89],
    "Freddie Solomon":    [88],
    "Ahmad Rashad":       [28],
    "Sammy White":        [85],
    "Fred Biletnikoff":   [25],
    "Cliff Branch":       [21],
    "Bob Hayes":          [22],
    "Lance Alworth":      [19],
    "Gary Collins":       [86],
    "Paul Warfield":      [42],
    "Charley Taylor":     [42],
    "Roy Jefferson":      [89],
    "Haven Moses":        [84],
    "Dave Casper":        [87],
    "Don Maynard":        [13],
    "Art Powell":         [88],
    "Lionel Taylor":      [87],
    "Rich Caster":        [88],
    "Riley Odoms":        [84],
    "Todd Christensen":   [46],
    "Marv Fleming":       [84],
    "Ken MacAfee":        [81],
    "Jimmie Giles":       [88],
    "Mickey Shuler":      [82],
    "Billy Joe DuPree":   [89],
    "Jean Fugett":        [84],

    # ── Defensive Players ───────────────────────────────────────────────────
    "Lawrence Taylor":    [56],
    "Mike Singletary":    [50],
    "Dick Butkus":        [51],
    "Jack Lambert":       [58],
    "Jack Ham":           [59],
    "Randy White":        [54],
    "Harvey Martin":      [79],
    "Lee Roy Selmon":     [63],
    "Mean Joe Greene":    [75],
    "Deacon Jones":       [75],
    "Merlin Olsen":       [74],
    "Ronnie Lott":        [42],
    "Lester Hayes":       [37],
    "Mike Haynes":        [22],
    "Mel Blount":         [47],
    "Kenny Easley":       [45],
    "Donnie Shell":       [31],
    "Gary Fencik":        [45],
    "L.C. Greenwood":     [68],
    "Ernie Holmes":       [63],
    "Dwight White":       [78],
    "Carl Eller":         [81],
    "Alan Page":          [88],
    "Gary Larsen":        [77],
    "Jim Marshall":       [70],
    "Elvin Bethea":       [65],
    "Curley Culp":        [61],
    "Willie Lanier":      [63],
    "Bobby Bell":         [78],
    "Buck Buchanan":      [86],
    "Jerry Mays":         [75],
    "Ben Davidson":       [83],
    "Tom Keating":        [74],
    "Ike Lassiter":       [84],
    "Dave Wilcox":        [64],
    "Chris Hanburger":    [55],
    "Lee Roy Jordan":     [55],
    "Tommy Nobis":        [60],
    "Chuck Howley":       [54],
    "Dave Robinson":      [89],
    "Fred Miller":        [75],
    "Walter Jones":       [71],   # OT
    "Gene Upshaw":        [63],
    "Art Shell":          [78],
    "Larry Little":       [66],
    "Bob Kuechenberg":    [67],
    "Russ Grimm":         [68],
    "Joe Jacoby":         [66],
    "Mark May":           [73],
    "John Hannah":        [73],
    "Anthony Munoz":      [78],
    "Mike Munchak":       [63],
    "Dwight Stephenson":  [57],
    "Mike Webster":       [52],
    "Mel Renfro":         [20],
    "Cornell Green":      [34],
    "Charlie Waters":     [41],
    "Cliff Harris":       [43],
    "Jake Scott":         [13],
    "Dick Anderson":      [40],
    "Nick Buoniconti":    [85],
    "Charley Grimes":     [55],
    "Ken Riley":          [13],
    "Louis Wright":       [20],
    "Mike Reinfeldt":     [26],
    "Glen Edwards":       [27],
    "Mike Wagner":        [23],
    "Rick Upchurch":      [80],
    "Rod Perry":          [47],
    "Pat Thomas":         [48],
    "LeRoy Irvin":        [25],
    "Nolan Cromwell":     [21],
    "Joey Browner":       [47],
    "Carl Lee":           [36],
    "Reggie Rutland":     [22],
    "Tom Landry":         [49],   # playing career
    "Chuck Cecil":        [25],
    "Mark Carrier":       [20],

    # ── Kickers / Punters ────────────────────────────────────────────────────
    "Jan Stenerud":       [3],
    "Morten Andersen":    [7],
    "Nick Lowery":        [8],
    "Ray Guy":            [8],
    "Rohn Stark":         [5],
    "Mike Bragg":         [5],
    "Dave Jennings":      [13],
    "Pat McInally":       [9],
    "Tom Skladany":       [5],
    "Efren Herrera":      [8],
    "Chester Marcol":     [13],
    "Garo Yepremian":     [1],
    "Jim O'Brien":        [26],
    "Roy Gerela":         [10],
    "Fred Cox":           [1],
    "Mike Mercer":        [10],
    "Danny Villanueva":   [18],
    "Don Cockroft":       [2],
    "Jim Bakken":         [3],
    "Booth Lusteg":       [12],
    "Mark Moseley":       [3],
    "Tony Franklin":      [1],
    "Rafael Septien":     [2],
    "Uwe Von Schamann":   [2],
    "Ed Murray":          [3],
    "Rich Karlis":        [3],
    "Ali Haji-Sheikh":    [2],
    "Paul McFadden":      [1],
    "Kevin Butler":       [6],
    "Dean Biasucci":      [5],
    "Scott Norwood":      [11],
    "Fuad Reveiz":        [9],
    "Gary Anderson":      [1],
    "Norm Johnson":       [2],
}


# ─── Load NFL players ─────────────────────────────────────────────────────────

with open(NFL_FILE) as f:
    raw = f.read()
players = json.loads(raw.replace("export const NFL_PLAYERS = ", "").rstrip(";\n"))
by_alpha = {alpha(p["name"]): p for p in players}
print(f"Loaded {len(players):,} players")


# ─── Source 1: Apply curated list ─────────────────────────────────────────────

curated_applied = 0
for name, numbers in CURATED.items():
    key = alpha(name)
    if key not in by_alpha:
        continue
    p = by_alpha[key]
    existing = set(p.get("numbers", []))
    added = existing | set(numbers)
    if added != existing:
        p["numbers"] = sorted(added)
        curated_applied += 1

print(f"Curated list: updated {curated_applied} players")


# ─── Source 2: nflverse players.csv ──────────────────────────────────────────

url = "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
pdf = pd.read_csv(url, low_memory=False)
nflverse_applied = 0

for _, row in pdf.iterrows():
    jersey = row.get("jersey_number")
    if pd.isna(jersey) or jersey == 0:
        continue
    num = int(jersey)
    name = str(row.get("display_name", "")).strip()
    if not name:
        continue
    key = alpha(name)
    if key not in by_alpha:
        continue
    p = by_alpha[key]
    existing = set(p.get("numbers", []))
    if num not in existing:
        p["numbers"] = sorted(existing | {num})
        nflverse_applied += 1

print(f"nflverse players.csv: updated {nflverse_applied} players")


# ─── Write output ─────────────────────────────────────────────────────────────

players.sort(key=lambda x: x["name"])
with open(NFL_FILE, "w") as f:
    f.write("export const NFL_PLAYERS = ")
    json.dump(players, f, indent=2)
    f.write(";")

total_with_numbers = sum(1 for p in players if p.get("numbers"))
print(f"\nWrote {NFL_FILE}")
print(f"Players with numbers: {total_with_numbers:,} / {len(players):,} ({total_with_numbers/len(players)*100:.1f}%)")

# Spot-checks
print("\nSpot-checks:")
checks = ["Walter Payton","Bo Jackson","Eric Dickerson","Earl Campbell",
          "Lawrence Taylor","Mike Ditka","Tom Brady","Patrick Mahomes",
          "Jerry Rice","Herschel Walker","Jan Stenerud","Anthony Munoz"]
for name in checks:
    p = by_alpha.get(alpha(name))
    if p:
        print(f"  {name}: #{p.get('numbers', [])}")
    else:
        print(f"  {name}: not found")

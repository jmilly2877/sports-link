import { PLAYERS, TEAMS, COLLEGE_ALIASES } from "./database.js";
import { TEAM_POPULARITY, PLAYER_FAME } from "./scoring.js";

const norm = (s) => String(s).toLowerCase().trim();

function normalizeNumber(value) {
  return String(value).replace("#", "").replace(".0", "").trim();
}

function normCollegeName(value) {
  const originalKey = norm(value);

  if (COLLEGE_ALIASES[originalKey]) {
    return norm(COLLEGE_ALIASES[originalKey]);
  }

  const simplifiedKey = originalKey
    .replace(/^the university of /, "")
    .replace(/^university of /, "")
    .replace(/^college of /, "")
    .replace(/ university$/, "")
    .replace(/ college$/, "")
    .replace(/\./g, "")
    .trim();

  if (COLLEGE_ALIASES[simplifiedKey]) {
    return norm(COLLEGE_ALIASES[simplifiedKey]);
  }

  return simplifiedKey;
}
    function displayCollegeName(value) {
  const rawKey = norm(value);
  const normalizedKey = normCollegeName(value);

  if (COLLEGE_ALIASES[rawKey]) return COLLEGE_ALIASES[rawKey];
  if (COLLEGE_ALIASES[normalizedKey]) return COLLEGE_ALIASES[normalizedKey];

  return String(value).trim();
}

function getColleges(player) {
  if (!player.college) return [];

  const raw = Array.isArray(player.college)
    ? player.college
    : [player.college];

  return raw
    .flatMap((c) => String(c).split(";"))
    .flatMap((c) => String(c).split(" and "))
    .map((c) => c.trim())
    .filter(Boolean);
}

function getNumbers(player) {
  if (!player.numbers) return [];
  return player.numbers.map(normalizeNumber).filter(Boolean);
}

const teamAliasMap = new Map();
TEAMS.forEach((t) => {
  teamAliasMap.set(norm(t.name), t.name);
  t.aliases.forEach((a) => {
    if (a) teamAliasMap.set(norm(a), t.name);
  });
});

export const TEAM_ALIASES = {
  // NBA
  "76ers": "Philadelphia 76ers",
  "sixers": "Philadelphia 76ers",
  "bucks": "Milwaukee Bucks",
  "bulls": "Chicago Bulls",
  "cavaliers": "Cleveland Cavaliers",
  "cavs": "Cleveland Cavaliers",
  "celtics": "Boston Celtics",
  "clippers": "Los Angeles Clippers",
  "grizzlies": "Memphis Grizzlies",
  "hawks": "Atlanta Hawks",
  "heat": "Miami Heat",
  "hornets": "Charlotte Hornets",
  "jazz": "Utah Jazz",
  "kings": "Sacramento Kings",
  "knicks": "New York Knicks",
  "lakers": "Los Angeles Lakers",
  "magic": "Orlando Magic",
  "mavericks": "Dallas Mavericks",
  "mavs": "Dallas Mavericks",
  "nets": "Brooklyn Nets",
  "nuggets": "Denver Nuggets",
  "pacers": "Indiana Pacers",
  "pelicans": "New Orleans Pelicans",
  "pistons": "Detroit Pistons",
  "raptors": "Toronto Raptors",
  "rockets": "Houston Rockets",
  "spurs": "San Antonio Spurs",
  "suns": "Phoenix Suns",
  "thunder": "Oklahoma City Thunder",
  "timberwolves": "Minnesota Timberwolves",
  "wolves": "Minnesota Timberwolves",
  "trail blazers": "Portland Trail Blazers",
  "blazers": "Portland Trail Blazers",
  "warriors": "Golden State Warriors",

  // NFL
  "49ers": "San Francisco 49ers",
  "niners": "San Francisco 49ers",
  "bears": "Chicago Bears",
  "bengals": "Cincinnati Bengals",
  "bills": "Buffalo Bills",
  "broncos": "Denver Broncos",
  "browns": "Cleveland Browns",
  "buccaneers": "Tampa Bay Buccaneers",
  "bucs": "Tampa Bay Buccaneers",
  "cardinals": "Arizona Cardinals",
  "chargers": "Los Angeles Chargers",
  "chiefs": "Kansas City Chiefs",
  "colts": "Indianapolis Colts",
  "commanders": "Washington Commanders",
  "cowboys": "Dallas Cowboys",
  "dolphins": "Miami Dolphins",
  "eagles": "Philadelphia Eagles",
  "falcons": "Atlanta Falcons",
  "giants": "New York Giants",
  "jaguars": "Jacksonville Jaguars",
  "jags": "Jacksonville Jaguars",
  "jets": "New York Jets",
  "lions": "Detroit Lions",
  "packers": "Green Bay Packers",
  "panthers": "Carolina Panthers",
  "patriots": "New England Patriots",
  "pats": "New England Patriots",
  "raiders": "Las Vegas Raiders",
  "rams": "Los Angeles Rams",
  "ravens": "Baltimore Ravens",
  "saints": "New Orleans Saints",
  "seahawks": "Seattle Seahawks",
  "steelers": "Pittsburgh Steelers",
  "texans": "Houston Texans",
  "titans": "Tennessee Titans",
  "vikings": "Minnesota Vikings",

  // MLB
  "angels": "Los Angeles Angels",
  "astros": "Houston Astros",
  "athletics": "Oakland Athletics",
  "a's": "Oakland Athletics",
  "blue jays": "Toronto Blue Jays",
  "braves": "Atlanta Braves",
  "brewers": "Milwaukee Brewers",
  "cardinals": "St. Louis Cardinals",
  "cubs": "Chicago Cubs",
  "diamondbacks": "Arizona Diamondbacks",
  "dbacks": "Arizona Diamondbacks",
  "dodgers": "Los Angeles Dodgers",
  "giants": "San Francisco Giants",
  "guardians": "Cleveland Guardians",
  "indians": "Cleveland Guardians",
  "mariners": "Seattle Mariners",
  "marlins": "Miami Marlins",
  "mets": "New York Mets",
  "nationals": "Washington Nationals",
  "nats": "Washington Nationals",
  "orioles": "Baltimore Orioles",
  "o's": "Baltimore Orioles",
  "padres": "San Diego Padres",
  "phillies": "Philadelphia Phillies",
  "pirates": "Pittsburgh Pirates",
  "rangers": "Texas Rangers",
  "rays": "Tampa Bay Rays",
  "devil rays": "Tampa Bay Rays",
  "red sox": "Boston Red Sox",
  "reds": "Cincinnati Reds",
  "rockies": "Colorado Rockies",
  "royals": "Kansas City Royals",
  "tigers": "Detroit Tigers",
  "twins": "Minnesota Twins",
  "white sox": "Chicago White Sox",
  "yankees": "New York Yankees"
};

Object.entries(TEAM_ALIASES).forEach(([alias, team]) => {
  teamAliasMap.set(norm(alias), team);
});

const playerByFullName = new Map();
const playersByLastName = new Map();

PLAYERS.forEach((p) => {
  const key = norm(p.display_name || p.name);
playerByFullName.set(key, p);

if (p.display_name && p.display_name !== p.name) {
  playerByFullName.set(norm(p.name), null);
}

  const parts = p.name.split(" ");
  if (parts.length >= 2) {
    const last = norm(parts[parts.length - 1]);
    if (!playersByLastName.has(last)) playersByLastName.set(last, []);
    playersByLastName.get(last).push(p);
  }
});

const teamToPlayers = new Map();
PLAYERS.forEach((p) => {
  p.teams.forEach((t) => {
    const key = norm(t);
    if (!teamToPlayers.has(key)) teamToPlayers.set(key, []);
    teamToPlayers.get(key).push(p);
  });
});

const collegeToPlayers = new Map();
PLAYERS.forEach((p) => {
  getColleges(p).forEach((c) => {
    const key = norm(c);
    if (!collegeToPlayers.has(key)) collegeToPlayers.set(key, []);
    collegeToPlayers.get(key).push(p);
  });
});

const numberToPlayers = new Map();
PLAYERS.forEach((p) => {
  getNumbers(p).forEach((n) => {
    if (!numberToPlayers.has(n)) numberToPlayers.set(n, []);
    numberToPlayers.get(n).push(p);
  });
});

export function findTeam(input) {
  const key = norm(input);
  if (teamAliasMap.has(key)) return { name: teamAliasMap.get(key) };
  return null;
}

export function findPlayer(input) {
  const key = norm(input);

  if (playerByFullName.has(key)) {
  const match = playerByFullName.get(key);
  if (match) return match;
}

  const stripped = key.replace(/[.\-']/g, "");

  for (const [pKey, p] of playerByFullName) {
    if (pKey.replace(/[.\-']/g, "") === stripped) return p;
  }

  if (playersByLastName.has(key)) {
    const matches = playersByLastName.get(key);
    if (matches.length === 1) return matches[0];
  }

  const candidates = [];
  for (const [pKey, p] of playerByFullName) {
    if (pKey.includes(key) || key.includes(pKey)) candidates.push(p);
  }

  if (candidates.length === 1) return candidates[0];

  return null;
}

export function findCollege(input) {
  const key = norm(input);

  if (COLLEGE_ALIASES[key]) return COLLEGE_ALIASES[key];

  for (const p of PLAYERS) {
    for (const c of getColleges(p)) {
      if (norm(c) === key) return c;
    }
  }

  return null;
}

function isNumber(input) {
  return /^#?\d{1,2}(\.0)?$/.test(String(input).trim());
}

export function validateStartTeam(input) {
  const team = findTeam(input);

  if (team) {
    const players = teamToPlayers.get(norm(team.name));

    if (players && players.length > 0) {
      return { valid: true, corrected_name: team.name };
    }

    return {
      valid: false,
      explanation: `${team.name} is in the database but has no players yet.`
    };
  }

  return {
    valid: false,
    explanation: "Not recognized as an NFL, NBA, or MLB team."
  };
}

export function validateChainLink(currentItem, currentType, answer) {
  const input = answer.trim();

  if (currentType === "team") {
    const player = findPlayer(input);

    if (!player) {
      return {
        valid: false,
        explanation: `"${input}" — player not found in the database.`
      };
    }

    const resolvedCurrent = teamAliasMap.get(norm(currentItem)) || currentItem;

    const played = player.teams.some(
      (t) => t === resolvedCurrent || teamAliasMap.get(norm(t)) === resolvedCurrent
    );

    if (played) {
      return { valid: true, type: "player", corrected_name: player.display_name || player.name };
    }

    return {
      valid: false,
      explanation: `${player.name} didn't play for the ${currentItem}.`
    };
  }

  if (currentType === "player") {
    const currentPlayer = findPlayer(currentItem);

    if (!currentPlayer) {
      return { valid: false, explanation: "Current player not found." };
    }

    if (isNumber(input)) {
      const guessedNumber = normalizeNumber(input);
      const validNumbers = getNumbers(currentPlayer);

      if (validNumbers.includes(guessedNumber)) {
        return {
          valid: true,
          type: "number",
          corrected_name: guessedNumber
        };
      }

      const known = validNumbers.length
        ? validNumbers.map((n) => `#${n}`).join(", ")
        : "no known numbers in database";

      return {
        valid: false,
        explanation: `${currentPlayer.name} wore ${known}, not #${guessedNumber}.`
      };
    }

    const playerColleges = getColleges(currentPlayer);

    for (const c of playerColleges) {
      if (normCollegeName(c) === normCollegeName(input)) {
        return { valid: true, type: "college", corrected_name: c };
      }
    }

    const resolvedCollege = findCollege(input);

    if (resolvedCollege) {
      const matchesPlayer = playerColleges.some(
        (c) => normCollegeName(c) === normCollegeName(resolvedCollege)
      );

      if (matchesPlayer) {
        return {
          valid: true,
          type: "college",
          corrected_name: resolvedCollege
        };
      }
    }

    const team = findTeam(input);

    if (team) {
      const playedFor = currentPlayer.teams.some((t) => t === team.name);

      if (playedFor) {
        return { valid: true, type: "team", corrected_name: team.name };
      }

      return {
        valid: false,
        explanation: `${currentPlayer.name} didn't play for the ${team.name}.`
      };
    }

    if (resolvedCollege) {
      const collegeList = playerColleges.length > 0
        ? playerColleges.join(" and ")
        : "no college listed in the database";

      return {
        valid: false,
        explanation: `${currentPlayer.name} went to ${collegeList}, not ${resolvedCollege}.`
      };
    }

    if (playerColleges.length > 0) {
      for (const c of playerColleges) {
        if (norm(c).includes(norm(input)) || norm(input).includes(norm(c))) {
          return { valid: true, type: "college", corrected_name: c };
        }
      }
    }

    return {
      valid: false,
      explanation: `"${input}" — not recognized as a team, number, or college for ${currentPlayer.name}.`
    };
  }

  if (currentType === "college") {
    const player = findPlayer(input);

    if (!player) {
      return {
        valid: false,
        explanation: `"${input}" — player not found in the database.`
      };
    }

    const collegeName = findCollege(currentItem) || currentItem;

    const attended = getColleges(player).some(
      (c) => normCollegeName(c) === normCollegeName(collegeName)
    );

    if (attended) {
      return { valid: true, type: "player", corrected_name: player.display_name || player.name };
    }

    const pc = getColleges(player);

    if (pc.length > 0) {
      return {
        valid: false,
        explanation: `${player.name} went to ${pc.join(" and ")}, not ${collegeName}.`
      };
    }

    return {
      valid: false,
      explanation: `${player.name} didn't attend college, or it is not in our database.`
    };
  }

  if (currentType === "number") {
    const player = findPlayer(input);

    if (!player) {
      return {
        valid: false,
        explanation: `"${input}" — player not found in the database.`
      };
    }

    const guessedNumber = normalizeNumber(currentItem);
    const validNumbers = getNumbers(player);

    if (validNumbers.includes(guessedNumber)) {
      return { valid: true, type: "player", corrected_name: player.display_name || player.name };
    }

    const known = validNumbers.length
      ? validNumbers.map((n) => `#${n}`).join(", ")
      : "no known numbers in database";

    return {
      valid: false,
      explanation: `${player.name} wore ${known}, not #${guessedNumber}.`
    };
  }

  return { valid: false, explanation: "Something went wrong." };
}

export function getStats() {
  const colleges = new Set();
  PLAYERS.forEach((p) => getColleges(p).forEach((c) => colleges.add(c)));

  const numbers = new Set();
  PLAYERS.forEach((p) => getNumbers(p).forEach((n) => numbers.add(n)));

  return {
    players: PLAYERS.length,
    teams: 92,
    colleges: colleges.size,
    numbers: numbers.size
  };
}

const DAILY_TEAMS = TEAMS.filter((t) => {
  const players = teamToPlayers.get(norm(t.name));
  return players && players.length >= 5;
}).map((t) => t.name);

export function getDailyTeam() {
  const today = new Date();
  const dateStr = `${today.getFullYear()}-${today.getMonth()}-${today.getDate()}`;

  let hash = 0;

  for (let i = 0; i < dateStr.length; i++) {
    hash = ((hash << 5) - hash) + dateStr.charCodeAt(i);
    hash |= 0;
  }

  return DAILY_TEAMS[Math.abs(hash) % DAILY_TEAMS.length];
}

function getTeamPop(teamName) {
  return TEAM_POPULARITY[teamName] || 3;
}

function getPlayerFame(playerName) {
  return PLAYER_FAME[playerName] || 3;
}

export function getRarityScore(fromItem, fromType, toName, toType) {
  let points = 10;

  if (fromType === "team" && toType === "player") {
    const fame = getPlayerFame(toName);
    const pop = getTeamPop(fromItem);
    points = fame * pop * 4;
  }

  else if (fromType === "player" && toType === "team") {
    const pop = getTeamPop(toName);
    points = pop * 8;
  }

  else if (fromType === "player" && toType === "college") {
    const collegePlayers = collegeToPlayers.get(norm(toName));
    const count = collegePlayers ? collegePlayers.length : 1;
    points = Math.round(100 / count);
    points = Math.round(points * 1.3);
  }

  else if (fromType === "player" && toType === "number") {
    const numPlayers = numberToPlayers.get(normalizeNumber(toName));
    const count = numPlayers ? numPlayers.length : 1;
    points = Math.round(100 / count);
    points = Math.round(points * 1.5);
  }

  else if (fromType === "college" && toType === "player") {
    const fame = getPlayerFame(toName);
    const collegePlayers = collegeToPlayers.get(norm(fromItem));
    const count = collegePlayers ? collegePlayers.length : 1;
    const collegeRarity = Math.round(50 / count);
    points = fame * 3 + collegeRarity;
  }

  else if (fromType === "number" && toType === "player") {
    const fame = getPlayerFame(toName);
    const numPlayers = numberToPlayers.get(normalizeNumber(fromItem));
    const count = numPlayers ? numPlayers.length : 1;
    const numRarity = Math.round(50 / count);
    points = fame * 3 + numRarity;
  }

  return Math.max(1, Math.min(100, points));
}
const duplicateDisplayNames = new Set(
  PLAYERS
    .filter((p) => p.display_name && p.display_name !== p.name)
    .map((p) => norm(p.name))
);

export function getSuggestionOptions(type) {
  if (type === "player") {
    return [...new Set(
      PLAYERS
        .map((p) => {
          if (p.display_name && p.display_name !== p.name) {
            return p.display_name.trim();
          }

          if (duplicateDisplayNames.has(norm(p.name))) {
            return null;
          }

          return p.name?.trim();
        })
        .filter(Boolean)
    )].sort();
  }

if (type === "college") {
  const colleges = new Set();

  PLAYERS.forEach((p) => {
    getColleges(p).forEach((c) => {
      const display = displayCollegeName(c);

      if (display) {
        colleges.add(display);
      }
    });
  });

  Object.values(COLLEGE_ALIASES).forEach((canonical) => {
    if (canonical) {
      colleges.add(canonical);
    }
  });

  Object.keys(COLLEGE_ALIASES).forEach((alias) => {
    const canonical = COLLEGE_ALIASES[alias];

    if (canonical) {
      colleges.add(canonical);
    }
  });

  return Array.from(colleges).sort();
}
}
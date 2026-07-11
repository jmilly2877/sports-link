import { PLAYERS, TEAMS } from "./database.js";

const norm = (s) => String(s).toLowerCase().trim();

function getColleges(player) {
  if (!player.college) return [];
  if (Array.isArray(player.college)) return player.college;
  return [player.college];
}

function getNumbers(player) {
  if (!player.numbers) return [];
  return player.numbers.map((n) => String(n).replace("#", "").replace(".0", "").trim());
}

function nodeKey(type, name) {
  return `${type}:${norm(name)}`;
}

function makeNode(type, name) {
  return {
    type,
    name,
    key: nodeKey(type, name),
  };
}

export function buildSportsGraph() {
  const graph = new Map();

  function addNode(node) {
    if (!graph.has(node.key)) {
      graph.set(node.key, {
        ...node,
        neighbors: [],
      });
    }
  }

  function addEdge(a, b) {
    addNode(a);
    addNode(b);

    graph.get(a.key).neighbors.push(b.key);
    graph.get(b.key).neighbors.push(a.key);
  }

  for (const team of TEAMS) {
    addNode(makeNode("team", team.name));
  }

  for (const player of PLAYERS) {
    const playerNode = makeNode("player", player.name);

    for (const team of player.teams || []) {
      addEdge(playerNode, makeNode("team", team));
    }

    for (const college of getColleges(player)) {
      addEdge(playerNode, makeNode("college", college));
    }

    for (const number of getNumbers(player)) {
      addEdge(playerNode, makeNode("number", number));
    }
  }

  return graph;
}

export function findShortestPath(startType, startName, goalType, goalName, maxDepth = 10) {
  const graph = buildSportsGraph();

  const startKey = nodeKey(startType, startName);
  const goalKey = nodeKey(goalType, goalName);

  if (!graph.has(startKey) || !graph.has(goalKey)) {
    return null;
  }

  const queue = [[startKey]];
  const visited = new Set([startKey]);

  while (queue.length > 0) {
    const path = queue.shift();
    const currentKey = path[path.length - 1];

    if (currentKey === goalKey) {
      return path.map((key) => {
        const node = graph.get(key);
        return {
          type: node.type,
          name: node.name,
        };
      });
    }

    if (path.length > maxDepth + 1) continue;

    const current = graph.get(currentKey);

    for (const nextKey of current.neighbors) {
      if (!visited.has(nextKey)) {
        visited.add(nextKey);
        queue.push([...path, nextKey]);
      }
    }
  }

  return null;
}

export function getDailyLinkChallenge() {
  // Epoch: Feb 1, 2026 UTC.
  const EPOCH_MS = Date.UTC(2026, 1, 1);
  const now = new Date();
  const todayUTC = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  const dayIndex = Math.floor((todayUTC - EPOCH_MS) / 86400000);

  // 70% NFL↔MLB, 30% NBA (popular teams/players only).
  // Pattern per 10-entry group: NFL→MLB, MLB→NFL, NFL→MLB, MLB→NFL, NFL→MLB, MLB→NFL, NFL→MLB, NBA, NBA, NBA
  const candidates = [
    // ── group 1 ──
    { startType: "team", startName: "Kansas City Chiefs",      goalType: "player", goalName: "Aaron Judge"         }, // NFL→MLB
    { startType: "team", startName: "New York Yankees",        goalType: "player", goalName: "Patrick Mahomes"     }, // MLB→NFL
    { startType: "team", startName: "Dallas Cowboys",          goalType: "player", goalName: "Shohei Ohtani"       }, // NFL→MLB
    { startType: "team", startName: "Los Angeles Dodgers",     goalType: "player", goalName: "Josh Allen"          }, // MLB→NFL
    { startType: "team", startName: "New England Patriots",    goalType: "player", goalName: "Paul Skenes"         }, // NFL→MLB
    { startType: "team", startName: "Boston Red Sox",          goalType: "player", goalName: "Joe Burrow"          }, // MLB→NFL
    { startType: "team", startName: "Green Bay Packers",       goalType: "player", goalName: "Bryce Harper"        }, // NFL→MLB
    { startType: "team", startName: "Los Angeles Lakers",      goalType: "player", goalName: "Patrick Mahomes"     }, // NBA→NFL
    { startType: "team", startName: "Kansas City Chiefs",      goalType: "player", goalName: "LeBron James"        }, // NFL→NBA
    { startType: "team", startName: "New York Yankees",        goalType: "player", goalName: "LeBron James"        }, // MLB→NBA

    // ── group 2 ──
    { startType: "team", startName: "Pittsburgh Steelers",     goalType: "player", goalName: "Mike Trout"          }, // NFL→MLB
    { startType: "team", startName: "Chicago Cubs",            goalType: "player", goalName: "Dak Prescott"        }, // MLB→NFL
    { startType: "team", startName: "San Francisco 49ers",     goalType: "player", goalName: "Freddie Freeman"     }, // NFL→MLB
    { startType: "team", startName: "Houston Astros",          goalType: "player", goalName: "CJ Stroud"           }, // MLB→NFL
    { startType: "team", startName: "Philadelphia Eagles",     goalType: "player", goalName: "Gerrit Cole"         }, // NFL→MLB
    { startType: "team", startName: "Atlanta Braves",          goalType: "player", goalName: "Justin Jefferson"    }, // MLB→NFL
    { startType: "team", startName: "Buffalo Bills",           goalType: "player", goalName: "Juan Soto"           }, // NFL→MLB
    { startType: "team", startName: "Boston Celtics",          goalType: "player", goalName: "Josh Allen"          }, // NBA→NFL
    { startType: "team", startName: "Dallas Cowboys",          goalType: "player", goalName: "Steph Curry"         }, // NFL→NBA
    { startType: "team", startName: "Los Angeles Dodgers",     goalType: "player", goalName: "Steph Curry"         }, // MLB→NBA

    // ── group 3 ──
    { startType: "team", startName: "Baltimore Ravens",        goalType: "player", goalName: "Corey Seager"        }, // NFL→MLB
    { startType: "team", startName: "San Francisco Giants",    goalType: "player", goalName: "Lamar Jackson"       }, // MLB→NFL
    { startType: "team", startName: "Los Angeles Rams",        goalType: "player", goalName: "Clayton Kershaw"     }, // NFL→MLB
    { startType: "team", startName: "St. Louis Cardinals",     goalType: "player", goalName: "Jalen Hurts"         }, // MLB→NFL
    { startType: "team", startName: "Seattle Seahawks",        goalType: "player", goalName: "Julio Rodriguez"     }, // NFL→MLB
    { startType: "team", startName: "San Diego Padres",        goalType: "player", goalName: "Trevor Lawrence"     }, // MLB→NFL
    { startType: "team", startName: "Miami Dolphins",          goalType: "player", goalName: "Ronald Acuna Jr"     }, // NFL→MLB
    { startType: "team", startName: "Golden State Warriors",   goalType: "player", goalName: "Joe Burrow"          }, // NBA→NFL
    { startType: "team", startName: "New England Patriots",    goalType: "player", goalName: "Kevin Durant"        }, // NFL→NBA
    { startType: "team", startName: "Boston Red Sox",          goalType: "player", goalName: "Kevin Durant"        }, // MLB→NBA

    // ── group 4 ──
    { startType: "team", startName: "New York Giants",         goalType: "player", goalName: "Pete Alonso"         }, // NFL→MLB
    { startType: "team", startName: "Toronto Blue Jays",       goalType: "player", goalName: "Aaron Rodgers"       }, // MLB→NFL
    { startType: "team", startName: "New Orleans Saints",      goalType: "player", goalName: "Yordan Alvarez"      }, // NFL→MLB
    { startType: "team", startName: "Pittsburgh Pirates",      goalType: "player", goalName: "Ja'Marr Chase"       }, // MLB→NFL
    { startType: "team", startName: "Carolina Panthers",       goalType: "player", goalName: "Spencer Strider"     }, // NFL→MLB
    { startType: "team", startName: "Tampa Bay Rays",          goalType: "player", goalName: "Jayden Daniels"      }, // MLB→NFL
    { startType: "team", startName: "Atlanta Falcons",         goalType: "player", goalName: "Max Scherzer"        }, // NFL→MLB
    { startType: "team", startName: "Chicago Bulls",           goalType: "player", goalName: "Dak Prescott"        }, // NBA→NFL
    { startType: "team", startName: "Philadelphia Eagles",     goalType: "player", goalName: "Giannis Antetokounmpo"}, // NFL→NBA
    { startType: "team", startName: "Chicago Cubs",            goalType: "player", goalName: "Giannis Antetokounmpo"}, // MLB→NBA

    // ── group 5 ──
    { startType: "team", startName: "Arizona Cardinals",       goalType: "player", goalName: "Nolan Arenado"       }, // NFL→MLB
    { startType: "team", startName: "Minnesota Twins",         goalType: "player", goalName: "Justin Herbert"      }, // MLB→NFL
    { startType: "team", startName: "Las Vegas Raiders",       goalType: "player", goalName: "Mookie Betts"        }, // NFL→MLB
    { startType: "team", startName: "Seattle Mariners",        goalType: "player", goalName: "Drake Maye"          }, // MLB→NFL
    { startType: "team", startName: "Los Angeles Chargers",    goalType: "player", goalName: "Vladimir Guerrero Jr"}, // NFL→MLB
    { startType: "team", startName: "Colorado Rockies",        goalType: "player", goalName: "Tua Tagovailoa"      }, // MLB→NFL
    { startType: "team", startName: "Tampa Bay Buccaneers",    goalType: "player", goalName: "Jose Altuve"         }, // NFL→MLB
    { startType: "team", startName: "Miami Heat",              goalType: "player", goalName: "Lamar Jackson"       }, // NBA→NFL
    { startType: "team", startName: "Buffalo Bills",           goalType: "player", goalName: "Jayson Tatum"        }, // NFL→NBA
    { startType: "team", startName: "Houston Astros",          goalType: "player", goalName: "Jayson Tatum"        }, // MLB→NBA

    // ── group 6 ──
    { startType: "team", startName: "Denver Broncos",          goalType: "player", goalName: "Aaron Judge"         }, // NFL→MLB
    { startType: "team", startName: "Miami Marlins",           goalType: "player", goalName: "Baker Mayfield"      }, // MLB→NFL
    { startType: "team", startName: "Minnesota Vikings",       goalType: "player", goalName: "Shohei Ohtani"       }, // NFL→MLB
    { startType: "team", startName: "Philadelphia Phillies",   goalType: "player", goalName: "Kirk Cousins"        }, // MLB→NFL
    { startType: "team", startName: "Chicago Bears",           goalType: "player", goalName: "Gerrit Cole"         }, // NFL→MLB
    { startType: "team", startName: "Texas Rangers",           goalType: "player", goalName: "Matthew Stafford"    }, // MLB→NFL
    { startType: "team", startName: "Detroit Lions",           goalType: "player", goalName: "Bryce Harper"        }, // NFL→MLB
    { startType: "team", startName: "New York Knicks",         goalType: "player", goalName: "CJ Stroud"           }, // NBA→NFL
    { startType: "team", startName: "San Francisco 49ers",     goalType: "player", goalName: "Nikola Jokic"        }, // NFL→NBA
    { startType: "team", startName: "Atlanta Braves",          goalType: "player", goalName: "Nikola Jokic"        }, // MLB→NBA

    // ── group 7 ──
    { startType: "team", startName: "Jacksonville Jaguars",    goalType: "player", goalName: "Mike Trout"          }, // NFL→MLB
    { startType: "team", startName: "Arizona Diamondbacks",    goalType: "player", goalName: "Brock Purdy"         }, // MLB→NFL
    { startType: "team", startName: "Indianapolis Colts",      goalType: "player", goalName: "Juan Soto"           }, // NFL→MLB
    { startType: "team", startName: "Washington Nationals",    goalType: "player", goalName: "Cam Newton"          }, // MLB→NFL
    { startType: "team", startName: "Houston Texans",          goalType: "player", goalName: "Freddie Freeman"     }, // NFL→MLB
    { startType: "team", startName: "New York Mets",           goalType: "player", goalName: "Patrick Mahomes"     }, // MLB→NFL
    { startType: "team", startName: "Tennessee Titans",        goalType: "player", goalName: "Clayton Kershaw"     }, // NFL→MLB
    { startType: "team", startName: "Milwaukee Bucks",         goalType: "player", goalName: "Trevor Lawrence"     }, // NBA→NFL
    { startType: "team", startName: "Los Angeles Rams",        goalType: "player", goalName: "LeBron James"        }, // NFL→NBA
    { startType: "team", startName: "Los Angeles Dodgers",     goalType: "player", goalName: "LeBron James"        }, // MLB→NBA

    // ── group 8 ──
    { startType: "team", startName: "Cincinnati Bengals",      goalType: "player", goalName: "Max Scherzer"        }, // NFL→MLB
    { startType: "team", startName: "Baltimore Orioles",       goalType: "player", goalName: "Josh Allen"          }, // MLB→NFL
    { startType: "team", startName: "New York Jets",           goalType: "player", goalName: "Mookie Betts"        }, // NFL→MLB
    { startType: "team", startName: "Cincinnati Reds",         goalType: "player", goalName: "Joe Burrow"          }, // MLB→NFL
    { startType: "team", startName: "Washington Commanders",   goalType: "player", goalName: "Paul Skenes"         }, // NFL→MLB
    { startType: "team", startName: "Cleveland Guardians",     goalType: "player", goalName: "Dak Prescott"        }, // MLB→NFL
    { startType: "team", startName: "Cleveland Browns",        goalType: "player", goalName: "Nolan Arenado"       }, // NFL→MLB
    { startType: "team", startName: "Los Angeles Lakers",      goalType: "player", goalName: "Aaron Rodgers"       }, // NBA→NFL
    { startType: "team", startName: "Green Bay Packers",       goalType: "player", goalName: "LeBron James"        }, // NFL→NBA
    { startType: "team", startName: "San Francisco Giants",    goalType: "player", goalName: "Kevin Durant"        }, // MLB→NBA

    // ── group 9 ──
    { startType: "team", startName: "Kansas City Chiefs",      goalType: "player", goalName: "Ronald Acuna Jr"     }, // NFL→MLB
    { startType: "team", startName: "Detroit Tigers",          goalType: "player", goalName: "Lamar Jackson"       }, // MLB→NFL
    { startType: "team", startName: "Dallas Cowboys",          goalType: "player", goalName: "Corey Seager"        }, // NFL→MLB
    { startType: "team", startName: "Chicago White Sox",       goalType: "player", goalName: "Justin Jefferson"    }, // MLB→NFL
    { startType: "team", startName: "Philadelphia Eagles",     goalType: "player", goalName: "Yordan Alvarez"      }, // NFL→MLB
    { startType: "team", startName: "Oakland Athletics",       goalType: "player", goalName: "Aaron Rodgers"       }, // MLB→NFL
    { startType: "team", startName: "Green Bay Packers",       goalType: "player", goalName: "Spencer Strider"     }, // NFL→MLB
    { startType: "team", startName: "Boston Celtics",          goalType: "player", goalName: "Jalen Hurts"         }, // NBA→NFL
    { startType: "team", startName: "Pittsburgh Steelers",     goalType: "player", goalName: "Steph Curry"         }, // NFL→NBA
    { startType: "team", startName: "St. Louis Cardinals",     goalType: "player", goalName: "LeBron James"        }, // MLB→NBA

    // ── group 10 ──
    { startType: "team", startName: "Pittsburgh Steelers",     goalType: "player", goalName: "Vladimir Guerrero Jr"}, // NFL→MLB
    { startType: "team", startName: "Kansas City Royals",      goalType: "player", goalName: "CJ Stroud"           }, // MLB→NFL
    { startType: "team", startName: "Buffalo Bills",           goalType: "player", goalName: "Jose Altuve"         }, // NFL→MLB
    { startType: "team", startName: "Milwaukee Brewers",       goalType: "player", goalName: "Jalen Hurts"         }, // MLB→NFL
    { startType: "team", startName: "Baltimore Ravens",        goalType: "player", goalName: "Pete Alonso"         }, // NFL→MLB
    { startType: "team", startName: "Toronto Blue Jays",       goalType: "player", goalName: "Baker Mayfield"      }, // MLB→NFL
    { startType: "team", startName: "San Francisco 49ers",     goalType: "player", goalName: "Julio Rodriguez"     }, // NFL→MLB
    { startType: "team", startName: "Golden State Warriors",   goalType: "player", goalName: "Aaron Judge"         }, // NBA→MLB
    { startType: "team", startName: "Baltimore Ravens",        goalType: "player", goalName: "Giannis Antetokounmpo"}, // NFL→NBA
    { startType: "team", startName: "New York Mets",           goalType: "player", goalName: "Jayson Tatum"        }, // MLB→NBA

    // ── group 11 ──
    { startType: "team", startName: "Los Angeles Rams",        goalType: "player", goalName: "Bryce Harper"        }, // NFL→MLB
    { startType: "team", startName: "New York Yankees",        goalType: "player", goalName: "Trevor Lawrence"     }, // MLB→NFL
    { startType: "team", startName: "New England Patriots",    goalType: "player", goalName: "Max Scherzer"        }, // NFL→MLB
    { startType: "team", startName: "Los Angeles Dodgers",     goalType: "player", goalName: "Brock Purdy"         }, // MLB→NFL
    { startType: "team", startName: "Denver Broncos",          goalType: "player", goalName: "Freddie Freeman"     }, // NFL→MLB
    { startType: "team", startName: "Boston Red Sox",          goalType: "player", goalName: "Ja'Marr Chase"       }, // MLB→NFL
    { startType: "team", startName: "Minnesota Vikings",       goalType: "player", goalName: "Pete Alonso"         }, // NFL→MLB
    { startType: "team", startName: "Miami Heat",              goalType: "player", goalName: "Mike Trout"          }, // NBA→MLB
    { startType: "team", startName: "New York Knicks",         goalType: "player", goalName: "Mookie Betts"        }, // NBA→MLB
    { startType: "team", startName: "Chicago Bulls",           goalType: "player", goalName: "Shohei Ohtani"       }, // NBA→MLB

    // ── group 12 ──
    { startType: "team", startName: "Chicago Bears",           goalType: "player", goalName: "Nolan Arenado"       }, // NFL→MLB
    { startType: "team", startName: "Chicago Cubs",            goalType: "player", goalName: "Tua Tagovailoa"      }, // MLB→NFL
    { startType: "team", startName: "Detroit Lions",           goalType: "player", goalName: "Jose Altuve"         }, // NFL→MLB
    { startType: "team", startName: "Houston Astros",          goalType: "player", goalName: "Sam Darnold"         }, // MLB→NFL
    { startType: "team", startName: "Jacksonville Jaguars",    goalType: "player", goalName: "Yordan Alvarez"      }, // NFL→MLB
    { startType: "team", startName: "Atlanta Braves",          goalType: "player", goalName: "Matthew Stafford"    }, // MLB→NFL
    { startType: "team", startName: "Indianapolis Colts",      goalType: "player", goalName: "Ronald Acuna Jr"     }, // NFL→MLB
    { startType: "team", startName: "Milwaukee Bucks",         goalType: "player", goalName: "Juan Soto"           }, // NBA→MLB
    { startType: "team", startName: "Los Angeles Lakers",      goalType: "player", goalName: "Freddie Freeman"     }, // NBA→MLB
    { startType: "team", startName: "Kansas City Royals",      goalType: "player", goalName: "Nikola Jokic"        }, // MLB→NBA
  ];

  const challenge = candidates[((dayIndex % candidates.length) + candidates.length) % candidates.length];
  const optimalPath = findShortestPath(
    challenge.startType,
    challenge.startName,
    challenge.goalType,
    challenge.goalName,
    10
  );

  return {
    ...challenge,
    optimalPath,
    par: optimalPath ? Math.max(4, optimalPath.length - 1) : 6,
  };
}

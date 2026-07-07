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
  // Epoch: Feb 1, 2026 UTC. Each index is used exactly once — no day ever repeats.
  // Today (Jun 1, 2026) = index 120.
  const EPOCH_MS = Date.UTC(2026, 1, 1); // Feb 1, 2026 UTC
  const now = new Date();
  const todayUTC = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  const dayIndex = Math.floor((todayUTC - EPOCH_MS) / 86400000);

  const candidates = [
    // ── index 0–19: NBA team → NFL player ──
    { startType: "team", startName: "Golden State Warriors",   goalType: "player", goalName: "Patrick Mahomes"    },
    { startType: "team", startName: "Los Angeles Lakers",      goalType: "player", goalName: "Joe Burrow"         },
    { startType: "team", startName: "Boston Celtics",          goalType: "player", goalName: "Josh Allen"         },
    { startType: "team", startName: "Chicago Bulls",           goalType: "player", goalName: "Dak Prescott"       },
    { startType: "team", startName: "Miami Heat",              goalType: "player", goalName: "Jalen Hurts"        },
    { startType: "team", startName: "Brooklyn Nets",           goalType: "player", goalName: "Justin Jefferson"   },
    { startType: "team", startName: "Denver Nuggets",          goalType: "player", goalName: "Lamar Jackson"      },
    { startType: "team", startName: "Milwaukee Bucks",         goalType: "player", goalName: "Ja'Marr Chase"      },
    { startType: "team", startName: "Phoenix Suns",            goalType: "player", goalName: "Aaron Rodgers"      },
    { startType: "team", startName: "Dallas Mavericks",        goalType: "player", goalName: "CJ Stroud"          },
    { startType: "team", startName: "Philadelphia 76ers",      goalType: "player", goalName: "Trevor Lawrence"    },
    { startType: "team", startName: "Cleveland Cavaliers",     goalType: "player", goalName: "Justin Herbert"     },
    { startType: "team", startName: "Atlanta Hawks",           goalType: "player", goalName: "Jayden Daniels"     },
    { startType: "team", startName: "Toronto Raptors",         goalType: "player", goalName: "Drake Maye"         },
    { startType: "team", startName: "Minnesota Timberwolves",  goalType: "player", goalName: "Sam Darnold"        },
    { startType: "team", startName: "Oklahoma City Thunder",   goalType: "player", goalName: "Matthew Stafford"   },
    { startType: "team", startName: "Memphis Grizzlies",       goalType: "player", goalName: "Brock Purdy"        },
    { startType: "team", startName: "Indiana Pacers",          goalType: "player", goalName: "Tua Tagovailoa"     },
    { startType: "team", startName: "New Orleans Pelicans",    goalType: "player", goalName: "Baker Mayfield"     },
    { startType: "team", startName: "Sacramento Kings",        goalType: "player", goalName: "Kirk Cousins"       },

    // ── index 20–39: NBA team → MLB player ──
    { startType: "team", startName: "Golden State Warriors",   goalType: "player", goalName: "Aaron Judge"        },
    { startType: "team", startName: "Los Angeles Lakers",      goalType: "player", goalName: "Shohei Ohtani"      },
    { startType: "team", startName: "Boston Celtics",          goalType: "player", goalName: "Paul Skenes"        },
    { startType: "team", startName: "Miami Heat",              goalType: "player", goalName: "Bryce Harper"       },
    { startType: "team", startName: "Chicago Bulls",           goalType: "player", goalName: "Gerrit Cole"        },
    { startType: "team", startName: "San Antonio Spurs",       goalType: "player", goalName: "Mike Trout"         },
    { startType: "team", startName: "Milwaukee Bucks",         goalType: "player", goalName: "Corey Seager"       },
    { startType: "team", startName: "Dallas Mavericks",        goalType: "player", goalName: "Freddie Freeman"    },
    { startType: "team", startName: "Denver Nuggets",          goalType: "player", goalName: "Mookie Betts"       },
    { startType: "team", startName: "Brooklyn Nets",           goalType: "player", goalName: "Juan Soto"          },
    { startType: "team", startName: "Phoenix Suns",            goalType: "player", goalName: "Clayton Kershaw"    },
    { startType: "team", startName: "Oklahoma City Thunder",   goalType: "player", goalName: "Max Scherzer"       },
    { startType: "team", startName: "Portland Trail Blazers",  goalType: "player", goalName: "Nolan Arenado"      },
    { startType: "team", startName: "Houston Rockets",         goalType: "player", goalName: "Jose Altuve"        },
    { startType: "team", startName: "Memphis Grizzlies",       goalType: "player", goalName: "Pete Alonso"        },
    { startType: "team", startName: "New Orleans Pelicans",    goalType: "player", goalName: "Ronald Acuna Jr"    },
    { startType: "team", startName: "Charlotte Hornets",       goalType: "player", goalName: "Spencer Strider"    },
    { startType: "team", startName: "Utah Jazz",               goalType: "player", goalName: "Julio Rodriguez"    },
    { startType: "team", startName: "Indiana Pacers",          goalType: "player", goalName: "Yordan Alvarez"     },
    { startType: "team", startName: "Cleveland Cavaliers",     goalType: "player", goalName: "Vladimir Guerrero Jr"},

    // ── index 40–59: NFL team → NBA player ──
    { startType: "team", startName: "Kansas City Chiefs",      goalType: "player", goalName: "LeBron James"       },
    { startType: "team", startName: "Dallas Cowboys",          goalType: "player", goalName: "Steph Curry"        },
    { startType: "team", startName: "New England Patriots",    goalType: "player", goalName: "Kevin Durant"       },
    { startType: "team", startName: "Green Bay Packers",       goalType: "player", goalName: "Jaylen Brown"       },
    { startType: "team", startName: "Pittsburgh Steelers",     goalType: "player", goalName: "Giannis Antetokounmpo"},
    { startType: "team", startName: "San Francisco 49ers",     goalType: "player", goalName: "Nikola Jokic"       },
    { startType: "team", startName: "Philadelphia Eagles",     goalType: "player", goalName: "Trae Young"         },
    { startType: "team", startName: "Buffalo Bills",           goalType: "player", goalName: "Jayson Tatum"       },
    { startType: "team", startName: "Baltimore Ravens",        goalType: "player", goalName: "Joel Embiid"        },
    { startType: "team", startName: "Cincinnati Bengals",      goalType: "player", goalName: "Zion Williamson"    },
    { startType: "team", startName: "Los Angeles Rams",        goalType: "player", goalName: "Anthony Davis"      },
    { startType: "team", startName: "Seattle Seahawks",        goalType: "player", goalName: "Damian Lillard"     },
    { startType: "team", startName: "Minnesota Vikings",       goalType: "player", goalName: "Ja Morant"          },
    { startType: "team", startName: "Denver Broncos",          goalType: "player", goalName: "Karl-Anthony Towns" },
    { startType: "team", startName: "Chicago Bears",           goalType: "player", goalName: "Devin Booker"       },
    { startType: "team", startName: "Detroit Lions",           goalType: "player", goalName: "Cade Cunningham"    },
    { startType: "team", startName: "Jacksonville Jaguars",    goalType: "player", goalName: "Paolo Banchero"     },
    { startType: "team", startName: "Indianapolis Colts",      goalType: "player", goalName: "Tyrese Haliburton"  },
    { startType: "team", startName: "Houston Texans",          goalType: "player", goalName: "Victor Wembanyama"  },
    { startType: "team", startName: "Tennessee Titans",        goalType: "player", goalName: "Desmond Bane"       },

    // ── index 60–79: NFL team → MLB player ──
    { startType: "team", startName: "Kansas City Chiefs",      goalType: "player", goalName: "Aaron Judge"        },
    { startType: "team", startName: "Dallas Cowboys",          goalType: "player", goalName: "Shohei Ohtani"      },
    { startType: "team", startName: "New England Patriots",    goalType: "player", goalName: "Paul Skenes"        },
    { startType: "team", startName: "Green Bay Packers",       goalType: "player", goalName: "Bryce Harper"       },
    { startType: "team", startName: "Pittsburgh Steelers",     goalType: "player", goalName: "Mike Trout"         },
    { startType: "team", startName: "San Francisco 49ers",     goalType: "player", goalName: "Freddie Freeman"    },
    { startType: "team", startName: "Philadelphia Eagles",     goalType: "player", goalName: "Gerrit Cole"        },
    { startType: "team", startName: "Buffalo Bills",           goalType: "player", goalName: "Juan Soto"          },
    { startType: "team", startName: "Baltimore Ravens",        goalType: "player", goalName: "Corey Seager"       },
    { startType: "team", startName: "Los Angeles Rams",        goalType: "player", goalName: "Clayton Kershaw"    },
    { startType: "team", startName: "Seattle Seahawks",        goalType: "player", goalName: "Julio Rodriguez"    },
    { startType: "team", startName: "Miami Dolphins",          goalType: "player", goalName: "Ronald Acuna Jr"    },
    { startType: "team", startName: "New York Giants",         goalType: "player", goalName: "Pete Alonso"        },
    { startType: "team", startName: "New Orleans Saints",      goalType: "player", goalName: "Yordan Alvarez"     },
    { startType: "team", startName: "Carolina Panthers",       goalType: "player", goalName: "Spencer Strider"    },
    { startType: "team", startName: "Atlanta Falcons",         goalType: "player", goalName: "Max Scherzer"       },
    { startType: "team", startName: "Arizona Cardinals",       goalType: "player", goalName: "Nolan Arenado"      },
    { startType: "team", startName: "Las Vegas Raiders",       goalType: "player", goalName: "Mookie Betts"       },
    { startType: "team", startName: "Los Angeles Chargers",    goalType: "player", goalName: "Vladimir Guerrero Jr"},
    { startType: "team", startName: "Tampa Bay Buccaneers",    goalType: "player", goalName: "Jose Altuve"        },

    // ── index 80–99: MLB team → NFL player ──
    { startType: "team", startName: "New York Yankees",        goalType: "player", goalName: "Patrick Mahomes"    },
    { startType: "team", startName: "Los Angeles Dodgers",     goalType: "player", goalName: "Josh Allen"         },
    { startType: "team", startName: "Boston Red Sox",          goalType: "player", goalName: "Joe Burrow"         },
    { startType: "team", startName: "Chicago Cubs",            goalType: "player", goalName: "Dak Prescott"       },
    { startType: "team", startName: "Houston Astros",          goalType: "player", goalName: "CJ Stroud"          },
    { startType: "team", startName: "Atlanta Braves",          goalType: "player", goalName: "Justin Jefferson"   },
    { startType: "team", startName: "San Francisco Giants",    goalType: "player", goalName: "Lamar Jackson"      },
    { startType: "team", startName: "St. Louis Cardinals",     goalType: "player", goalName: "Jalen Hurts"        },
    { startType: "team", startName: "San Diego Padres",        goalType: "player", goalName: "Trevor Lawrence"    },
    { startType: "team", startName: "Toronto Blue Jays",       goalType: "player", goalName: "Aaron Rodgers"      },
    { startType: "team", startName: "Pittsburgh Pirates",      goalType: "player", goalName: "Ja'Marr Chase"      },
    { startType: "team", startName: "Tampa Bay Rays",          goalType: "player", goalName: "Jayden Daniels"     },
    { startType: "team", startName: "Minnesota Twins",         goalType: "player", goalName: "Justin Herbert"     },
    { startType: "team", startName: "Seattle Mariners",        goalType: "player", goalName: "Drake Maye"         },
    { startType: "team", startName: "Colorado Rockies",        goalType: "player", goalName: "Tua Tagovailoa"     },
    { startType: "team", startName: "Miami Marlins",           goalType: "player", goalName: "Baker Mayfield"     },
    { startType: "team", startName: "Philadelphia Phillies",   goalType: "player", goalName: "Kirk Cousins"       },
    { startType: "team", startName: "Texas Rangers",           goalType: "player", goalName: "Matthew Stafford"   },
    { startType: "team", startName: "Arizona Diamondbacks",    goalType: "player", goalName: "Brock Purdy"        },
    { startType: "team", startName: "Washington Nationals",    goalType: "player", goalName: "Cam Newton"         },

    // ── index 100–119: MLB team → NBA player ──
    { startType: "team", startName: "New York Yankees",        goalType: "player", goalName: "LeBron James"       },
    { startType: "team", startName: "Los Angeles Dodgers",     goalType: "player", goalName: "Steph Curry"        },
    { startType: "team", startName: "Boston Red Sox",          goalType: "player", goalName: "Kevin Durant"       },
    { startType: "team", startName: "Chicago Cubs",            goalType: "player", goalName: "Jayson Tatum"       },
    { startType: "team", startName: "Houston Astros",          goalType: "player", goalName: "Joel Embiid"        },
    { startType: "team", startName: "Atlanta Braves",          goalType: "player", goalName: "Trae Young"         },
    { startType: "team", startName: "San Francisco Giants",    goalType: "player", goalName: "Klay Thompson"      },
    { startType: "team", startName: "St. Louis Cardinals",     goalType: "player", goalName: "Damian Lillard"     },
    { startType: "team", startName: "Pittsburgh Pirates",      goalType: "player", goalName: "Zion Williamson"    },
    { startType: "team", startName: "Toronto Blue Jays",       goalType: "player", goalName: "Jaylen Brown"       },
    // ── index 110: today (Jun 1) ──
    { startType: "team", startName: "Oakland Athletics",       goalType: "player", goalName: "Giannis Antetokounmpo"},
    { startType: "team", startName: "Tampa Bay Rays",          goalType: "player", goalName: "Anthony Davis"      },
    { startType: "team", startName: "San Diego Padres",        goalType: "player", goalName: "Nikola Jokic"       },
    { startType: "team", startName: "Seattle Mariners",        goalType: "player", goalName: "Anthony Edwards"    },
    { startType: "team", startName: "Minnesota Twins",         goalType: "player", goalName: "Karl-Anthony Towns" },
    { startType: "team", startName: "Miami Marlins",           goalType: "player", goalName: "Ja Morant"          },
    { startType: "team", startName: "Texas Rangers",           goalType: "player", goalName: "Devin Booker"       },
    { startType: "team", startName: "Colorado Rockies",        goalType: "player", goalName: "Tyrese Haliburton"  },
    { startType: "team", startName: "Kansas City Royals",      goalType: "player", goalName: "Cade Cunningham"    },
    { startType: "team", startName: "Milwaukee Brewers",       goalType: "player", goalName: "Victor Wembanyama"  },

    // ── index 120: today (Jun 1, 2026) ──
    { startType: "team", startName: "Los Angeles Lakers",      goalType: "player", goalName: "Patrick Mahomes"    },

    // ── index 121–149: mixed and harder combos ──
    { startType: "team", startName: "Chicago Bulls",           goalType: "player", goalName: "Aaron Judge"        },
    { startType: "team", startName: "San Antonio Spurs",       goalType: "player", goalName: "Josh Allen"         },
    { startType: "team", startName: "Oklahoma City Thunder",   goalType: "player", goalName: "Paul Skenes"        },
    { startType: "team", startName: "Utah Jazz",               goalType: "player", goalName: "Lamar Jackson"      },
    { startType: "team", startName: "New York Knicks",         goalType: "player", goalName: "Shohei Ohtani"      },
    { startType: "team", startName: "Washington Wizards",      goalType: "player", goalName: "Joe Burrow"         },
    { startType: "team", startName: "Orlando Magic",           goalType: "player", goalName: "Dak Prescott"       },
    { startType: "team", startName: "Detroit Pistons",         goalType: "player", goalName: "Bryce Harper"       },
    { startType: "team", startName: "Minnesota Timberwolves",  goalType: "player", goalName: "Gerrit Cole"        },
    { startType: "team", startName: "Sacramento Kings",        goalType: "player", goalName: "CJ Stroud"          },
    { startType: "team", startName: "New Orleans Pelicans",    goalType: "player", goalName: "Mike Trout"         },
    { startType: "team", startName: "Charlotte Hornets",       goalType: "player", goalName: "Justin Jefferson"   },
    { startType: "team", startName: "New York Mets",           goalType: "player", goalName: "LeBron James"       },
    { startType: "team", startName: "Baltimore Orioles",       goalType: "player", goalName: "Steph Curry"        },
    { startType: "team", startName: "Cincinnati Reds",         goalType: "player", goalName: "Patrick Mahomes"    },
    { startType: "team", startName: "Cleveland Guardians",     goalType: "player", goalName: "Justin Jefferson"   },
    { startType: "team", startName: "Detroit Tigers",          goalType: "player", goalName: "Kevin Durant"       },
    { startType: "team", startName: "Chicago White Sox",       goalType: "player", goalName: "Joe Burrow"         },
    { startType: "team", startName: "Oakland Athletics",       goalType: "player", goalName: "Dak Prescott"       },
    { startType: "team", startName: "New York Mets",           goalType: "player", goalName: "Josh Allen"         },
    { startType: "team", startName: "Kansas City Royals",      goalType: "player", goalName: "Lamar Jackson"      },
    { startType: "team", startName: "Milwaukee Brewers",       goalType: "player", goalName: "Trae Young"         },
    { startType: "team", startName: "Baltimore Orioles",       goalType: "player", goalName: "Jaylen Brown"       },
    { startType: "team", startName: "Cincinnati Reds",         goalType: "player", goalName: "Zion Williamson"    },
    { startType: "team", startName: "Cleveland Guardians",     goalType: "player", goalName: "Joel Embiid"        },
    { startType: "team", startName: "Detroit Tigers",          goalType: "player", goalName: "Ja Morant"          },
    { startType: "team", startName: "Chicago White Sox",       goalType: "player", goalName: "Jayson Tatum"       },
    { startType: "team", startName: "Washington Nationals",    goalType: "player", goalName: "Nikola Jokic"       },
    { startType: "team", startName: "Miami Marlins",           goalType: "player", goalName: "Aaron Rodgers"      },
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
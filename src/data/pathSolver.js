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
  const candidates = [
    {
      startType: "team",
      startName: "Arizona Diamondbacks",
      goalType: "player",
      goalName: "Russell Wilson",
    },
    {
      startType: "team",
      startName: "Los Angeles Lakers",
      goalType: "player",
      goalName: "Tom Brady",
    },
    {
      startType: "team",
      startName: "Philadelphia Eagles",
      goalType: "player",
      goalName: "Shohei Ohtani",
    },
    {
      startType: "team",
      startName: "New York Yankees",
      goalType: "player",
      goalName: "LeBron James",
    },
  ];

  const today = new Date();
  const dateStr = `${today.getFullYear()}-${today.getMonth()}-${today.getDate()}`;

  let hash = 0;
  for (let i = 0; i < dateStr.length; i++) {
    hash = ((hash << 5) - hash) + dateStr.charCodeAt(i);
    hash |= 0;
  }

  const challenge = candidates[Math.abs(hash) % candidates.length];
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
    par: optimalPath ? Math.max(6, optimalPath.length - 1) : 7,
  };
}
import { supabase } from "../lib/supabase.js";

// In-memory cache: lowercase player name → use count
const usageCache = new Map();
let cacheLoaded = false;

export async function loadPlayerUsage() {
  if (cacheLoaded) return;

  const { data, error } = await supabase
    .from("player_usage")
    .select("player_name, use_count");

  if (!error && data) {
    for (const row of data) {
      usageCache.set(row.player_name.toLowerCase(), row.use_count);
    }
  }

  cacheLoaded = true;
}

export function getPlayerUsageCount(playerName) {
  return usageCache.get(playerName.toLowerCase()) ?? 0;
}

export async function recordPlayerUse(playerName) {
  // Optimistic local update so scoring reflects it immediately next turn
  const current = getPlayerUsageCount(playerName);
  usageCache.set(playerName.toLowerCase(), current + 1);

  await supabase.rpc("increment_player_usage", { p_name: playerName });
}

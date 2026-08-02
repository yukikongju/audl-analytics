/* ═══════════════════════════════════════════════════════════
   api.js — the ONLY data boundary in the app.
   Today: reads static JSON from data/. Later: swap each body for
   fetch('/api/...'). Callers only ever see Promises, so the swap
   is invisible to pages. Query objects (`q`) are accepted now and
   become querystrings when the live API lands.
   ═══════════════════════════════════════════════════════════ */

const _cache = new Map();
function load(url){
  if (!_cache.has(url)){
    _cache.set(url, fetch(url).then(r => {
      if (!r.ok) throw new Error(`${r.status} ${url}`);
      return r.json();
    }));
  }
  return _cache.get(url);
}

export const api = {
  // collections (leaderboard / ticker / schedule / search)
  getPlayers: (q = {}) => load('data/players.json'),
  getTeams:   (q = {}) => load('data/teams.json'),
  getGames:   (q = {}) => load('data/games.json'),

  // single entities
  getPlayer: (id) => load(`data/players/${id}.json`),
  getTeam:   (id) => load(`data/teams/${id}.json`),
  getGame:   (id) => load(`data/games/${id}.json`),
};

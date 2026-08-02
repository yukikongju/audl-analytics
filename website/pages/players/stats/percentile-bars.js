/* percentile-bars.js — player percentile rankings.
   Ported from inspiration/player_profile.html pctBars. Colocated
   (player Stats tab only). Values are real league percentiles when
   given a `rankings` array; falls back to seeded demo otherwise. */
import { P } from '../../../js/theme.js';
import { noise } from '../../../js/util.js';

/** rankings: [{label, val}] where val is 0–100. Renders into `mount`. */
export function renderPercentileBars(mount, rankings){
  mount.innerHTML = rankings.map(s => {
    const col = s.val >= 70 ? P.lime : s.val >= 50 ? P.orange : P.red;
    return `<div class="pct-row">
      <span class="label">${s.label}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${s.val}%;background:${col};opacity:.35"></div></div>
      <span class="dot" style="background:${col}"></span>
      <span class="val" style="color:${col}">${s.val}</span>
    </div>`;
  }).join('');
}

/** Seeded demo rankings for a player. */
export function percentileData(seed){
  const labels = ['A', 'R-aEC', 'PI-T', 'OI%', 'Tot-aEC', 'G', 'T-aEC', 'LC', 'xCP', 'PI-P', 'B', 'CPOE'];
  return labels.map((label, i) => ({
    label,
    val: Math.round(20 + noise(i, seed) * 70),
  })).sort((a, b) => b.val - a.val);
}

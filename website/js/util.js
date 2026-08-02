/* util.js — small shared helpers.
   pctile/pctClass lifted from inspiration/leaderboard.html; used by
   the shared stats table for percentile-colored cells. */

/** Percentile (0–100) of `val` within `arr`. */
export function pctile(val, arr, higherBetter = true){
  const sorted = [...arr].sort((a, b) => a - b);
  const idx = sorted.filter(v => v < val).length;
  const p = Math.round((idx / sorted.length) * 100);
  return higherBetter ? p : 100 - p;
}

/** Bucket a percentile into a CSS class: hi (>=75) / mid (>=40) / lo. */
export function pctClass(p){
  return p >= 75 ? 'hi' : p >= 40 ? 'mid' : 'lo';
}

/** Small DOM helper: create an element from an HTML string. */
export function el(html){
  const t = document.createElement('template');
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

/** clamp */
export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

/* ─── deterministic noise (for seeded demo data until the live API) ───
   Same idea as the mockups' `sn()` but seeded so a given player/team
   always renders the same chart. Swap for real api data later. */
export function noise(a, b = 0, c = 0){
  const x = Math.sin(a * 127.1 + b * 311.7 + c * 73.13) * 43758.5453;
  return x - Math.floor(x);
}
export function hashStr(s = ''){
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h) % 997;
}

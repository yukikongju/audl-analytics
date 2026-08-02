/* rose.js — throw/receive direction rose chart.
   Ported from inspiration/player_profile.html drawRose(). Single
   consumer (player Stats tab) → colocated here per the plan. */
import { P } from '../../../js/theme.js';
import { noise } from '../../../js/util.js';

/** Render a rose chart of `data` ([{v, c}]) into an <svg> element. */
export function renderRose(svg, data){
  const n = data.length, maxR = 80;
  const maxVal = Math.max(...data.map(d => d.v));
  let html = '';
  [0.25, 0.5, 0.75, 1].forEach(f => {
    html += `<circle cx="0" cy="0" r="${maxR * f}" fill="none" stroke="rgba(255,255,255,.06)" stroke-width=".5"/>`;
  });
  data.forEach((d, i) => {
    const a1 = (i / n) * Math.PI * 2 - Math.PI / 2;
    const a2 = ((i + 1) / n) * Math.PI * 2 - Math.PI / 2;
    const r = maxR * (d.v / maxVal);
    const x1 = Math.cos(a1) * r, y1 = Math.sin(a1) * r;
    const x2 = Math.cos(a2) * r, y2 = Math.sin(a2) * r;
    html += `<path d="M0,0 L${x1},${y1} A${r},${r} 0 0,1 ${x2},${y2} Z" fill="${d.c}" opacity=".7" stroke="rgba(0,0,0,.3)" stroke-width=".5"/>`;
  });
  svg.innerHTML = html;
}

/** Deterministic demo data for one player. */
export function roseData(seed, kind){
  const cols = [P.lime, P.blue, P.purple, P.orange];
  const off = kind === 'recv' ? 1 : 0;
  return Array.from({ length: 12 }, (_, i) => ({
    v: 26 + Math.sin(i * 1.3 + seed) * 18 + noise(i, seed, off) * 14,
    c: cols[(i + off) % 4],
  }));
}

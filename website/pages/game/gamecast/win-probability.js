/* win-probability.js — game win-probability line chart.
   Ported from inspiration/game.html. Colocated (Gamecast only). */
import { P } from '../../../js/theme.js';
import { noise } from '../../../js/util.js';

/** pts: array of home-win-% (0–100). Renders an SVG into `svg` element. */
export function renderWinProbability(svg, pts){
  const W = 500, H = 200, pad = 10, n = pts.length;
  const X = (i) => pad + (i / (n - 1)) * (W - pad * 2);
  const Y = (p) => pad + (1 - p / 100) * (H - pad * 2);
  const line = pts.map((p, i) => (i ? ' L' : 'M') + X(i).toFixed(1) + ',' + Y(p).toFixed(1)).join('');
  const midY = Y(50);

  let s = `<defs>
    <linearGradient id="homeGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${P.home}"/><stop offset="1" stop-color="${P.home}" stop-opacity="0"/></linearGradient>
    <linearGradient id="awayGrad" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="${P.away}"/><stop offset="1" stop-color="${P.away}" stop-opacity="0"/></linearGradient>
  </defs>`;
  s += `<line x1="${pad}" y1="${midY}" x2="${W - pad}" y2="${midY}" stroke="rgba(255,255,255,.1)" stroke-width="1" stroke-dasharray="4 3"/>`;
  [0.25, 0.5, 0.75].forEach(f => { const x = pad + f * (W - pad * 2); s += `<line x1="${x}" y1="${pad}" x2="${x}" y2="${H - pad}" stroke="rgba(255,255,255,.05)" stroke-width="1"/>`; });
  s += `<path d="${line} L${X(n - 1)},${H - pad} L${pad},${H - pad} Z" fill="url(#homeGrad)" opacity=".2"/>`;
  s += `<path d="${line} L${X(n - 1)},${pad} L${pad},${pad} Z" fill="url(#awayGrad)" opacity=".15"/>`;
  s += `<path d="${line}" fill="none" stroke="${P.text}" stroke-width="1.5"/>`;
  s += `<text x="${W - pad + 4}" y="${pad + 4}" fill="${P.home}" font-size="10" font-family="'JetBrains Mono',monospace" font-weight="700">100%</text>`;
  s += `<text x="${W - pad + 4}" y="${midY + 3}" fill="${P.dim}" font-size="9" font-family="'JetBrains Mono',monospace">50%</text>`;
  s += `<text x="${W - pad + 4}" y="${H - pad + 4}" fill="${P.away}" font-size="10" font-family="'JetBrains Mono',monospace" font-weight="700">0%</text>`;
  s += `<circle cx="${X(n - 1)}" cy="${Y(pts[n - 1])}" r="4" fill="${pts[n - 1] >= 50 ? P.home : P.away}" stroke="${P.panel2}" stroke-width="2"/>`;
  svg.innerHTML = s;
}

/** Seeded win-probability walk ending at the actual winner. */
export function winProbData(seed, homeWon){
  const n = 39; const pts = [];
  let v = 50;
  for (let i = 0; i < n; i++){
    v += (noise(i, seed) - 0.5) * 22;
    v = Math.max(4, Math.min(96, v));
    pts.push(Math.round(v));
  }
  // ease toward the real outcome at the end
  const target = homeWon ? 100 : 0;
  for (let i = n - 6; i < n; i++){ const w = (i - (n - 6)) / 5; pts[i] = Math.round(pts[i] * (1 - w) + target * w); }
  return pts;
}

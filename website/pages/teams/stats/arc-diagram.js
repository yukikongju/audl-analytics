/* arc-diagram.js — team throwing/receiving connections as an arc diagram.
   Ported from inspiration/team_profile.html. Colocated (Team Stats only). */
import { P } from '../../../js/theme.js';
import { noise } from '../../../js/util.js';

const COLORS = [P.blue, P.lime, P.orange, P.purple, P.teal, P.red, P.blue, P.lime, P.orange, P.purple];

/** players: [name]. connections: [[aIdx, bIdx, weight]]. Renders into `mount`. */
export function renderArcDiagram(mount, players, connections){
  const N = players.length, svgW = 680, svgH = 360, padL = 10, padR = 10;
  const nodeW = svgW - padL - padR, nodeY = svgH - 30;
  const maxW = Math.max(...connections.map(c => c[2]));
  const pos = players.map((_, i) => padL + (i / (N - 1)) * nodeW);

  let svg = `<svg width="100%" viewBox="0 0 ${svgW} ${svgH}" style="max-width:${svgW}px">`;
  connections.forEach(([a, b, w]) => {
    const x1 = pos[a], x2 = pos[b], radius = Math.abs(x2 - x1) / 2;
    svg += `<path d="M${x1},${nodeY} A${radius},${radius} 0 0,1 ${x2},${nodeY}" fill="none" stroke="${COLORS[a % COLORS.length]}" stroke-width="${1 + (w / maxW) * 8}" opacity="${0.15 + (w / maxW) * 0.45}"/>`;
  });
  players.forEach((p, i) => {
    svg += `<circle cx="${pos[i]}" cy="${nodeY}" r="5" fill="${COLORS[i % COLORS.length]}" stroke="${P.panel}" stroke-width="2"/>`;
    svg += `<text x="${pos[i]}" y="${nodeY + 12}" text-anchor="end" transform="rotate(-45,${pos[i]},${nodeY + 12})" fill="${P.dim}" font-size="9" font-family="'JetBrains Mono',monospace" font-weight="500">${p}</text>`;
  });
  mount.innerHTML = svg + '</svg>';
}

/** Seeded demo connections among a roster (list of names). */
export function arcData(names, seed){
  const conns = [];
  const n = names.length;
  for (let i = 0; i < Math.min(14, n * 1.4); i++){
    const a = Math.floor(noise(i, seed) * n);
    let b = Math.floor(noise(i, seed, 5) * n);
    if (b === a) b = (b + 1) % n;
    conns.push([a, b, Math.round(12 + noise(i, seed, 9) * 56)]);
  }
  return conns;
}

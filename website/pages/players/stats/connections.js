/* connections.js — a player's top throwing/receiving partners.
   Ported from inspiration/player_profile.html connections. Colocated
   (player Stats tab only). */
import { P } from '../../../js/theme.js';
import { noise } from '../../../js/util.js';

/** conns: [{name, throws, recv, pct, partner}]. Renders into `mount`. */
export function renderConnections(mount, conns){
  const maxConn = Math.max(...conns.map(c => c.throws + c.recv));
  let h = `<div style="display:grid;grid-template-columns:auto 1fr auto auto;gap:6px 0;align-items:center;font-family:'JetBrains Mono',monospace;font-size:11px;">`;
  h += `<span style="color:var(--dim);font-size:9px;text-align:right;padding-right:10px;text-transform:uppercase;letter-spacing:.06em">Thrower</span><span></span><span style="color:var(--dim);font-size:9px;padding-left:10px;text-transform:uppercase;letter-spacing:.06em">Receiver</span><span style="color:var(--dim);font-size:9px;text-align:right;padding-left:8px;text-transform:uppercase;letter-spacing:.06em">%</span>`;
  conns.forEach(c => {
    const col = c.pct >= 85 ? P.lime : c.pct >= 75 ? P.blue : P.orange;
    h += `
      <span style="text-align:right;padding-right:10px;color:var(--text);font-size:11px">${c.name}</span>
      <div style="display:flex;gap:3px;height:22px;align-items:center">
        <div style="flex:${c.throws};height:100%;background:${P.blue};border-radius:3px 0 0 3px;opacity:.6"></div>
        <div style="flex:${c.recv};height:100%;background:${P.purple};border-radius:0 3px 3px 0;opacity:.6"></div>
      </div>
      <span style="padding-left:10px;color:var(--text);font-size:11px">${c.partner}</span>
      <span style="text-align:right;padding-left:8px;font-weight:700;color:${col}">${c.pct}%</span>`;
  });
  h += `</div><div class="legend" style="justify-content:center;margin-top:14px"><span class="gi"><span class="gd" style="background:${P.blue}"></span>Throws to</span><span class="gi"><span class="gd" style="background:${P.purple}"></span>Receives from</span></div>`;
  mount.innerHTML = h;
}

/** Seeded demo connections for a player. */
export function connectionsData(seed){
  const names = ['Enzo F.', 'Jakob B.', 'Christophe T.', 'Malik A.', 'Jacob D.'];
  const partners = ['Malik A.', 'Enzo F.', 'Christophe T.', 'Jakob B.', 'Simon R.'];
  return names.map((name, i) => ({
    name,
    throws: Math.round(20 + noise(i, seed) * 25),
    recv: Math.round(18 + noise(i, seed, 2) * 22),
    pct: Math.round(74 + noise(i, seed, 3) * 18),
    partner: partners[i],
  }));
}

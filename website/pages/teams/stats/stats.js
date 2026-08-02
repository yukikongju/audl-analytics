/* Team → Stats tab. Reuses the shared stats-table (team row vs league)
   + top performers list + colocated arc diagram of connections. */
import { renderStatsTable } from '../../../js/stats-table.js';
import { hashStr } from '../../../js/util.js';
import { renderArcDiagram, arcData } from './arc-diagram.js';

const f1 = (v) => (+v).toFixed(1);
const signed = (v, d = 2) => (v > 0 ? '+' : '') + (+v).toFixed(d);

const TEAM_COLS = [
  { key:'record', label:'Record', sortVal:r => r.winPct },
  { key:'winPct', label:'Win%', fmt:r => r.winPct.toFixed(3) },
  { key:'gp', label:'GP' },
  { key:'ss', label:'SS Rk', divide:true, fmt:r => signed(r.ss), color:r => r.ss > 0 ? 'var(--lime)' : 'var(--red)', pctileOf:r => r.ss },
  { key:'sos', label:'SOS', fmt:r => signed(r.sos) },
  { key:'scoreFor', label:'S', divide:true, fmt:r => f1(r.scoreFor), pctileOf:r => r.scoreFor },
  { key:'scoreAgainst', label:'SA', fmt:r => f1(r.scoreAgainst), pctileOf:r => r.scoreAgainst, higherBetter:false },
  { key:'oe', label:'OE', divide:true, fmt:r => f1(r.oe) + '%', pctileOf:r => r.oe },
  { key:'de', label:'DE', fmt:r => f1(r.de) + '%', pctileOf:r => r.de },
  { key:'turnovers', label:'T', divide:true, fmt:r => f1(r.turnovers), pctileOf:r => r.turnovers, higherBetter:false },
  { key:'blocks', label:'B', fmt:r => f1(r.blocks), pctileOf:r => r.blocks },
  { key:'aec', label:'aEC', fmt:r => f1(r.aec), pctileOf:r => r.aec },
];
const GROUPS = [
  { label:'Standing', span:3 },
  { label:'Ratings', span:2, divide:true },
  { label:'Scores', span:2, divide:true },
  { label:'Conversion', span:2, divide:true },
  { label:'Box Stats', span:3, divide:true },
];

export async function init(content, ctx){
  const [teams, players] = await Promise.all([ctx.api.getTeams(), ctx.api.getPlayers()]);
  const team = teams.find(t => t.id === ctx.params.id);
  if (!team){ content.innerHTML = `<div class="content" style="grid-template-columns:1fr"><div class="card"><h3>Team not found</h3></div></div>`; return; }

  const roster = players.filter(p => p.team === team.id);
  const names = (roster.length ? roster : players.slice(0, 8)).map(p => p.name.split(' ').map((w, i) => i ? w[0] + '.' : w).join(' '));
  const seed = hashStr(team.id);

  // top performers by a few categories
  const cats = [
    { label:'Tot-aEC', key:'aec' }, { label:'Goals', key:'g' },
    { label:'Assists', key:'a' }, { label:'Completions', key:'c' },
  ];

  content.innerHTML = `
    <div style="padding:24px 5vw 0"><div id="t-table"></div></div>
    <div class="content" style="grid-template-columns:320px 1fr">
      <div class="card">
        <h3>Top Performers</h3>
        <div id="perf"></div>
      </div>
      <div class="card">
        <h3>Team Connections</h3>
        <div class="note" style="margin-top:0;margin-bottom:14px">Top throwing/receiving pairs by volume</div>
        <div id="arc"></div>
      </div>
    </div>`;

  renderStatsTable(content.querySelector('#t-table'), {
    title: `${team.city} ${team.name} — Season 2026`, columns: TEAM_COLS, groups: GROUPS,
    rows: [team], pctileRows: teams,
  });

  content.querySelector('#perf').innerHTML = cats.map(c => {
    const top = [...roster].sort((a, b) => b[c.key] - a[c.key]).slice(0, 3);
    return `<div style="padding:12px 0;border-bottom:1px solid var(--line)">
      <div style="font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--orange);margin-bottom:8px;padding-left:10px;border-left:2px solid var(--orange)">${c.label}</div>
      ${top.map((p, i) => `<div style="display:flex;align-items:baseline;padding:3px 0;font-family:'JetBrains Mono',monospace;font-size:12px"><span style="width:20px;color:var(--dim);font-size:10px">${i + 1}</span><a href="#/players/${p.id}/stats" style="flex:1;font-weight:600;color:var(--text);text-decoration:none">${p.name}</a><span style="color:var(--dim)">${f1(p[c.key])}</span></div>`).join('')}
    </div>`;
  }).join('') || '<div class="note">No roster data.</div>';

  renderArcDiagram(content.querySelector('#arc'), names, arcData(names, seed));
}

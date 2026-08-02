/* Leaderboard → Players tab. Player column config (with percentile
   badges) handed to the shared stats-table. Search + min-games filter. */
import { renderStatsTable, entityCell } from '../../../js/stats-table.js';

const f1 = (v) => (+v).toFixed(1);

function columns(teamById){
  return [
    { key:'name', label:'Player', sticky:true, left:'0', sortVal:r => r.name,
      render:r => entityCell({ href:`#/players/${r.id}/stats`, label:r.name }) },
    { key:'team', label:'Team', sticky:true, left:'120px', sortVal:r => r.team,
      render:r => { const t = teamById[r.team]; return entityCell({ color:t?.color, label:t?.name || r.team, dim:true }); } },
    // Contribution
    { key:'aec',  label:'Tot-aEC', divide:true, fmt:r => f1(r.aec),  pctileOf:r => r.aec },
    { key:'taec', label:'T-aEC',  fmt:r => f1(r.taec), pctileOf:r => r.taec },
    { key:'raec', label:'R-aEC',  fmt:r => f1(r.raec), pctileOf:r => r.raec },
    // Box score
    { key:'g', label:'G', divide:true, pctileOf:r => r.g },
    { key:'a', label:'A', pctileOf:r => r.a },
    { key:'c', label:'C', pctileOf:r => r.c },
    { key:'t', label:'T' },
    { key:'b', label:'B' },
    // Throwing
    { key:'cp',  label:'CP%', divide:true, fmt:r => f1(r.cp),  pctileOf:r => r.cp },
    { key:'hu',  label:'HuR', fmt:r => f1(r.hu),  pctileOf:r => r.hu },
    { key:'xcp', label:'xCP', fmt:r => f1(r.xcp), pctileOf:r => r.xcp },
    // Usage
    { key:'gp', label:'GP', divide:true },
  ];
}

const GROUPS = [
  { span:1, sticky:true, left:'0' }, { span:1, sticky:true, left:'120px' },
  { label:'Contribution', span:3, divide:true },
  { label:'Box Score', span:5, divide:true },
  { label:'Throwing', span:3, divide:true },
  { label:'Usage', span:1, divide:true },
];

export async function init(content, ctx){
  const [players, teams] = await Promise.all([ctx.api.getPlayers(), ctx.api.getTeams()]);
  const teamById = Object.fromEntries(teams.map(t => [t.id, t]));
  let search = '', minGP = 1;

  content.innerHTML = `<div class="controls" id="lb-filters"></div><div id="lb-table"></div>`;
  const filters = content.querySelector('#lb-filters');
  const table = content.querySelector('#lb-table');

  filters.innerHTML = `
    <div class="ctrl-group"><label>Season</label><select><option>2026</option><option>2025</option></select></div>
    <div class="ctrl-group"><label>View</label><select><option>Per Game</option><option>Total</option><option>Per Point</option></select></div>
    <div class="ctrl-group"><label>Search</label><input type="text" id="lb-search" placeholder="Player name..."></div>
    <div class="spacer"></div>
    <div class="ctrl-group"><label>Min Games <span id="mg-val">1</span></label>
      <input type="range" id="lb-mg" min="1" max="15" value="1"></div>`;

  filters.querySelector('#lb-search').addEventListener('input', (e) => { search = e.target.value.toLowerCase(); draw(); });
  filters.querySelector('#lb-mg').addEventListener('input', (e) => { minGP = +e.target.value; filters.querySelector('#mg-val').textContent = minGP; draw(); });

  function draw(){
    let rows = players.filter(p => p.gp >= minGP);
    if (search) rows = rows.filter(p => p.name.toLowerCase().includes(search));
    renderStatsTable(table, {
      title: 'Player Rankings', columns: columns(teamById), groups: GROUPS,
      rows, defaultSort: { key:'aec', dir:-1 },
    });
  }

  draw();
}

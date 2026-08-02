/* Leaderboard → Teams tab. Builds a team column config and hands it
   to the shared stats-table. Division pills re-filter the rows. */
import { renderStatsTable, entityCell } from '../../../js/stats-table.js';

const DIVISIONS = ['all', 'east', 'central', 'south', 'west'];

const fmt1  = (v) => (+v).toFixed(1);
const signed = (v, d = 2) => (v > 0 ? '+' : '') + (+v).toFixed(d);

function columns(){
  return [
    { key:'__rank', label:'Rk', sticky:true, left:'0' },
    { key:'name', label:'Team', sticky:true, left:'32px',
      sortVal:r => r.name,
      render:r => entityCell({ href:`#/teams/${r.id}/stats`, color:r.color, label:r.name }) },
    // Standing
    { key:'record', label:'Record', divide:true, sortVal:r => r.winPct },
    { key:'winPct', label:'Win%', fmt:r => r.winPct.toFixed(3) },
    { key:'gp', label:'GP' },
    // Ratings
    { key:'ss', label:'SS Rk', divide:true, fmt:r => signed(r.ss), color:r => r.ss > 0 ? 'var(--lime)' : 'var(--red)' },
    { key:'sos', label:'SOS', fmt:r => signed(r.sos) },
    // Scores
    { key:'scoreFor', label:'S', divide:true, fmt:r => fmt1(r.scoreFor) },
    { key:'scoreAgainst', label:'SA', fmt:r => fmt1(r.scoreAgainst) },
    { key:'diff', label:'Diff', sortVal:r => r.scoreFor - r.scoreAgainst,
      fmt:r => signed(r.scoreFor - r.scoreAgainst, 1),
      color:r => { const d = r.scoreFor - r.scoreAgainst; return d > 0 ? 'pos' : d < 0 ? 'neg' : ''; } },
    // Conversion
    { key:'oe', label:'OE', divide:true, fmt:r => fmt1(r.oe) + '%' },
    { key:'de', label:'DE', fmt:r => fmt1(r.de) + '%' },
    // Box
    { key:'turnovers', label:'T', divide:true, fmt:r => fmt1(r.turnovers) },
    { key:'blocks', label:'B', fmt:r => fmt1(r.blocks) },
    { key:'aec', label:'aEC', fmt:r => fmt1(r.aec) },
  ];
}

const GROUPS = [
  { span:1, sticky:true, left:'0' }, { span:1, sticky:true, left:'32px' },
  { label:'Standing', span:3, divide:true },
  { label:'Ratings', span:2, divide:true },
  { label:'Scores', span:3, divide:true },
  { label:'Conversion', span:2, divide:true },
  { label:'Box Stats', span:3, divide:true },
];

export async function init(content, ctx){
  const all = await ctx.api.getTeams();
  let division = 'all';

  content.innerHTML = `<div class="controls" id="lb-filters"></div><div id="lb-table"></div>`;
  const filters = content.querySelector('#lb-filters');
  const table = content.querySelector('#lb-table');

  function renderFilters(){
    filters.innerHTML = `
      <div class="ctrl-group"><label>Season</label><select><option>2026</option><option>2025</option></select></div>
      <div class="ctrl-group"><label>View</label><select><option>Per Game</option><option>Total</option><option>Per Point</option></select></div>
      <div class="spacer"></div>
      <div class="pills" id="divs">
        ${DIVISIONS.map(d => `<button class="pill${division === d ? ' active' : ''}" data-div="${d}">${d.toUpperCase()}</button>`).join('')}
      </div>`;
    filters.querySelector('#divs').addEventListener('click', (e) => {
      const b = e.target.closest('.pill'); if (!b) return;
      division = b.dataset.div; renderFilters(); draw();
    });
  }

  function draw(){
    const rows = division === 'all' ? all : all.filter(t => t.div === division);
    renderStatsTable(table, {
      title: 'Teams Leaderboard', columns: columns(), groups: GROUPS,
      rows, defaultSort: { key:'ss', dir:-1 },
    });
  }

  renderFilters();
  draw();
}

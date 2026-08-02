/* Team → Roster tab. Reuses the shared stats-table with player columns,
   filtered to this team (percentiles ranked league-wide for context). */
import { renderStatsTable, entityCell } from '../../../js/stats-table.js';

const f1 = (v) => (+v).toFixed(1);

export async function init(content, ctx){
  const [players, teams] = await Promise.all([ctx.api.getPlayers(), ctx.api.getTeams()]);
  const team = teams.find(t => t.id === ctx.params.id);
  const roster = players.filter(p => p.team === ctx.params.id);

  content.innerHTML = `<div style="padding:24px 5vw 0"><div id="r-table"></div></div>`;

  const columns = [
    { key:'__rank', label:'#', sticky:true, left:'0' },
    { key:'name', label:'Player', sticky:true, left:'32px', sortVal:r => r.name,
      render:r => entityCell({ href:`#/players/${r.id}/stats`, color:team?.color, label:r.name }) },
    { key:'g', label:'G', divide:true, pctileOf:r => r.g },
    { key:'a', label:'A', pctileOf:r => r.a },
    { key:'c', label:'C', pctileOf:r => r.c },
    { key:'t', label:'T' },
    { key:'b', label:'B' },
    { key:'cp', label:'CP%', divide:true, fmt:r => f1(r.cp), pctileOf:r => r.cp },
    { key:'aec', label:'aEC', fmt:r => f1(r.aec), pctileOf:r => r.aec },
    { key:'gp', label:'GP', divide:true },
  ];

  renderStatsTable(content.querySelector('#r-table'), {
    title: `${team ? team.city + ' ' + team.name : 'Team'} — Roster`,
    columns, rows: roster, pctileRows: players, defaultSort: { key:'aec', dir:-1 },
  });
}

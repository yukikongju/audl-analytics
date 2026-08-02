/* Game → Box Score tab: reuses the shared stats-table for each team's
   contributors. (Season lines stand in until per-game stats land in the api.) */
import { renderStatsTable, entityCell } from '../../../js/stats-table.js';

const f1 = (v) => (+v).toFixed(1);

function boxColumns(color){
  return [
    { key:'name', label:'Player', sticky:true, left:'0', sortVal:r => r.name,
      render:r => entityCell({ href:`#/players/${r.id}/stats`, color, label:r.name }) },
    { key:'g', label:'G', divide:true }, { key:'a', label:'A' }, { key:'c', label:'C' },
    { key:'t', label:'T' }, { key:'b', label:'B' },
    { key:'cp', label:'CP%', divide:true, fmt:r => f1(r.cp) },
  ];
}

export async function init(content, ctx){
  const [games, teams, players] = await Promise.all([ctx.api.getGames(), ctx.api.getTeams(), ctx.api.getPlayers()]);
  const g = games.find(x => x.id === ctx.params.id) || {};
  const byAb = Object.fromEntries(teams.map(t => [t.ab, t]));
  const sides = [{ ab:g.away, label:'Away' }, { ab:g.home, label:'Home' }];

  content.innerHTML = `<div class="content" style="grid-template-columns:1fr" id="box"></div>`;
  const box = content.querySelector('#box');

  sides.forEach(side => {
    const team = byAb[side.ab];
    const roster = team ? players.filter(p => p.team === team.id) : [];
    const holder = document.createElement('div');
    box.appendChild(holder);
    renderStatsTable(holder, {
      title: `${side.label} — ${team ? team.city + ' ' + team.name : side.ab}`,
      columns: boxColumns(team?.color), rows: roster,
      defaultSort: { key:'g', dir:-1 },
    });
  });

  if (!byAb[g.home] && !byAb[g.away]){
    box.innerHTML = `<div class="card"><h3>No box score</h3><p class="note">Roster data unavailable for this matchup.</p></div>`;
  }
}

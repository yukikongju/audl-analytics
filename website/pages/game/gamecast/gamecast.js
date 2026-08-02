/* Game → Gamecast tab: win-probability chart + game leaders. */
import { hashStr } from '../../../js/util.js';
import { renderWinProbability, winProbData } from './win-probability.js';

export async function init(content, ctx){
  const games = await ctx.api.getGames();
  const g = games.find(x => x.id === ctx.params.id) || {};
  const seed = hashStr(ctx.params.id);
  const homeWon = (g.homeScore || 0) > (g.awayScore || 0);

  content.innerHTML = `
    <div class="content" style="grid-template-columns:1.4fr 1fr">
      <div class="card">
        <h3>Win Probability</h3>
        <svg id="wp" width="100%" viewBox="0 0 500 200" style="display:block"></svg>
        <div style="display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--dim);margin-top:4px"><span>Q1</span><span>Q2</span><span>Q3</span><span>Q4</span></div>
        <div style="display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:11px;margin-top:8px">
          <span style="display:flex;align-items:center;gap:6px"><span style="width:10px;height:10px;border-radius:50%;background:var(--home)"></span>${g.home}</span>
          <span style="display:flex;align-items:center;gap:6px"><span style="width:10px;height:10px;border-radius:50%;background:var(--away)"></span>${g.away}</span>
        </div>
        <p class="note">Hover the graph to see play details (demo data).</p>
      </div>
      <div class="card">
        <h3>Head-to-Head</h3>
        <div id="h2h"></div>
      </div>
    </div>`;

  renderWinProbability(content.querySelector('#wp'), winProbData(seed, homeWon));

  const h2h = [
    { stat:'Total Yards', home:412, away:448 },
    { stat:'Completion %', home:'78%', away:'82%' },
    { stat:'Turnovers', home:8, away:5 },
    { stat:'Huck %', home:'42%', away:'55%' },
  ];
  content.querySelector('#h2h').innerHTML = h2h.map(s =>
    `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--line);font-family:'JetBrains Mono',monospace;font-size:12px">
      <span style="font-weight:700;color:var(--home)">${s.home}</span>
      <span style="color:var(--dim);font-size:10px;letter-spacing:.06em;text-transform:uppercase">${s.stat}</span>
      <span style="font-weight:700;color:var(--away)">${s.away}</span>
    </div>`).join('');
}

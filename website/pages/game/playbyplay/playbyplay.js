/* Game → Play-by-Play tab: seeded scoring timeline. (Real events from
   the api later — the pipeline already produces throw-level data.) */
import { P } from '../../../js/theme.js';
import { noise, hashStr } from '../../../js/util.js';

export async function init(content, ctx){
  const games = await ctx.api.getGames();
  const g = games.find(x => x.id === ctx.params.id) || { home:'H', away:'A', homeScore:0, awayScore:0 };
  const seed = hashStr(ctx.params.id);
  const total = (g.homeScore || 0) + (g.awayScore || 0);

  // build a plausible scoring sequence that ends on the real final
  let h = 0, a = 0;
  const events = [];
  for (let i = 0; i < total; i++){
    const remainingH = (g.homeScore || 0) - h, remainingA = (g.awayScore || 0) - a;
    const homeScores = noise(i, seed) < remainingH / (remainingH + remainingA || 1);
    if (homeScores) h++; else a++;
    events.push({ q: Math.min(4, Math.floor(i / (total / 4)) + 1), home: h, away: a, team: homeScores ? g.home : g.away, scoredHome: homeScores });
  }

  content.innerHTML = `
    <div class="content" style="grid-template-columns:1fr">
      <div class="card">
        <h3>Scoring Timeline</h3>
        <div style="font-family:'JetBrains Mono',monospace;font-size:12px">
          ${events.map(e => `
            <div style="display:grid;grid-template-columns:40px 1fr auto;gap:12px;align-items:center;padding:7px 0;border-bottom:1px solid rgba(37,48,60,.5)">
              <span style="color:var(--dim);font-size:10px">Q${e.q}</span>
              <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${e.scoredHome ? P.home : P.away};margin-right:8px"></span>${e.team} scores</span>
              <span style="font-weight:700"><span style="color:var(--away)">${e.away}</span> — <span style="color:var(--home)">${e.home}</span></span>
            </div>`).join('')}
        </div>
        <p class="note">Demo sequence reconstructed to the final score. Real per-throw events come from the extraction pipeline.</p>
      </div>
    </div>`;
}

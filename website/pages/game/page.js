/* Game detail shell: matchup hero + Gamecast/Box Score/Play-by-Play tabs. */
import { initTabs } from '../../js/components.js';

export const tabs = (params) => ([
  { key: 'gamecast',   label: 'Gamecast',     href: `#/schedule/${params.id}/gamecast` },
  { key: 'boxscore',   label: 'Box Score',    href: `#/schedule/${params.id}/boxscore` },
  { key: 'playbyplay', label: 'Play-by-Play', href: `#/schedule/${params.id}/playbyplay` },
]);

export async function render(view, ctx){
  const games = await ctx.api.getGames();
  const g = games.find(x => x.id === ctx.params.id) || { home:'?', away:'?', homeScore:0, awayScore:0, date:'', week:'' };
  const hWin = g.homeScore > g.awayScore, aWin = g.awayScore > g.homeScore;

  const hero = document.createElement('section');
  hero.className = 'hero';
  hero.style.background = 'linear-gradient(90deg,rgba(74,127,181,.08) 0%,transparent 40%,transparent 60%,rgba(232,168,56,.08) 100%)';
  hero.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:center;gap:24px;max-width:820px;margin:0 auto">
      <div style="flex:1;text-align:right">
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim)">Away</div>
        <div style="font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:clamp(22px,4vw,34px);text-transform:uppercase">${g.away}</div>
      </div>
      <div style="font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:clamp(40px,8vw,72px);color:var(--away)">${g.awayScore}</div>
      <div style="text-align:center;min-width:90px">
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--lime);border:1px solid rgba(198,255,61,.3);padding:4px 14px;border-radius:20px;background:rgba(198,255,61,.06)">${g.status || 'Final'}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);margin-top:8px">${g.date}<br>Week ${g.week}</div>
      </div>
      <div style="font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:clamp(40px,8vw,72px);color:var(--home)">${g.homeScore}</div>
      <div style="flex:1;text-align:left">
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim)">Home</div>
        <div style="font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:clamp(22px,4vw,34px);text-transform:uppercase">${g.home}</div>
      </div>
    </div>`;

  const tabsEl = document.createElement('nav');
  initTabs(tabsEl, tabs(ctx.params), ctx.tab);

  const content = document.createElement('div');
  content.className = 'tab-content';
  view.append(hero, tabsEl, content);
  return content;
}

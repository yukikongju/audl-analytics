/* Prediction page (tabless): pick two teams, predict win probability
   from their strength (SS) ratings via a logistic on the rating gap. */
import { renderHero } from '../../js/components.js';
import { P } from '../../js/theme.js';

export async function render(view, ctx){
  const teams = await ctx.api.getTeams();
  let aId = teams[0].id, bId = teams[1].id;

  const hero = document.createElement('section');
  renderHero(hero, { type: 'simple', data: { eyebrow: 'Matchup model', title: 'Predict' } });

  const body = document.createElement('div');
  const opts = (sel) => teams.map(t => `<option value="${t.id}"${t.id === sel ? ' selected' : ''}>${t.city} ${t.name}</option>`).join('');
  body.innerHTML = `
    <div class="controls">
      <div class="ctrl-group"><label>Home</label><select id="pA">${opts(aId)}</select></div>
      <div class="spacer"></div>
      <div class="ctrl-group"><label>Away</label><select id="pB">${opts(bId)}</select></div>
    </div>
    <div class="content" style="grid-template-columns:1fr"><div class="card"><div id="pred"></div></div></div>`;

  view.append(hero, body);
  const A = body.querySelector('#pA'), B = body.querySelector('#pB'), out = body.querySelector('#pred');
  A.addEventListener('change', () => { aId = A.value; draw(); });
  B.addEventListener('change', () => { bId = B.value; draw(); });

  function draw(){
    const a = teams.find(t => t.id === aId), b = teams.find(t => t.id === bId);
    // logistic on the strength gap (+ small home edge)
    const gap = (a.ss - b.ss) + 0.4;
    const pa = Math.round(100 / (1 + Math.exp(-gap / 3)));
    const pb = 100 - pa;
    out.innerHTML = `
      <div style="display:flex;justify-content:space-between;font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:20px;text-transform:uppercase;margin-bottom:10px">
        <span>${a.name}</span><span>${b.name}</span>
      </div>
      <div style="display:flex;height:34px;border-radius:6px;overflow:hidden;font-family:'JetBrains Mono',monospace;font-weight:700">
        <div style="flex:${pa};background:${P.home};display:flex;align-items:center;justify-content:flex-start;padding:0 12px;color:#0A0E14">${pa}%</div>
        <div style="flex:${pb};background:${P.away};display:flex;align-items:center;justify-content:flex-end;padding:0 12px;color:#0A0E14">${pb}%</div>
      </div>
      <div style="display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);margin-top:14px">
        <span>SS ${a.ss > 0 ? '+' : ''}${a.ss.toFixed(2)}</span>
        <span>Projected: ${a.scoreFor.toFixed(0)}–${b.scoreFor.toFixed(0)}</span>
        <span>SS ${b.ss > 0 ? '+' : ''}${b.ss.toFixed(2)}</span>
      </div>
      <p class="note">Win probability from a logistic on the strength-rating gap plus a small home-field edge. Illustrative model.</p>`;
  }
  draw();
  return null;
}

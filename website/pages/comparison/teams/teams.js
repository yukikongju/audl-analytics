/* Comparison → Teams: pick two teams, compare ratings side by side. */

const STATS = [
  { key:'winPct', label:'Win %', fmt:v => v.toFixed(3) },
  { key:'ss', label:'SS Rk', fmt:v => (v > 0 ? '+' : '') + v.toFixed(2) },
  { key:'scoreFor', label:'Score For', fmt:v => v.toFixed(1) },
  { key:'scoreAgainst', label:'Score Against', fmt:v => v.toFixed(1), lowerBetter:true },
  { key:'oe', label:'O-Line Eff', fmt:v => v.toFixed(1) + '%' },
  { key:'de', label:'D-Line Eff', fmt:v => v.toFixed(1) + '%' },
  { key:'turnovers', label:'Turnovers', fmt:v => v.toFixed(1), lowerBetter:true },
  { key:'blocks', label:'Blocks', fmt:v => v.toFixed(1) },
  { key:'aec', label:'aEC', fmt:v => v.toFixed(1) },
];

export async function init(content, ctx){
  const teams = await ctx.api.getTeams();
  let aId = teams[0].id, bId = teams[1].id;

  const opts = (sel) => teams.map(t => `<option value="${t.id}"${t.id === sel ? ' selected' : ''}>${t.city} ${t.name}</option>`).join('');
  content.innerHTML = `
    <div class="controls">
      <div class="ctrl-group"><label>Team A</label><select id="cmpA">${opts(aId)}</select></div>
      <div class="spacer"></div>
      <div class="ctrl-group"><label>Team B</label><select id="cmpB">${opts(bId)}</select></div>
    </div>
    <div class="content" style="grid-template-columns:1fr"><div class="card"><div id="cmp"></div></div></div>`;

  const A = content.querySelector('#cmpA'), B = content.querySelector('#cmpB'), out = content.querySelector('#cmp');
  A.addEventListener('change', () => { aId = A.value; draw(); });
  B.addEventListener('change', () => { bId = B.value; draw(); });

  function draw(){
    const a = teams.find(t => t.id === aId), b = teams.find(t => t.id === bId);
    out.innerHTML = STATS.map(s => {
      const av = a[s.key], bv = b[s.key];
      const aWin = s.lowerBetter ? av < bv : av > bv;
      const bWin = s.lowerBetter ? bv < av : bv > av;
      return `<div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:9px 0;border-bottom:1px solid var(--line);font-family:'JetBrains Mono',monospace;font-size:13px">
        <span style="text-align:right;font-weight:700;color:${aWin ? 'var(--lime)' : 'var(--text)'}">${s.fmt(av)}</span>
        <span style="color:var(--dim);font-size:10px;text-transform:uppercase;letter-spacing:.06em;padding:0 20px">${s.label}</span>
        <span style="font-weight:700;color:${bWin ? 'var(--lime)' : 'var(--text)'}">${s.fmt(bv)}</span>
      </div>`;
    }).join('');
  }
  draw();
}

/* Comparison → Players: pick two players, compare stat lines side by side. */

const STATS = [
  { key:'aec', label:'Tot-aEC' }, { key:'taec', label:'T-aEC' }, { key:'raec', label:'R-aEC' },
  { key:'g', label:'Goals' }, { key:'a', label:'Assists' }, { key:'c', label:'Completions' },
  { key:'t', label:'Turns', lowerBetter:true }, { key:'b', label:'Blocks' },
  { key:'cp', label:'CP%' }, { key:'hu', label:'Huck Rate' }, { key:'xcp', label:'xCP' }, { key:'gp', label:'GP' },
];

export async function init(content, ctx){
  const players = await ctx.api.getPlayers();
  let aId = players[0].id, bId = players[1].id;

  const opts = (sel) => players.map(p => `<option value="${p.id}"${p.id === sel ? ' selected' : ''}>${p.name}</option>`).join('');
  content.innerHTML = `
    <div class="controls">
      <div class="ctrl-group"><label>Player A</label><select id="cmpA">${opts(aId)}</select></div>
      <div class="spacer"></div>
      <div class="ctrl-group"><label>Player B</label><select id="cmpB">${opts(bId)}</select></div>
    </div>
    <div class="content" style="grid-template-columns:1fr"><div class="card"><div id="cmp"></div></div></div>`;

  const A = content.querySelector('#cmpA'), B = content.querySelector('#cmpB'), out = content.querySelector('#cmp');
  A.addEventListener('change', () => { aId = A.value; draw(); });
  B.addEventListener('change', () => { bId = B.value; draw(); });

  function draw(){
    const a = players.find(p => p.id === aId), b = players.find(p => p.id === bId);
    out.innerHTML = STATS.map(s => {
      const av = a[s.key], bv = b[s.key];
      const aWin = s.lowerBetter ? av < bv : av > bv;
      const bWin = s.lowerBetter ? bv < av : bv > av;
      return `<div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:9px 0;border-bottom:1px solid var(--line);font-family:'JetBrains Mono',monospace;font-size:13px">
        <span style="text-align:right;font-weight:700;color:${aWin ? 'var(--lime)' : 'var(--text)'}">${av}</span>
        <span style="color:var(--dim);font-size:10px;text-transform:uppercase;letter-spacing:.06em;padding:0 20px">${s.label}</span>
        <span style="font-weight:700;color:${bWin ? 'var(--lime)' : 'var(--text)'}">${bv}</span>
      </div>`;
    }).join('');
  }
  draw();
}

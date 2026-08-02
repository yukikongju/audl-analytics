/* throw-field.js — the throw-chart canvas engine.
   Ported from inspiration/throwing.html and parameterized: it mounts
   the whole throw-chart UI (filters + field + side stats) into a given
   container and takes its throws as data. Largest reused asset; kept
   colocated with the Throwing tab (single consumer for now). */
import { P } from '../../../js/theme.js';
import { noise, clamp } from '../../../js/util.js';

const COLS = 10, EZ_R = 5, FIELD_R = 14, TOT_R = EZ_R + FIELD_R + EZ_R;
const CW = 42, CH = 28, FW = COLS * CW, FH = TOT_R * CH;
const TYPES = ['pass', 'dump', 'swing', 'huck'];
const TC = {
  pass:  { label:'Pass',  color:P.lime,   desc:'Forward to a cutter' },
  dump:  { label:'Dump',  color:P.blue,   desc:'Short reset backward' },
  swing: { label:'Swing', color:P.purple, desc:'Lateral cross-field' },
  huck:  { label:'Huck',  color:P.orange, desc:'Deep bomb downfield' },
};
const yAt = (r) => r * CH;
const EZ_TOP = yAt(EZ_R), EZ_BOT = yAt(EZ_R + FIELD_R);
const BRICK_T = yAt(EZ_R + 4), BRICK_B = yAt(EZ_R + FIELD_R - 4), MID = yAt(EZ_R + 7);

/** Deterministic demo throws for a player (seeded). Swap for api later. */
export function generateThrows(seed, num = 620){
  const sn = (i, k) => noise(i, k, seed);
  const throws = [];
  for (let i = 0; i < num; i++){
    const r0 = sn(i, 0), r1 = sn(i, 1), r2 = sn(i, 2), r3 = sn(i, 3), r4 = sn(i, 4), r5 = sn(i, 5), r6 = sn(i, 6), r7 = sn(i, 7);
    let y;
    if (r0 < 0.06) y = r1 * EZ_TOP;
    else if (r0 > 0.93) y = EZ_BOT + r1 * (FH - EZ_BOT);
    else y = EZ_TOP + ((r1 + r2 + r3) / 3) * (EZ_BOT - EZ_TOP);
    const x = clamp(((r4 + r5) / 2) * FW, 3, FW - 3);
    const yn = y / FH, edge = Math.abs(x / FW - 0.5) * 2;
    let wP = 24 + 22 * (1 - edge * 0.35) * (1 - Math.abs(yn - 0.4) * 1.4);
    let wD = 10 + 22 * yn * (1 + edge * 0.2);
    let wS = 8 + 20 * edge * (1 - yn * 0.15);
    let wH = 3 + 16 * Math.max(0, yn - 0.28) * (1 - edge * 0.5);
    const roll = r6 * (wP + wD + wS + wH);
    const type = roll < wP ? 'pass' : roll < wP + wD ? 'dump' : roll < wP + wD + wS ? 'swing' : 'huck';
    let cp = type === 'pass' ? 83 + 12 * (1 - edge * 0.3) - yn * 5
      : type === 'dump' ? 89 + 7 * (1 - edge * 0.2)
      : type === 'swing' ? 73 + 14 * (1 - edge * 0.5)
      : 43 + 20 * (1 - edge * 0.5) - yn * 8;
    cp = clamp(cp + (r7 - 0.5) * 14, 20, 99);
    throws.push({ x, y, type, completed: sn(i, 8) * 100 < cp });
  }
  return throws;
}

const HTML = `
  <div class="sec-head" style="display:flex;align-items:baseline;justify-content:space-between;margin:0 5vw 24px;gap:16px;flex-wrap:wrap">
    <div><span style="font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.16em;color:var(--orange);text-transform:uppercase;display:block;margin-bottom:4px">Decision + Completion</span>
      <h2 style="font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:clamp(24px,4vw,36px);text-transform:uppercase;letter-spacing:.02em">Throw Chart</h2></div>
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
      <div class="pills" data-role="type"></div>
      <div class="pills" data-role="result" style="padding-left:16px;border-left:1px solid var(--line)"></div>
    </div>
  </div>
  <div class="content" style="grid-template-columns:auto 1fr">
    <div class="card">
      <div class="card-hd"><h3>Throw Chart</h3><span class="tag" data-role="count">0 throws</span></div>
      <div class="field-wrap" data-role="fieldwrap" style="position:relative;display:inline-block">
        <div data-role="fieldbox" style="position:relative;overflow:hidden">
          <div style="position:absolute;inset:0;background:linear-gradient(180deg,#102a1a 0%,#163822 50%,#102a1a 100%)"></div>
          <div data-role="mows"></div>
          <div data-role="eztTop" style="position:absolute;left:0;right:0;background:rgba(0,0,0,.1);pointer-events:none"></div>
          <div data-role="eztBot" style="position:absolute;left:0;right:0;background:rgba(0,0,0,.1);pointer-events:none"></div>
          <canvas data-role="canvas" style="position:absolute;inset:0;z-index:12"></canvas>
          <svg data-role="svg" style="position:absolute;inset:0;z-index:20;pointer-events:none"></svg>
        </div>
        <div class="tip" data-role="tip"></div>
      </div>
      <div class="legend" data-role="legend"></div>
      <p class="note">Each dot is one throw attempt. Hover a region to see zone stats. Filter by throw type above.</p>
    </div>
    <div style="display:flex;flex-direction:column;gap:18px">
      <div class="card" data-role="summary"></div>
      <div class="card" data-role="volume"></div>
    </div>
  </div>`;

/** Mount the throw-chart UI into `container` with the given `throws`. */
export function mountThrowField(container, throws){
  container.innerHTML = HTML;
  const q = (r) => container.querySelector(`[data-role="${r}"]`);
  const fieldBox = q('fieldbox'), fieldWrap = q('fieldwrap');
  const canvas = q('canvas'), ctx = canvas.getContext('2d');
  const tip = q('tip');
  let filter = 'all', showMade = true, showMiss = true;

  // field geometry
  fieldBox.style.width = FW + 'px'; fieldBox.style.height = FH + 'px';
  canvas.width = FW; canvas.height = FH;
  let mows = '';
  for (let i = 0; i < 12; i++)
    mows += `<div style="position:absolute;left:0;right:0;pointer-events:none;top:${yAt(i * 2)}px;height:${CH * 2}px;background:${i % 2 ? 'rgba(0,0,0,.015)' : 'rgba(255,255,255,.015)'}"></div>`;
  q('mows').innerHTML = mows;
  q('eztTop').style.cssText = `position:absolute;left:0;right:0;top:0;height:${EZ_TOP}px;background:rgba(0,0,0,.1)`;
  q('eztBot').style.cssText = `position:absolute;left:0;right:0;top:${EZ_BOT}px;bottom:0;background:rgba(0,0,0,.1)`;

  // field lines
  const svg = q('svg');
  svg.setAttribute('width', FW); svg.setAttribute('height', FH); svg.setAttribute('viewBox', `0 0 ${FW} ${FH}`);
  const lc = 'rgba(255,255,255,.5)', fc = 'rgba(255,255,255,.12)', cx = FW / 2, bk = 8;
  let s = `<rect x="1" y="1" width="${FW - 2}" height="${FH - 2}" fill="none" stroke="${lc}" stroke-width="2"/>`;
  s += `<line x1="0" y1="${EZ_TOP}" x2="${FW}" y2="${EZ_TOP}" stroke="${lc}" stroke-width="2.5"/>`;
  s += `<line x1="0" y1="${EZ_BOT}" x2="${FW}" y2="${EZ_BOT}" stroke="${lc}" stroke-width="2.5"/>`;
  for (let i = 1; i <= 13; i++) s += `<line x1="0" y1="${yAt(EZ_R + i)}" x2="${FW}" y2="${yAt(EZ_R + i)}" stroke="${fc}" stroke-width=".75"/>`;
  s += `<line x1="0" y1="${MID}" x2="${FW}" y2="${MID}" stroke="rgba(255,255,255,.28)" stroke-width="1.5" stroke-dasharray="8 5"/>`;
  [BRICK_T, BRICK_B].forEach(by => {
    s += `<rect x="${cx - bk}" y="${by - bk}" width="${bk * 2}" height="${bk * 2}" fill="none" stroke="${lc}" stroke-width="1.5"/>`;
    s += `<line x1="${cx - bk}" y1="${by}" x2="${cx + bk}" y2="${by}" stroke="${lc}" stroke-width="1"/>`;
    s += `<line x1="${cx}" y1="${by - bk}" x2="${cx}" y2="${by + bk}" stroke="${lc}" stroke-width="1"/>`;
  });
  s += `<text x="${cx}" y="${EZ_TOP / 2 + 1}" text-anchor="middle" dominant-baseline="central" fill="rgba(255,255,255,.18)" font-size="11" font-weight="700" letter-spacing=".2em" font-family="'Barlow Condensed',sans-serif">ATTACKING ENDZONE</text>`;
  s += `<text x="${cx}" y="${EZ_BOT + (FH - EZ_BOT) / 2 + 1}" text-anchor="middle" dominant-baseline="central" fill="rgba(255,255,255,.18)" font-size="11" font-weight="700" letter-spacing=".2em" font-family="'Barlow Condensed',sans-serif">DEFENDING ENDZONE</text>`;
  [0, 10, 20, 30, 40, 50, 60, 70].forEach(yd => {
    const yy = EZ_TOP + (yd / 70) * (FIELD_R * CH);
    s += `<line x1="0" y1="${yy}" x2="6" y2="${yy}" stroke="rgba(255,255,255,.35)" stroke-width="1.5"/>`;
    s += `<text x="10" y="${yy + 1}" dominant-baseline="central" fill="rgba(255,255,255,.3)" font-size="8" font-weight="600" font-family="'JetBrains Mono',monospace">${yd}</text>`;
  });
  svg.innerHTML = s;

  function drawDots(){
    ctx.clearRect(0, 0, FW, FH);
    let vis = throws.filter(t => filter === 'all' || t.type === filter);
    if (!showMade) vis = vis.filter(t => !t.completed);
    if (!showMiss) vis = vis.filter(t => t.completed);
    [...vis].sort((a, b) => (a.completed ? 1 : 0) - (b.completed ? 1 : 0)).forEach(t => {
      const col = TC[t.type].color;
      if (t.completed){
        ctx.beginPath(); ctx.arc(t.x, t.y, 3.2, 0, Math.PI * 2);
        ctx.globalAlpha = 0.85; ctx.fillStyle = col; ctx.fill();
        ctx.globalAlpha = 0.3; ctx.strokeStyle = '#000'; ctx.lineWidth = 0.8; ctx.stroke();
      } else {
        const sz = 3.2; ctx.globalAlpha = 0.85; ctx.strokeStyle = col; ctx.lineWidth = 1.8; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(t.x - sz, t.y - sz); ctx.lineTo(t.x + sz, t.y + sz);
        ctx.moveTo(t.x + sz, t.y - sz); ctx.lineTo(t.x - sz, t.y + sz); ctx.stroke();
      }
    });
    ctx.globalAlpha = 1; ctx.lineCap = 'butt';
    q('count').textContent = vis.length + ' throws';
  }

  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) * (FW / rect.width);
    const my = (e.clientY - rect.top) * (FH / rect.height);
    const nearby = throws.filter(t => {
      if (filter !== 'all' && t.type !== filter) return false;
      if (!showMade && t.completed) return false;
      if (!showMiss && !t.completed) return false;
      return Math.hypot(t.x - mx, t.y - my) < 22;
    });
    if (nearby.length < 2){ tip.classList.remove('on'); return; }
    const counts = {}, made = {};
    TYPES.forEach(t => { counts[t] = 0; made[t] = 0; });
    nearby.forEach(t => { counts[t.type]++; if (t.completed) made[t.type]++; });
    const total = nearby.length, totalMade = nearby.filter(t => t.completed).length;
    const zone = my < EZ_TOP ? 'Attacking EZ' : my > EZ_BOT ? 'Defending EZ' : Math.round(((my - EZ_TOP) / (EZ_BOT - EZ_TOP)) * 70) + ' yd line';
    let rows = '';
    TYPES.forEach(t => {
      if (!counts[t]) return;
      const pct = Math.round(made[t] / counts[t] * 100);
      rows += `<div class="row"><span><span class="dot" style="background:${TC[t].color}"></span>${TC[t].label} ${counts[t]}</span><span style="color:${pct >= 70 ? P.lime : pct >= 50 ? P.orange : P.red}">${pct}%</span></div>`;
    });
    tip.innerHTML = `<div class="tl">${zone}</div><div class="ts">${total} throws nearby · ${Math.round(totalMade / total * 100)}% completion</div><div class="tv">${rows}</div>`;
    const fr = fieldWrap.getBoundingClientRect();
    let left = e.clientX - fr.left + 14, top = e.clientY - fr.top - 60;
    if (left + 210 > fr.width) left = e.clientX - fr.left - 214;
    if (top < 0) top = e.clientY - fr.top + 14;
    tip.style.left = left + 'px'; tip.style.top = top + 'px';
    tip.classList.add('on');
  });
  canvas.addEventListener('mouseleave', () => tip.classList.remove('on'));

  function renderLegend(){
    let h = TYPES.map(t => `<span class="gi"><span class="gd" style="background:${TC[t].color}"></span>${TC[t].label}</span>`).join('');
    h += `<span class="gi" style="margin-left:8px;padding-left:12px;border-left:1px solid var(--line)">● complete</span><span class="gi">✕ turnover</span>`;
    q('legend').innerHTML = h;
  }

  function renderStats(){
    const vis = throws.filter(t => filter === 'all' || t.type === filter);
    const totalMade = vis.filter(t => t.completed).length;
    const totalPct = vis.length ? Math.round(totalMade / vis.length * 100) : 0;
    const col = totalPct >= 75 ? P.lime : totalPct >= 55 ? P.orange : P.red;
    const lbl = filter === 'all' ? 'Overall' : TC[filter].label;
    let html = `<div class="card-hd"><h3>Throw Breakdown</h3><span class="tag">season</span></div>`;
    html += `<div class="big-stat"><div class="num" style="color:${col}">${totalPct}%</div><div class="lbl">${lbl} Completion</div></div>`;
    TYPES.forEach(t => {
      const sub = throws.filter(th => th.type === t);
      const cnt = sub.length, madeCnt = sub.filter(th => th.completed).length;
      const pct = cnt ? Math.round(madeCnt / cnt * 100) : 0;
      const barW = clamp((pct - 30) / 62 * 100, 2, 100);
      html += `<div style="margin-bottom:14px;opacity:${filter === 'all' || filter === t ? 1 : 0.3}">
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px">
          <div style="display:flex;align-items:center;gap:8px"><span style="width:8px;height:8px;border-radius:50%;background:${TC[t].color}"></span><span style="font-family:'Barlow Condensed',sans-serif;font-weight:600;text-transform:uppercase;font-size:14px;letter-spacing:.04em">${TC[t].label}</span></div>
          <span style="font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;color:var(--lime)">${pct}%</span>
        </div>
        <div style="height:4px;background:var(--panel-2);border-radius:2px;overflow:hidden"><div style="height:100%;border-radius:2px;width:${barW}%;background:linear-gradient(90deg,${P.orange},${TC[t].color})"></div></div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--dim);margin-top:4px">${TC[t].desc}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--dim);margin-top:2px">${madeCnt}/${cnt} completed</div>
      </div>`;
    });
    q('summary').innerHTML = html;

    const grand = throws.length;
    let vol = `<h3>Volume Split</h3><div style="display:flex;height:10px;border-radius:5px;overflow:hidden;margin-bottom:12px">`;
    TYPES.forEach(t => vol += `<div style="flex:${throws.filter(th => th.type === t).length};background:${TC[t].color}"></div>`);
    vol += `</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">`;
    TYPES.forEach(t => {
      const c = throws.filter(th => th.type === t).length;
      vol += `<div style="display:flex;align-items:center;gap:8px"><span style="width:8px;height:8px;border-radius:50%;background:${TC[t].color}"></span><span style="font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--text)">${Math.round(c / grand * 100)}%</span><span style="font-size:11px;color:var(--dim)">${TC[t].label}</span></div>`;
    });
    vol += `</div>`;
    q('volume').innerHTML = vol;
  }

  // filter pills
  q('type').innerHTML = `<button class="pill active" data-filter="all">ALL</button>` +
    TYPES.map(t => `<button class="pill" data-filter="${t}"><span class="d" style="background:${TC[t].color}"></span>${TC[t].label.toUpperCase()}</button>`).join('');
  q('result').innerHTML = `<button class="pill active" data-toggle="made"><span class="d" style="background:${P.lime}"></span>COMPLETED</button><button class="pill active" data-toggle="miss"><span class="d" style="background:${P.red}"></span>INCOMPLETE</button>`;

  q('type').addEventListener('click', (e) => {
    const b = e.target.closest('.pill'); if (!b) return;
    q('type').querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active'); filter = b.dataset.filter; render();
  });
  q('result').addEventListener('click', (e) => {
    const b = e.target.closest('.pill'); if (!b) return;
    if (b.dataset.toggle === 'made') showMade = !showMade; else showMiss = !showMiss;
    b.classList.toggle('active');
    drawDots();
  });

  function render(){ drawDots(); renderLegend(); renderStats(); }
  render();
}

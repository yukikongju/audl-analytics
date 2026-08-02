/* Schedule page (tabless) — reworked from inspiration/schedule.html.
   Hero + playoff strip (derived from standings), season/team/week filters,
   day-grouped game cards linking to each game's gamecast. */

// View metadata (presentation, not entity data): week date ranges + current week.
const WEEK_DATES = {
  1:'Apr 24 – Apr 26', 2:'May 1 – May 3', 3:'May 8 – May 10', 4:'May 15 – May 17',
  5:'May 23 – May 24', 6:'May 29 – May 31', 7:'Jun 5 – Jun 6', 8:'Jun 12 – Jun 14',
};
const CURRENT_WEEK = 5;
const DIV_FINALS = [
  { key:'east',    label:'East Final',    date:'Aug 8' },
  { key:'central', label:'Central Final', date:'Aug 8' },
  { key:'south',   label:'South Final',   date:'Aug 7' },
  { key:'west',    label:'West Final',    date:'' },
];
const PLAY = `<svg viewBox="0 0 10 10" width="10" height="10" fill="none" style="vertical-align:middle"><path d="M2 1l7 4-7 4V1z" fill="currentColor"/></svg>`;

export async function render(view, ctx){
  const [games, teams] = await Promise.all([ctx.api.getGames(), ctx.api.getTeams()]);
  const byAb = Object.fromEntries(teams.map(t => [t.ab, t]));
  const weeks = [...new Set(games.map(g => g.week))].sort((a, b) => a - b);
  let selWeek = 0, selTeam = '';

  // ── playoff strip: top-2 by SS within each division ──
  const finals = DIV_FINALS.map(d => {
    const seeded = teams.filter(t => t.div === d.key).sort((a, b) => b.ss - a.ss).slice(0, 2);
    return { ...d, seeded };
  }).filter(d => d.seeded.length === 2);

  // ── static shell ──
  const teamOpts = ['<option value="">All Teams</option>']
    .concat([...teams].sort((a, b) => a.name.localeCompare(b.name)).map(t => `<option value="${t.ab}">${t.city} ${t.name}</option>`))
    .join('');
  const weekPills = [`<button class="wpill active" data-week="0"><span class="wnum">All</span><span class="wdates">Weeks</span></button>`]
    .concat(weeks.map(w => `<button class="wpill${w === CURRENT_WEEK ? ' current' : ''}" data-week="${w}"><span class="wnum">Week ${w}</span><span class="wdates">${WEEK_DATES[w] || ''}</span><div class="dot"></div></button>`))
    .join('');

  view.innerHTML = `
    <section class="sched-hero">
      <div class="eyebrow">UFA · 2026 Season</div>
      <h1>Schedule</h1>
      <div class="accent-bar"></div>
      <div class="playoff">
        <div class="playoff-hd"><div class="title">UFA <em>Playoffs</em></div><div class="sub">Division Finals</div></div>
        ${finals.map(d => `<div class="po-game">
          <div class="po-label">${d.label}${d.date ? `<span class="date">${d.date}</span>` : ''}</div>
          ${d.seeded.map((t, i) => `<div class="po-row"><span class="seed">${i + 1}</span><span class="abr">${t.ab}</span><span class="sc">0</span></div>`).join('')}
        </div>`).join('')}
      </div>
    </section>
    <div class="filter-card">
      <div class="filter-top">
        <h2>Schedule</h2>
        <select id="seasonSel"><option>2026</option><option>2025</option></select>
        <div class="spacer"></div>
        <select class="team-select" id="teamSel">${teamOpts}</select>
      </div>
      <div class="week-strip" id="weekStrip">${weekPills}</div>
    </div>
    <div class="team-header" id="teamHeader">
      <div class="th-badge"><svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8" stroke="#E7EDF3" stroke-width="1.5"/></svg></div>
      <div class="th-info"><div class="label">Team Schedule</div><div class="name" id="thName">—</div></div>
    </div>
    <div class="game-count" id="gameCount"></div>
    <div class="game-list" id="gameList"></div>`;

  const weekStrip = view.querySelector('#weekStrip');
  const teamSel = view.querySelector('#teamSel');
  const teamHeader = view.querySelector('#teamHeader');

  function renderList(){
    let list = games.filter(g => selWeek === 0 || g.week === selWeek);
    if (selTeam) list = list.filter(g => g.home === selTeam || g.away === selTeam);

    if (selTeam){ teamHeader.classList.add('show'); view.querySelector('#thName').textContent = `${byAb[selTeam]?.city || ''} ${byAb[selTeam]?.name || selTeam}`; }
    else teamHeader.classList.remove('show');

    const days = {};
    list.forEach(g => { (days[g.day] = days[g.day] || []).push(g); });

    let html = '';
    Object.keys(days).forEach(day => {
      html += `<div class="day-header">${day}</div>`;
      days[day].forEach(g => {
        html += gameCard(g);
      });
    });
    view.querySelector('#gameList').innerHTML = list.length ? html : `<div class="no-games">No games found for this filter combination.</div>`;
    view.querySelector('#gameCount').textContent = `${list.length} game${list.length !== 1 ? 's' : ''}`;
  }

  function gameCard(g){
    const aWin = g.awayScore > g.homeScore, hWin = g.homeScore > g.awayScore;
    const at = byAb[g.away] || { name:g.away, record:'', color:'#555' };
    const ht = byAb[g.home] || { name:g.home, record:'', color:'#555' };
    const row = (t, score, win) => `<div class="trow ${win ? 'winner' : 'loser'}">
        <div class="bar" style="background:${t.color}"></div>
        <span class="tname">${t.name}</span><span class="rec">${t.record || ''}</span>
        <span class="arrow">◂</span>
        <span class="gscore">${score}</span>
      </div>`;
    return `<a class="gcard" href="#/schedule/${g.id}/gamecast">
      <div class="teams">${row(at, g.awayScore, aWin)}${row(ht, g.homeScore, hWin)}</div>
      <div class="gmeta"><div class="badge">${g.status}</div><div class="gdate">${g.date}</div><div class="gtime">${g.time}</div></div>
      <div class="gcta">${PLAY} Gamecast →</div>
    </a>`;
  }

  weekStrip.addEventListener('click', (e) => {
    const b = e.target.closest('.wpill'); if (!b) return;
    weekStrip.querySelectorAll('.wpill').forEach(x => x.classList.remove('active'));
    b.classList.add('active'); selWeek = +b.dataset.week; renderList();
  });
  teamSel.addEventListener('change', () => { selTeam = teamSel.value; renderList(); });

  renderList();
  return null;
}

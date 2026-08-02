/* ═══════════════════════════════════════════════════════════
   components.js — shared chrome rendered by the shell/router.
   renderNav / renderTicker / renderHero / initTabs.
   All links are REAL hash routes (the mockups' dead buttons are
   replaced here) so navigation actually works.
   ═══════════════════════════════════════════════════════════ */

import { P } from './theme.js';

const LOGO = `<svg width="28" height="28" viewBox="0 0 28 28" fill="none">
  <rect x="1" y="1" width="26" height="26" rx="3" stroke="rgba(255,255,255,.3)" stroke-width="1.5"/>
  <ellipse cx="14" cy="14" rx="9" ry="4.5" stroke="#E7EDF3" stroke-width="1.2" transform="rotate(-15 14 14)"/>
  <circle cx="14" cy="14" r="2.5" fill="#FF6A2B"/></svg>`;
const CHEV = `<svg class="chev" width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`;
const AV = `<svg width="60" height="80" viewBox="0 0 60 80" fill="none"><circle cx="30" cy="22" r="14" stroke="#E7EDF3" stroke-width="2"/><path d="M8 72c0-12 10-22 22-22s22 10 22 22" stroke="#E7EDF3" stroke-width="2"/></svg>`;
const LOGO_TEAM = `<svg width="50" height="50" viewBox="0 0 50 50" fill="none"><circle cx="25" cy="25" r="18" stroke="#E7EDF3" stroke-width="2"/><path d="M25 10v30M13 17l24 16M13 33l24-16" stroke="#E7EDF3" stroke-width="1.5"/></svg>`;

/* Primary nav — real routes. `match` is the path prefix that marks it active.
   Leaderboard is its own page; Players/Teams open the featured profile (the
   bare #/players and #/teams routes redirect to the top-ranked entity). */
export const NAV_ITEMS = [
  { label: 'Leaderboard', href: '#/leaderboard/players', match: '/leaderboard' },
  { label: 'Schedule',    href: '#/schedule',            match: '/schedule' },
  { label: 'Players',     href: '#/players',             match: '/players' },
  { label: 'Teams',       href: '#/teams',               match: '/teams' },
  { label: 'Compare',     href: '#/comparison/players',  match: '/comparison' },
  { label: 'Predict',     href: '#/prediction',          match: '/prediction' },
  { label: 'About',       href: '#/about',               match: '/about' },
];

/** Render the top nav into `mount`. Primary items are anchors; burger toggles a dropdown. */
export function renderNav(mount){
  mount.className = 'nav';
  mount.innerHTML = `
    <a class="nav-logo" href="#/"> ${LOGO} <div class="wm">Disc<br><em>Space.</em></div></a>
    <nav class="nav-links">
      ${NAV_ITEMS.slice(0, 4).map(i =>
        `<a class="nav-link" href="${i.href}" data-match="${i.match}">${i.label}${CHEV}</a>`).join('')}
      <button class="nav-burger" aria-label="Menu">
        <svg width="18" height="12" viewBox="0 0 18 12" fill="none">
          <line x1="0" y1="1" x2="18" y2="1" stroke="#E7EDF3" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="0" y1="6" x2="18" y2="6" stroke="#E7EDF3" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="0" y1="11" x2="18" y2="11" stroke="#E7EDF3" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
    </nav>`;

  // Burger dropdown: full nav list (simple menu, closes on outside click)
  const burger = mount.querySelector('.nav-burger');
  burger.addEventListener('click', (e) => {
    e.stopPropagation();
    let menu = mount.querySelector('.nav-menu');
    if (menu){ menu.remove(); return; }
    menu = document.createElement('div');
    menu.className = 'nav-menu';
    menu.style.cssText = 'position:absolute;top:52px;right:5vw;background:var(--panel);border:1px solid var(--line);border-radius:4px;z-index:70;min-width:160px;overflow:hidden;';
    menu.innerHTML = NAV_ITEMS.map(i =>
      `<a href="${i.href}" style="display:block;padding:10px 16px;color:var(--dim);text-decoration:none;font-family:'Barlow Condensed',sans-serif;font-weight:600;text-transform:uppercase;letter-spacing:.04em;font-size:14px;border-bottom:1px solid var(--line)">${i.label}</a>`).join('');
    mount.appendChild(menu);
    const close = () => { menu.remove(); document.removeEventListener('click', close); };
    setTimeout(() => document.addEventListener('click', close), 0);
  });
}

/** Highlight the primary nav item matching the current path. */
export function setActiveNav(path){
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', path.startsWith(a.dataset.match));
  });
}

/** Score ticker — each game links to its gamecast. */
export function renderTicker(mount, games, { highlight } = {}){
  mount.className = 'ticker';
  mount.innerHTML = games.map(g => {
    const aWin = g.awayScore > g.homeScore, hWin = g.homeScore > g.awayScore;
    const hi = ab => highlight && ab === highlight ? ' win' : '';
    return `<a class="game" href="#/schedule/${g.id}/gamecast">
      <span class="team">${g.away}</span><span></span><span class="score${aWin ? hi(g.away) || ' win' : ''}">${g.awayScore}</span>
      <span class="team">${g.home}</span><span></span><span class="score${hWin ? hi(g.home) || ' win' : ''}">${g.homeScore}</span>
      <div class="badge"><b>${g.status || 'Final'}</b> ${g.date || ''}</div>
    </a>`;
  }).join('');
}

/** Hero. type: 'player' | 'team' | 'simple'. data shape varies by type. */
export function renderHero(mount, { type, data }){
  mount.className = type === 'simple' ? 'hero simple' : 'hero';
  if (type === 'player'){
    mount.innerHTML = `
      <span class="ghost">${data.number ?? ''}</span>
      <div class="hero-inner">
        <div class="avatar">${AV}</div>
        <div class="hero-info">
          <div class="eyebrow">Player Profile</div>
          <h1>${data.name}${data.number != null ? `<span class="num">#${data.number}</span>` : ''}</h1>
          <div class="team-line">
            <span class="tn">${data.team ?? ''}</span>
            ${data.line ? `<span class="sep">·</span>${data.line}` : ''}
            ${data.position ? `<span class="sep">·</span>${data.position}` : ''}
          </div>
          ${data.bio ? `<div class="bio">${data.bio.map(b => `<span>${b}</span>`).join('')}</div>` : ''}
          ${data.accolades ? `<div class="accolades">${data.accolades.map(a => `<span class="acc">${a}</span>`).join('')}</div>` : ''}
        </div>
      </div>`;
  } else if (type === 'team'){
    mount.innerHTML = `
      <span class="ghost">${data.name}</span>
      <div class="hero-inner">
        <div class="team-logo">${LOGO_TEAM}</div>
        <div class="hero-info">
          <div class="city">${data.city ?? ''}</div>
          <h1>${data.name}</h1>
          <div class="team-meta">
            ${data.record ? `<span class="record">${data.record}</span>` : ''}
            ${(data.stats || []).map(s => `<span class="team-stat">${s.label} <b>${s.value}</b></span>`).join('<span class="sep">·</span>')}
            ${data.social ? `<span class="social">${data.social}</span>` : ''}
          </div>
        </div>
      </div>`;
  } else {
    mount.innerHTML = `
      <div class="ey" style="font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.14em;color:var(--dim);text-transform:uppercase;margin-bottom:6px">${data.eyebrow ?? ''}</div>
      <h1 style="font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:clamp(48px,9vw,88px);text-transform:uppercase;letter-spacing:.02em;line-height:.92">${data.title}</h1>
      <div class="bar"></div>`;
  }
}

/**
 * Render a tab strip as real route anchors and mark the active one.
 * tabs: [{ key, label, href }]. activeKey: which tab is active.
 */
export function initTabs(mount, tabs, activeKey){
  mount.className = 'tabs';
  mount.innerHTML = tabs.map((t, i) =>
    `<a class="tab${t.key === activeKey ? ' active' : ''}" href="${t.href}" data-key="${t.key}">
       <span class="idx">${String(i + 1).padStart(2, '0')}</span>${t.label}
     </a>`).join('');
}

/** Toggle the active tab in an already-rendered strip (no re-render). */
export function setActiveTab(mount, activeKey){
  mount.querySelectorAll('.tab').forEach(a =>
    a.classList.toggle('active', a.dataset.key === activeKey));
}

/**
 * Profile controls bar (Season / optional Stat View / Find search).
 * Rendered once in a page shell so it persists across that page's tabs.
 *  opts.statView   — include the Total/Per Game/Per Point select
 *  opts.findLabel  — label for the search box (e.g. "Find Player")
 *  opts.entities   — [{ id, label }] to search over (a datalist)
 *  opts.onFind(id) — called when a listed entity is chosen
 */
export function renderControls(mount, { statView = false, findLabel = 'Search', entities = [], onFind } = {}){
  mount.className = 'controls';
  mount.innerHTML = `
    <div class="ctrl-group"><label>Season</label><select><option>2026</option><option>2025</option><option>2024</option></select></div>
    ${statView ? `<div class="ctrl-group"><label>Stat View</label><select><option>Total</option><option>Per Game</option><option>Per Point</option></select></div>` : ''}
    <div class="spacer"></div>
    <div class="ctrl-group"><label>${findLabel}</label>
      <input type="text" class="find-input" list="find-list" placeholder="Search…">
      <datalist id="find-list">${entities.map(e => `<option value="${e.label}"></option>`).join('')}</datalist>
    </div>`;
  const input = mount.querySelector('.find-input');
  input.addEventListener('change', () => {
    const m = entities.find(e => e.label.toLowerCase() === input.value.trim().toLowerCase());
    if (m && onFind) onFind(m.id);
  });
}

/* ═══════════════════════════════════════════════════════════
   app.js — client-side shell: hash router + page/tab loader.

   Model:
   - A route resolves to { page, params, tab }.
   - Each page module (pages/<page>/page.js) exports:
       async render(view, ctx) -> returns the tab-content element
                                   (or null for tabless pages).
       tabs?(params) -> [{key,label,href}]  (optional)
   - Each tab module (pages/<page>/<tab>/<tab>.js) exports:
       async init(contentEl, ctx)
   - Switching tabs of the SAME page+params only reloads the tab
     module into the existing content element (hero/nav untouched).
   ═══════════════════════════════════════════════════════════ */

import { api } from './api.js';
import { renderNav, setActiveNav, setActiveTab } from './components.js';

/* ─── route table ─────────────────────────────────────────── */
const ROUTES = [
  { page:'leaderboard', re:/^\/leaderboard\/(players|teams)$/,                     parse:m => ({ tab:m[1], params:{} }) },
  { page:'players',     re:/^\/players\/([^/]+)\/(stats|throwing)$/,               parse:m => ({ tab:m[2], params:{ id:m[1] } }) },
  { page:'teams',       re:/^\/teams\/([^/]+)\/(stats|roster)$/,                   parse:m => ({ tab:m[2], params:{ id:m[1] } }) },
  { page:'game',        re:/^\/schedule\/([^/]+)\/(gamecast|boxscore|playbyplay)$/, parse:m => ({ tab:m[2], params:{ id:m[1] } }) },
  { page:'schedule',    re:/^\/schedule$/,                                         parse:() => ({ tab:null, params:{} }) },
  { page:'comparison',  re:/^\/comparison\/(players|teams)$/,                      parse:m => ({ tab:m[1], params:{} }) },
  { page:'prediction',  re:/^\/prediction$/,                                       parse:() => ({ tab:null, params:{} }) },
  { page:'about',       re:/^\/about$/,                                            parse:() => ({ tab:null, params:{} }) },
];

const DEFAULT_ROUTE = '#/leaderboard/players';
const view = document.getElementById('view');

/* Bare section routes redirect to the featured (top-ranked) entity's profile,
   since a profile needs an id. Computed from data, not order-dependent. */
const topBy = (list, key) => list.reduce((a, b) => (b[key] > a[key] ? b : a)).id;
const INDEX_REDIRECTS = {
  '/players': async () => `#/players/${topBy(await api.getPlayers(), 'aec')}/stats`,
  '/teams':   async () => `#/teams/${topBy(await api.getTeams(), 'ss')}/stats`,
};

/* module + render caches */
const _pageMod = new Map();   // page name -> module
const _tabMod  = new Map();   // "page/tab" -> module
const loadPage = (page)      => (_pageMod.has(page) ? Promise.resolve(_pageMod.get(page)) : import(`../pages/${page}/page.js`).then(m => (_pageMod.set(page, m), m)));
const loadTab  = (page, tab) => { const k = `${page}/${tab}`; return _tabMod.has(k) ? Promise.resolve(_tabMod.get(k)) : import(`../pages/${page}/${tab}/${tab}.js`).then(m => (_tabMod.set(k, m), m)); };

/* what's currently mounted, so tab switches can skip a shell re-render */
let current = { key: null, contentEl: null, tabsEl: null };

function resolve(hash){
  const path = (hash || '').replace(/^#/, '') || '/';
  for (const r of ROUTES){
    const m = path.match(r.re);
    if (m) return { page: r.page, ...r.parse(m) };
  }
  return null;
}

async function navigate(){
  const path = (location.hash || '').replace(/^#/, '') || '/';
  if (INDEX_REDIRECTS[path]){ location.hash = await INDEX_REDIRECTS[path](); return; }

  const route = resolve(location.hash);
  if (!route){ location.hash = DEFAULT_ROUTE; return; }

  const { page, params, tab } = route;
  const paramsKey = `${page}:${JSON.stringify(params)}`;
  const ctx = { params, tab, api, navigate: (h) => (location.hash = h) };

  setActiveNav(location.hash.replace(/^#/, ''));

  try {
    const mod = await loadPage(page);

    // Re-render the shell only when the page or its params changed.
    if (current.key !== paramsKey){
      view.innerHTML = '';
      const contentEl = await mod.render(view, ctx);
      current = { key: paramsKey, contentEl, tabsEl: view.querySelector('.tabs') };
    } else if (current.tabsEl && tab){
      setActiveTab(current.tabsEl, tab);
    }

    // Load the active tab into the content region (tabbed pages only).
    if (tab && current.contentEl){
      const tmod = await loadTab(page, tab);
      await tmod.init(current.contentEl, ctx);
    }
  } catch (err){
    console.error(err);
    view.innerHTML = `<div class="content" style="grid-template-columns:1fr"><div class="card"><h3>Something went wrong</h3><p class="note">${err.message}</p></div></div>`;
  }
}

renderNav(document.getElementById('nav'));
window.addEventListener('hashchange', navigate);
navigate();

# Disc Space — Ultimate Frisbee Analytics

A multi-page analytics website for professional ultimate frisbee: player and team
profiles, throw-by-throw charts, leaderboards, matchup comparison, and a
win-probability model.

**Vanilla HTML/CSS/JS — no framework, no build step.** A small hash router loads
per-tab HTML/JS modules on demand and renders hand-rolled SVG/canvas charts.

---

## Run locally

The app uses `fetch()` to load partials and JSON, which browsers block on
`file://`, so you need a static server (any will do):

```bash
cd website
python3 -m http.server 8001
# then open http://localhost:8001/
```

Other options: `npx serve`, `php -S localhost:8000`, or the VS Code "Live Server"
extension. There is **nothing to install or build** — it's static files.

### Verifying changes

```bash
# syntax-check every module
find js pages -name '*.js' -exec node --check {} \;

# validate the data files
for f in data/*.json; do node -e "JSON.parse(require('fs').readFileSync('$f'))"; done
```

To smoke-test rendering, load each route in a browser and confirm the view + URL
change with no console errors.

---

## Architecture

### The big picture

```
index.html                 shell: <head> + <header id="nav"> + <main id="view">
  │
  ├─ js/app.js              hash router — resolves a route, renders the page shell,
  │                         loads the active tab module into the content region
  ├─ js/api.js              the ONLY data boundary (static JSON now → live API later)
  ├─ js/components.js       shared chrome: nav, ticker, hero, tabs
  ├─ js/stats-table.js      SHARED config-driven stats table (used by 6 tabs)
  ├─ js/theme.js            the color palette (single source, mirrors CSS vars)
  ├─ js/util.js             pctile / pctClass / seeded-noise helpers
  │
  ├─ css/base.css           design tokens (:root), reset, fonts
  ├─ css/nav.css            nav + ticker
  ├─ css/components.css     hero, tabs, cards, pills, stat bars, stats-table…
  │
  ├─ data/                  static JSON exports (stand-in for a future API)
  └─ pages/<page>/…         one folder per page; per-tab HTML partial + JS module
```

### Routing

Hash-based (`#/players/:id/throwing`) so it works on any static host and over
`file://`-style paths. `js/app.js` holds a small route table that maps a path to
`{ page, params, tab }`.

A **page** (e.g. a player profile) has a persistent shell — hero + tab strip —
and a swappable content region. On navigation the router:

1. resolves the route,
2. re-renders the page shell **only if the page or its params changed** — so
   switching tabs of the same player swaps just the tab content, leaving the
   hero/nav untouched,
3. dynamically `import()`s the active tab module and calls its `init()`.

Every page and active tab is **deep-linkable** — refresh, back/forward, and
bookmarks all land on the exact same view. All nav items, tabs, and in-content
links (ticker games, leaderboard rows, roster names) are real routes.

### Module contracts

A **page module** (`pages/<page>/page.js`) exports:

```js
export const tabs = (params) => [{ key, label, href }];  // optional
export async function render(view, ctx) {                // build hero + tabs
  // …append shell to `view`…
  return contentEl;   // element the active tab renders into (null if tabless)
}
```

A **tab module** (`pages/<page>/<tab>/<tab>.js`) exports:

```js
export async function init(contentEl, ctx) { /* render the tab */ }
```

`ctx = { params, tab, api, navigate }`. Tabs are self-contained: they pull what
they need from `ctx.api` (responses are cached) and `ctx.params`, so a tab switch
never depends on shell state.

### The data layer (`js/api.js`)

The single seam between the UI and its data. Today each method reads a static
JSON file from `data/`; every method returns a **Promise**, so swapping in a live
API later is a one-file change the pages never see:

```js
export const api = {
  getPlayers: (q = {}) => load('data/players.json'),   // → fetch('/api/players?…')
  getPlayer:  (id)     => load(`data/players/${id}.json`),
  // …teams, games…
};
```

`data/*.json` is meant to be produced from the project's dbt `fct_`/`dim_` tables
by a small export step in the daily extraction cron, matching the shapes the API
will eventually return.

### Shared vs. colocated — the key design rule

| Concern | Where it lives | Why |
|---|---|---|
| Chrome (nav, ticker, hero, tabs) | `js/components.js` + `css/` | Used on every page |
| Design tokens / palette | `css/base.css` + `js/theme.js` | Single source of truth |
| **Stats table** | `js/stats-table.js` (shared) | 6 consumers: both leaderboards, both profile Stats tabs, roster, box score |
| **Charts** | beside their tab (colocated) | Each has one consumer today |

Single-use charts (`rose.js`, `percentile-bars.js`, `connections.js`,
`throw-field.js`, `arc-diagram.js`, `win-probability.js`) live **inside their tab
folder**, next to the only code that uses them. The **promotion rule**: a chart
moves up to a shared location only when a *second* real consumer appears — no
pre-built chart library for single-use charts.

The stats table is the opposite case: it had multiple consumers from day one, so
it's a shared **config-driven** engine. Callers pass a column config (columns,
grouped headers, sticky columns, percentile-colored cells) and rows; the engine
owns sorting, sticky columns, and rendering.

---

## Pages

| Route | Page | Tabs |
|---|---|---|
| `#/leaderboard/{teams,players}` | Leaderboard | Teams, Players |
| `#/players` | → redirects to the featured (top-`aec`) player | — |
| `#/players/:id/{stats,throwing}` | Player profile | Stats, Throwing |
| `#/teams` | → redirects to the featured (top-`ss`) team | — |
| `#/teams/:id/{stats,roster}` | Team profile | Stats, Roster |
| `#/schedule` | Schedule | — |
| `#/schedule/:id/{gamecast,boxscore,playbyplay}` | Game | Gamecast, Box Score, Play-by-Play |
| `#/comparison/{players,teams}` | Comparison | Players, Teams |
| `#/prediction` | Prediction | — |
| `#/about` | About | — |

The top nav is **Leaderboard · Schedule · Players · Teams · Compare · Predict ·
About**. Leaderboard is its own page; "Players"/"Teams" open the featured
entity's profile (the bare `#/players` / `#/teams` routes redirect to the
top-ranked player/team). Individual profiles are also reached by clicking
leaderboard rows, rosters, and schedule cards.

---

## Data status

The leaderboard, profiles, comparison, and prediction use the **real** data in
`data/*.json`. Some views (throw charts, win-probability lines, play-by-play,
per-game box scores) currently render **seeded demo data** generated
client-side — deterministic per entity — until the per-game/throw-level exports
are wired through `api.js`. Those spots are marked in the code and in each view's
note text.

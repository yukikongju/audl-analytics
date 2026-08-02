/* ═══════════════════════════════════════════════════════════
   stats-table.js — ONE config-driven stats table, shared by the
   Leaderboard (teams + players) and the Player/Team profile Stats
   tabs. Ported + generalized from inspiration/leaderboard.html.

   Owns: grouped header row, per-column sorting, sticky leading
   columns, and percentile-colored cells (via util.js).

   renderStatsTable(container, {
     title, right,                       // header strip (right = raw HTML)
     groups:  [{label, span}],           // optional grouped header row
     columns: [ Column ],                // see below
     rows,                               // array of row objects
     defaultSort: {key, dir},            // dir: 1 asc, -1 desc
   })

   Column:
     { key, label,
       divide,        // border-left (group separator)
       sticky, left,  // sticky column + its CSS left offset e.g. '0' | '32px'
       render(row),   // custom cell inner HTML (e.g. entity cell) — overrides numeric
       sortVal(row),  // value used for sorting (defaults to row[key])
       fmt(row),      // numeric cell text (defaults to row[key])
       color(row),    // 'pos' | 'neg' | css color string for the cell text
       pctileOf(row), // value to percentile-rank across rows → colored badge
       higherBetter } // for pctile (default true)
   ═══════════════════════════════════════════════════════════ */

import { pctile, pctClass } from './util.js';

/** Helper for pages: an entity cell (color dot + linked name). */
export function entityCell({ href, color, label, dim }){
  const dot = color ? `<span class="dot" style="background:${color}"></span>` : '';
  const inner = `${dot}<span${dim ? ' style="color:var(--dim);font-size:10px"' : ''}>${label}</span>`;
  return href ? `<a href="${href}">${inner}</a>` : inner;
}

export function renderStatsTable(container, cfg){
  const { columns, rows } = cfg;
  let sort = cfg.defaultSort ? { ...cfg.defaultSort } : null;

  const sortValOf = (c) => c.sortVal || ((r) => r[c.key]);
  const stickyStyle = (c) => c.sticky ? ` sticky" style="--l:${c.left || '0'}` : '';

  function bodyHTML(){
    let data = rows;
    if (sort){
      const c = columns.find(x => x.key === sort.key);
      if (c){
        const v = sortValOf(c);
        data = [...rows].sort((a, b) => {
          const av = v(a), bv = v(b);
          if (av < bv) return -sort.dir;
          if (av > bv) return sort.dir;
          return 0;
        });
      }
    }
    return data.map((r, i) => '<tr>' + columns.map(c => {
      const cls = ['', c.divide ? ' divide' : ''];
      // custom / entity cell
      if (c.render){
        return `<td class="entity${c.divide ? ' divide' : ''}${c.sticky ? ' sticky' : ''}"${c.sticky ? ` style="--l:${c.left || '0'}"` : ''}>${c.render(r, i)}</td>`;
      }
      // rank pseudo-column
      if (c.key === '__rank'){
        return `<td class="rk${c.sticky ? ' sticky' : ''}"${c.sticky ? ` style="--l:${c.left || '0'}"` : ''}>${i + 1}</td>`;
      }
      // numeric cell
      let text = c.fmt ? c.fmt(r) : r[c.key];
      let colorCls = '', colorStyle = '';
      if (c.color){
        const col = c.color(r);
        if (col === 'pos' || col === 'neg') colorCls = ' ' + col;
        else if (col) colorStyle = `color:${col}`;
      }
      let badge = '';
      if (c.pctileOf){
        // Rank against cfg.pctileRows when provided (e.g. a single-player
        // profile row still shows its league percentile), else the rows shown.
        const arr = (cfg.pctileRows || rows).map(x => c.pctileOf(x));
        const p = pctile(c.pctileOf(r), arr, c.higherBetter !== false);
        badge = `<span class="pct ${pctClass(p)}">${p}</span>`;
      }
      const styleAttr = (colorStyle || c.sticky) ? ` style="${[colorStyle, c.sticky ? `--l:${c.left || '0'}` : ''].filter(Boolean).join(';')}"` : '';
      return `<td class="num${colorCls}${c.divide ? ' divide' : ''}${c.sticky ? ' sticky' : ''}"${styleAttr}>${text}${badge}</td>`;
    }).join('') + '</tr>').join('');
  }

  function headHTML(){
    let h = '';
    if (cfg.groups){
      h += '<tr>' + cfg.groups.map(g =>
        `<th class="group${g.divide ? ' divide' : ''}${g.sticky ? ' sticky' : ''}"${g.sticky ? ` style="--l:${g.left || '0'}"` : ''} colspan="${g.span}">${g.label || ''}</th>`).join('') + '</tr>';
    }
    h += '<tr>' + columns.map(c => {
      const sorted = sort && sort.key === c.key ? ' sorted' : '';
      const sticky = c.sticky ? ` sticky` : '';
      const style = c.sticky ? ` style="--l:${c.left || '0'}"` : '';
      const label = c.key === '__rank' ? (c.label || 'Rk') : c.label;
      return `<th class="${c.divide ? 'divide ' : ''}${sticky}${sorted}"${style} data-key="${c.key}">${label}</th>`;
    }).join('') + '</tr>';
    return h;
  }

  container.className = 'table-wrap';
  container.innerHTML = `
    ${cfg.title ? `<div class="table-header"><h3>${cfg.title}</h3>${cfg.right ? `<div class="right">${cfg.right}</div>` : ''}</div>` : ''}
    <div class="table-scroll">
      <table class="stats-table">
        <thead>${headHTML()}</thead>
        <tbody>${bodyHTML()}</tbody>
      </table>
    </div>`;

  // Sort on header click (skip the group row / rank / non-sortable).
  const thead = container.querySelector('thead');
  thead.addEventListener('click', (e) => {
    const th = e.target.closest('th[data-key]');
    if (!th) return;
    const key = th.dataset.key;
    if (key === '__rank') return;
    const col = columns.find(c => c.key === key);
    if (col && col.sortable === false) return;
    if (sort && sort.key === key) sort.dir *= -1;
    else sort = { key, dir: -1 };
    thead.innerHTML = headHTML();
    container.querySelector('tbody').innerHTML = bodyHTML();
  });
}

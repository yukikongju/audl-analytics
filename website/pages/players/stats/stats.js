/* Player → Stats tab. Reuses the shared stats-table (single-player row,
   league percentiles) + three colocated charts: rose / percentile / connections. */
import { renderStatsTable } from '../../../js/stats-table.js';
import { hashStr } from '../../../js/util.js';
import { renderRose, roseData } from './rose.js';
import { renderPercentileBars, percentileData } from './percentile-bars.js';
import { renderConnections, connectionsData } from './connections.js';

const f1 = (v) => (+v).toFixed(1);

const STAT_COLS = [
  { key:'aec',  label:'Tot-aEC', fmt:r => f1(r.aec),  pctileOf:r => r.aec },
  { key:'taec', label:'T-aEC',  fmt:r => f1(r.taec), pctileOf:r => r.taec },
  { key:'raec', label:'R-aEC',  fmt:r => f1(r.raec), pctileOf:r => r.raec },
  { key:'g', label:'G', divide:true, pctileOf:r => r.g },
  { key:'a', label:'A', pctileOf:r => r.a },
  { key:'c', label:'C', pctileOf:r => r.c },
  { key:'t', label:'T' },
  { key:'b', label:'B' },
  { key:'cp',  label:'CP%', divide:true, fmt:r => f1(r.cp),  pctileOf:r => r.cp },
  { key:'hu',  label:'HuR', fmt:r => f1(r.hu),  pctileOf:r => r.hu },
  { key:'xcp', label:'xCP', fmt:r => f1(r.xcp), pctileOf:r => r.xcp },
  { key:'gp', label:'GP', divide:true },
];
const GROUPS = [
  { label:'Contribution', span:3 },
  { label:'Box Score', span:5, divide:true },
  { label:'Throwing', span:3, divide:true },
  { label:'Usage', span:1, divide:true },
];

export async function init(content, ctx){
  const players = await ctx.api.getPlayers();
  const player = players.find(p => p.id === ctx.params.id);
  if (!player){
    content.innerHTML = `<div class="content" style="grid-template-columns:1fr"><div class="card"><h3>Player not found</h3></div></div>`;
    return;
  }
  const seed = hashStr(player.id);

  content.innerHTML = `
    <div style="padding:24px 5vw 0"><div id="p-table"></div></div>
    <div class="content" style="grid-template-columns:1fr">
      <div class="card">
        <div class="stats-panels">
          <div>
            <h3>Throw &amp; Receive Direction</h3>
            <h4>Throws</h4>
            <div class="rose-wrap"><svg id="roseThrow" width="200" height="200" viewBox="-100 -100 200 200"></svg></div>
            <h4>Receptions</h4>
            <div class="rose-wrap"><svg id="roseRecv" width="200" height="200" viewBox="-100 -100 200 200"></svg></div>
          </div>
          <div><h3>Percentile Rankings</h3><div id="pctBars"></div></div>
          <div><h3>Connections</h3><div id="conns"></div></div>
        </div>
      </div>
    </div>`;

  renderStatsTable(content.querySelector('#p-table'), {
    title: `${player.name} — Season 2026`, columns: STAT_COLS, groups: GROUPS,
    rows: [player], pctileRows: players,
  });
  renderRose(content.querySelector('#roseThrow'), roseData(seed, 'throw'));
  renderRose(content.querySelector('#roseRecv'), roseData(seed, 'recv'));
  renderPercentileBars(content.querySelector('#pctBars'), percentileData(seed));
  renderConnections(content.querySelector('#conns'), connectionsData(seed));
}

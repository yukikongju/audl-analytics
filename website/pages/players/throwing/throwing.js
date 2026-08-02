/* Player → Throwing tab. Seeds throws for this player and mounts the
   colocated throw-field engine. (Throws come from the api later.) */
import { hashStr } from '../../../js/util.js';
import { generateThrows, mountThrowField } from './throw-field.js';

export async function init(content, ctx){
  const players = await ctx.api.getPlayers();
  const player = players.find(p => p.id === ctx.params.id);
  const seed = hashStr(ctx.params.id);

  content.innerHTML = `<div style="padding:30px 0 50px"></div>`;
  const host = content.firstElementChild;
  mountThrowField(host, generateThrows(seed));
}

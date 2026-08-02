/* Player profile shell: player hero + controls + Stats/Throwing tabs + content. */
import { renderHero, initTabs, renderControls } from '../../js/components.js';

/* current tab from the URL, so search-navigation keeps the active tab */
const curTab = () => location.hash.split('/')[3] || 'stats';

export const tabs = (params) => ([
  { key: 'stats',    label: 'Stats',    href: `#/players/${params.id}/stats` },
  { key: 'throwing', label: 'Throwing', href: `#/players/${params.id}/throwing` },
]);

export async function render(view, ctx){
  const { id } = ctx.params;
  const [players, teams] = await Promise.all([ctx.api.getPlayers(), ctx.api.getTeams()]);
  const player = players.find(p => p.id === id);
  const team = player && teams.find(t => t.id === player.team);

  const hero = document.createElement('section');
  renderHero(hero, { type: 'player', data: {
    name: player ? player.name : id,
    team: team ? `${team.city} ${team.name}` : '',
    line: 'Offense',
    position: 'Cutter',
    bio: player ? [`GP: ${player.gp}`, `Completions: ${player.c}`, `CP%: ${player.cp}`] : [],
  }});

  const controls = document.createElement('div');
  renderControls(controls, {
    statView: true,
    findLabel: 'Find Player',
    entities: players.map(p => ({ id: p.id, label: p.name })),
    onFind: (pid) => ctx.navigate(`#/players/${pid}/${curTab()}`),
  });

  const tabsEl = document.createElement('nav');
  initTabs(tabsEl, tabs(ctx.params), ctx.tab);

  const content = document.createElement('div');
  content.className = 'tab-content';

  view.append(hero, controls, tabsEl, content);
  return content;
}

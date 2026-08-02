/* Team profile shell: team hero + controls + Stats/Roster tabs + content. */
import { renderHero, initTabs, renderControls } from '../../js/components.js';

/* current tab from the URL, so search-navigation keeps the active tab */
const curTab = () => location.hash.split('/')[3] || 'stats';

export const tabs = (params) => ([
  { key: 'stats',  label: 'Stats',  href: `#/teams/${params.id}/stats` },
  { key: 'roster', label: 'Roster', href: `#/teams/${params.id}/roster` },
]);

export async function render(view, ctx){
  const teams = await ctx.api.getTeams();
  const team = teams.find(t => t.id === ctx.params.id);

  const hero = document.createElement('section');
  renderHero(hero, { type: 'team', data: team ? {
    city: team.city, name: team.name, record: team.record,
    stats: [
      { label: 'aEC', value: team.aec.toFixed(1) },
      { label: 'OE', value: team.oe.toFixed(1) + '%' },
      { label: 'DE', value: team.de.toFixed(1) + '%' },
    ],
    social: `@${team.name.toLowerCase().replace(/\s/g, '')}`,
  } : { name: ctx.params.id } });

  const controls = document.createElement('div');
  renderControls(controls, {
    findLabel: 'Find Team',
    entities: teams.map(t => ({ id: t.id, label: `${t.city} ${t.name}` })),
    onFind: (tid) => ctx.navigate(`#/teams/${tid}/${curTab()}`),
  });

  const tabsEl = document.createElement('nav');
  initTabs(tabsEl, tabs(ctx.params), ctx.tab);

  const content = document.createElement('div');
  content.className = 'tab-content';
  view.append(hero, controls, tabsEl, content);
  return content;
}

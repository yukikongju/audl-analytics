/* Comparison shell: simple hero + Players/Teams tabs. */
import { renderHero, initTabs } from '../../js/components.js';

export const tabs = () => ([
  { key: 'players', label: 'Players', href: '#/comparison/players' },
  { key: 'teams',   label: 'Teams',   href: '#/comparison/teams' },
]);

export async function render(view, ctx){
  const hero = document.createElement('section');
  renderHero(hero, { type: 'simple', data: { eyebrow: 'Head to head', title: 'Compare' } });
  const tabsEl = document.createElement('nav');
  initTabs(tabsEl, tabs(), ctx.tab);
  const content = document.createElement('div');
  content.className = 'tab-content';
  view.append(hero, tabsEl, content);
  return content;
}

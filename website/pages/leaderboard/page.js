/* Leaderboard page shell: simple hero + Teams/Players tabs + content region. */
import { renderHero, initTabs } from '../../js/components.js';

export const tabs = () => ([
  { key: 'teams',   label: 'Teams',   href: '#/leaderboard/teams' },
  { key: 'players', label: 'Players', href: '#/leaderboard/players' },
]);

export async function render(view, ctx){
  const hero = document.createElement('section');
  renderHero(hero, { type: 'simple', data: { eyebrow: 'UFA · 2026 Season', title: 'Leaderboard' } });

  const tabsEl = document.createElement('nav');
  initTabs(tabsEl, tabs(), ctx.tab);

  const content = document.createElement('div');
  content.className = 'tab-content';

  view.append(hero, tabsEl, content);
  return content;
}

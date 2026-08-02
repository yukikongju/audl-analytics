/* About page (tabless): static overview. */
import { renderHero } from '../../js/components.js';

export async function render(view, ctx){
  const hero = document.createElement('section');
  renderHero(hero, { type: 'simple', data: { eyebrow: 'What is this', title: 'About' } });

  const body = document.createElement('div');
  body.className = 'content';
  body.style.gridTemplateColumns = '1fr';
  body.innerHTML = `
    <div class="card">
      <h3>Disc Space</h3>
      <p style="color:var(--dim);line-height:1.7;font-size:14px">
        Advanced analytics for professional ultimate frisbee — player and team profiles,
        throw-by-throw charts, leaderboards, matchup comparisons, and a win-probability model.
      </p>
      <h3 style="margin-top:24px">How it works</h3>
      <p style="color:var(--dim);line-height:1.7;font-size:14px">
        Game events are extracted daily and modeled into fact and dimension tables with dbt.
        Those tables are exported to JSON that this site reads through a single data layer
        (<code style="color:var(--lime)">js/api.js</code>), which will later point at a live API
        without any page changes.
      </p>
      <h3 style="margin-top:24px">Stack</h3>
      <p style="color:var(--dim);line-height:1.7;font-size:14px">
        Vanilla HTML/CSS/JS, no framework, no build step — a small hash router loads per-tab
        modules and hand-rolled SVG/canvas charts. Shared chrome and the stats table are
        deduped into one place; single-use charts live beside their tab.
      </p>
    </div>`;

  view.append(hero, body);
  return null;
}

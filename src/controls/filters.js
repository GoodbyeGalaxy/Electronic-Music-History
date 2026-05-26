import { YEAR_END } from '../graph/layout.js';

/**
 * Creates track solo badges and year range slider in toolbar.
 * Solo mode: click a badge to isolate that track; click again to show all.
 *
 * @param {HTMLElement} toolbarEl
 * @param {object[]}    tracks    - from genres.json
 * @param {object[]}    genres    - from genres.json
 * @param {object}      renderer  - { filterTracks, filterYears }
 */
export function createFilters(toolbarEl, tracks, genres, renderer) {
  let soloTrackId = null;
  const allTrackIds = tracks.map(t => t.id);
  const badges = new Map();

  const badgeWrap = document.createElement('div');
  badgeWrap.style.cssText = 'display:flex;gap:6px;align-items:center;margin-left:auto;flex-wrap:wrap;';

  tracks.forEach(track => {
    const badge = document.createElement('button');
    badge.className = 'filter-badge active';
    badge.style.cssText = `background:${track.color}22;border-color:${track.color};color:${track.color};`;
    badge.textContent = track.label;
    badge.addEventListener('click', () => {
      if (soloTrackId === track.id) {
        // De-solo: show all
        soloTrackId = null;
        badges.forEach(b => b.classList.add('active'));
        renderer.filterTracks(null);
      } else {
        // Solo this track
        soloTrackId = track.id;
        badges.forEach((b, id) => b.classList.toggle('active', id === track.id));
        renderer.filterTracks([track.id]);
      }
    });
    badges.set(track.id, badge);
    badgeWrap.appendChild(badge);
  });

  const years = genres.map(g => g.year_start).filter(Boolean);
  const minYear = Math.min(...years);
  const maxYear = YEAR_END;

  const sliderWrap = document.createElement('div');
  sliderWrap.style.cssText = 'display:flex;align-items:center;gap:8px;';

  const label = document.createElement('span');
  label.style.cssText = 'color:#888;font-size:11px;white-space:nowrap;';
  label.textContent = `${minYear} – ${maxYear}`;

  const slider = document.createElement('input');
  slider.type = 'range';
  slider.min = minYear;
  slider.max = maxYear;
  slider.value = minYear;
  slider.style.width = '120px';

  slider.addEventListener('input', () => {
    const from = parseInt(slider.value, 10);
    label.textContent = `${from} – ${maxYear}`;
    renderer.filterYears(from, maxYear);
  });

  renderer.filterYears(minYear, maxYear);
  sliderWrap.appendChild(label);
  sliderWrap.appendChild(slider);
  toolbarEl.appendChild(sliderWrap);
  toolbarEl.appendChild(badgeWrap);
}

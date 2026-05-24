/**
 * Creates track toggle badges and year range slider in toolbar.
 *
 * @param {HTMLElement} toolbarEl
 * @param {object[]}    tracks    - from genres.json
 * @param {object[]}    genres    - from genres.json
 * @param {object}      renderer  - { filterTracks, filterYears }
 */
export function createFilters(toolbarEl, tracks, genres, renderer) {
  const activeTrackIds = new Set(tracks.map(t => t.id));

  const badgeWrap = document.createElement('div');
  badgeWrap.style.cssText = 'display:flex;gap:6px;align-items:center;margin-left:auto;';

  tracks.forEach(track => {
    const badge = document.createElement('button');
    badge.className = 'filter-badge active';
    badge.style.cssText = `background:${track.color}22;border-color:${track.color};color:${track.color};`;
    badge.textContent = track.label;
    badge.addEventListener('click', () => {
      if (activeTrackIds.has(track.id)) {
        activeTrackIds.delete(track.id);
        badge.classList.remove('active');
      } else {
        activeTrackIds.add(track.id);
        badge.classList.add('active');
      }
      renderer.filterTracks([...activeTrackIds]);
    });
    badgeWrap.appendChild(badge);
  });

  const years = genres.map(g => g.year_start).filter(Boolean);
  const minYear = Math.min(...years);
  const maxYear = new Date().getFullYear();

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

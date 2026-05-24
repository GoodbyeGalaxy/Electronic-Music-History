import { createRenderer } from './graph/renderer.js';
import { createDetailPanel } from './panels/detail.js';
import { createFilters } from './controls/filters.js';
import { createSearch } from './controls/search.js';

async function init() {
  const res = await fetch('./data/genres.json');
  if (!res.ok) throw new Error(`Failed to load genres.json: ${res.status}`);
  const data = await res.json();

  const wrapper  = document.getElementById('canvas-wrapper');
  const labelsEl = document.getElementById('track-labels');
  const toolbarEl = document.getElementById('toolbar');
  const panelEl  = document.getElementById('detail-panel');

  const searchInput = document.createElement('input');
  searchInput.type = 'search';
  searchInput.placeholder = 'Genre suchen…';
  toolbarEl.appendChild(searchInput);

  const panel = createDetailPanel(panelEl, data.tracks, genreId => {
    renderer.highlight(genreId);
    const genre = data.genres.find(g => g.id === genreId);
    if (genre) panel.open(genre);
  });

  const renderer = createRenderer(wrapper, labelsEl, data, genre => {
    if (!genre) { panel.close(); renderer.clearHighlight(); return; }
    renderer.highlight(genre.id);
    panel.open(genre);
  });

  createSearch(searchInput, renderer.layout.nodes, renderer);
  createFilters(toolbarEl, data.tracks, data.genres, renderer);
}

init().catch(err => {
  const pre = document.createElement('pre');
  pre.style.cssText = 'color:red;padding:20px;';
  pre.textContent = `Error: ${err.message}`;
  document.body.appendChild(pre);
  console.error(err);
});

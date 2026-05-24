import { createAudioPlayer } from './audio.js';

/**
 * Manages the slide-in genre detail panel.
 * All DOM operations via createElement — no innerHTML.
 *
 * @param {HTMLElement} panelEl    - #detail-panel
 * @param {object[]}    tracks     - from genres.json
 * @param {Function}    onTagClick - callback(genreId)
 */
export function createDetailPanel(panelEl, tracks, onTagClick) {
  function trackColor(trackId) {
    return tracks.find(t => t.id === trackId)?.color ?? '#888';
  }

  function open(genre) {
    while (panelEl.firstChild) panelEl.removeChild(panelEl.firstChild);

    const color = trackColor(genre.track);

    const header = document.createElement('div');
    header.className = 'panel-header';

    const headerLeft = document.createElement('div');

    const badge = document.createElement('span');
    badge.className = 'tag';
    badge.style.cssText = `background:${color}22;border-color:${color};color:${color};margin-bottom:6px;display:inline-block;`;
    badge.textContent = genre.track;

    const nameEl = document.createElement('h3');
    nameEl.style.cssText = 'color:#e6edf3;font-size:16px;margin:6px 0 2px;';
    nameEl.textContent = genre.name;

    const metaEl = document.createElement('div');
    metaEl.style.cssText = 'color:#888;font-size:11px;';
    const yearRange = genre.year_end ? `${genre.year_start}–${genre.year_end}` : `${genre.year_start} – heute`;
    metaEl.textContent = genre.origin ? `${yearRange} · ${genre.origin}` : yearRange;

    const closeBtn = document.createElement('button');
    closeBtn.className = 'panel-close';
    closeBtn.textContent = '✕';
    closeBtn.addEventListener('click', close);

    headerLeft.appendChild(badge);
    headerLeft.appendChild(nameEl);
    headerLeft.appendChild(metaEl);
    header.appendChild(headerLeft);
    header.appendChild(closeBtn);
    panelEl.appendChild(header);

    const body = document.createElement('div');
    body.className = 'panel-body';

    if (genre.description) {
      body.appendChild(makeSection('Beschreibung', () => {
        const p = document.createElement('p');
        p.style.cssText = 'color:#cdd9e5;font-size:12px;line-height:1.6;';
        p.textContent = genre.description;
        return p;
      }));
    }

    if (genre.parents?.length) {
      body.appendChild(makeSection('Herkunft', () =>
        makeTagList(genre.parents, color, onTagClick)
      ));
    }

    if (genre.key_artists?.length) {
      body.appendChild(makeSection('Schluesselkuenstler:innen', () => {
        const p = document.createElement('p');
        p.style.cssText = 'color:#cdd9e5;font-size:11px;line-height:1.8;';
        p.textContent = genre.key_artists.join(' · ');
        return p;
      }));
    }

    if (genre.subvariants?.length) {
      body.appendChild(makeSection('Subvarianten', () => {
        const p = document.createElement('p');
        p.style.cssText = 'color:#888;font-size:11px;';
        p.textContent = genre.subvariants.join(', ');
        return p;
      }));
    }

    if (genre.audio_examples?.length) {
      body.appendChild(makeSection('Audiobeispiel (CC)', () => {
        const wrap = document.createElement('div');
        wrap.style.cssText = 'display:flex;flex-direction:column;gap:8px;';
        genre.audio_examples.forEach(ex => wrap.appendChild(createAudioPlayer(ex, color)));
        return wrap;
      }));
    }

    const links = [];
    if (genre.wikipedia_slug) {
      links.push({ label: '📖 Wikipedia', href: `https://en.wikipedia.org/wiki/${genre.wikipedia_slug}` });
    }
    if (genre.wikidata_id) {
      links.push({ label: `🔗 Wikidata ${genre.wikidata_id}`, href: `https://www.wikidata.org/wiki/${genre.wikidata_id}` });
    }
    if (links.length) {
      body.appendChild(makeSection('Links', () => {
        const wrap = document.createElement('div');
        wrap.style.cssText = 'display:flex;gap:12px;';
        links.forEach(({ label, href }) => {
          const a = document.createElement('a');
          a.href = href;
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          a.style.cssText = 'color:#4fc3f7;font-size:11px;text-decoration:none;';
          a.textContent = label;
          wrap.appendChild(a);
        });
        return wrap;
      }));
    }

    panelEl.appendChild(body);
    panelEl.classList.add('panel--open');
    panelEl.classList.remove('panel--closed');
  }

  function close() {
    panelEl.classList.remove('panel--open');
    panelEl.classList.add('panel--closed');
  }

  return { open, close };
}

function makeSection(label, contentFn) {
  const wrap = document.createElement('div');
  const lbl = document.createElement('div');
  lbl.className = 'panel-section-label';
  lbl.textContent = label;
  wrap.appendChild(lbl);
  wrap.appendChild(contentFn());
  return wrap;
}

function makeTagList(ids, color, onClick) {
  const wrap = document.createElement('div');
  wrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;';
  ids.forEach(id => {
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.style.cssText = `background:${color}11;border-color:${color};color:${color};`;
    tag.textContent = id;
    tag.addEventListener('click', () => onClick(id));
    wrap.appendChild(tag);
  });
  return wrap;
}

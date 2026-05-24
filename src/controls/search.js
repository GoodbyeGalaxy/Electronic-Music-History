/**
 * Free text search over genre names, artists, and subvariants.
 *
 * @param {HTMLInputElement} inputEl
 * @param {object[]}         nodes    - from computeLayout()
 * @param {object}           renderer - { highlight, clearHighlight }
 */
export function createSearch(inputEl, nodes, renderer) {
  inputEl.addEventListener('input', () => {
    const q = inputEl.value.trim().toLowerCase();
    if (!q) { renderer.clearHighlight(); return; }

    const matches = nodes.filter(n =>
      n.name.toLowerCase().includes(q) ||
      n.key_artists?.some(a => a.toLowerCase().includes(q)) ||
      n.subvariants?.some(s => s.toLowerCase().includes(q))
    );

    if (matches.length === 0) { renderer.clearHighlight(); return; }
    renderer.highlight(matches[0].id);
  });
}

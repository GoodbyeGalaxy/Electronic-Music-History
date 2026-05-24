# Force-Directed Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the static row-stacking layout with a D3 force simulation that resolves node overlap naturally while preserving track lanes and temporal X-axis; add drag-to-disturb-snap-back interaction.

**Architecture:** `layout.js` computes deterministic *target* positions (`tx`, `ty`) per node — year → X, track → Y. `renderer.js` initialises `x = tx, y = ty` then runs a `d3.forceSimulation` with three forces: `forceX` (soft pull to `tx`), `forceY` (strong pull to `ty`, keeps nodes in their lane), and `forceCollide` (no overlap). Drag fixes a node's position temporarily; releasing it unfixes so forces snap it back. A brief reheat on click gives tactile feedback. The public renderer API (`highlight`, `clearHighlight`, `filterTracks`, `filterYears`, `layout`) is unchanged.

**Tech Stack:** D3 v7 (`d3.forceSimulation`, `forceX`, `forceY`, `forceCollide`, `drag`), Vitest, Vite.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/graph/layout.js` | Modify | Remove `assignRows`; add `tx`/`ty` target fields to nodes |
| `src/graph/renderer.js` | Modify | Replace static positioning with force simulation + drag |
| `tests/graph/layout.test.js` | Modify | Assert `tx`/`ty` instead of `x`/`y` |

---

## Task 1: Update `layout.js` — target positions

The current `computeLayout` assigns `x`/`y` directly and runs `assignRows` to stack crowded nodes into multiple rows. We replace this with `tx` (target x from year) and `ty` (target y from track centre). The force simulation in `renderer.js` will own `x`/`y`. `assignRows` is deleted entirely.

**Files:**
- Modify: `src/graph/layout.js`
- Modify: `tests/graph/layout.test.js`

- [ ] **Step 1: Update the failing tests first**

Open `tests/graph/layout.test.js` and replace the entire file:

```javascript
import { describe, it, expect } from 'vitest';
import { computeLayout } from '../../src/graph/layout.js';

const MOCK_DATA = {
  genres: [
    { id: 'theremin', name: 'Theremin', track: 'early', year_start: 1920,
      year_end: null, parents: [], key_artists: [], audio_examples: [] },
    { id: 'musique_concrete', name: 'Musique Concrete', track: 'electroacoustic',
      year_start: 1948, year_end: null, parents: ['theremin'],
      key_artists: [], audio_examples: [] },
  ],
  edges: [
    { from: 'theremin', to: 'musique_concrete', type: 'derives', label: '' },
  ],
  tracks: [
    { id: 'early', label: 'Fruehgeschichte', color: '#4fc3f7', order: 0 },
    { id: 'electroacoustic', label: 'Elektroakustik', color: '#388e3c', order: 1 },
  ],
};

describe('computeLayout', () => {
  it('sets tx ≈ 160px for year 1920 at width 1000', () => {
    const { nodes } = computeLayout(MOCK_DATA, 1000, 400);
    const n = nodes.find(n => n.id === 'theremin');
    // (1920 - 1900) / (2025 - 1900) * 1000 ≈ 160
    expect(n.tx).toBeCloseTo(160, 0);
  });

  it('sets ty for musique_concrete below theremin (track order 1 > 0)', () => {
    const { nodes } = computeLayout(MOCK_DATA, 1000, 400);
    const t = nodes.find(n => n.id === 'theremin');
    const m = nodes.find(n => n.id === 'musique_concrete');
    expect(m.ty).toBeGreaterThan(t.ty);
  });

  it('assigns positive width and fixed height to every node', () => {
    const { nodes } = computeLayout(MOCK_DATA, 1000, 400);
    for (const n of nodes) {
      expect(n.width).toBeGreaterThan(0);
      expect(n.height).toBe(36);
    }
  });

  it('resolves edge source and target to node objects', () => {
    const { edges } = computeLayout(MOCK_DATA, 1000, 400);
    expect(edges).toHaveLength(1);
    expect(edges[0].source.id).toBe('theremin');
    expect(edges[0].target.id).toBe('musique_concrete');
  });

  it('drops edges where source or target is not found', () => {
    const data = {
      ...MOCK_DATA,
      edges: [{ from: 'ghost', to: 'theremin', type: 'derives', label: '' }],
    };
    const { edges } = computeLayout(data, 1000, 400);
    expect(edges).toHaveLength(0);
  });

  it('sets trackHeight = svgHeight / trackCount', () => {
    const { trackHeight } = computeLayout(MOCK_DATA, 1000, 400);
    expect(trackHeight).toBe(200);
  });
});
```

- [ ] **Step 2: Run tests — expect 2 failures**

```bash
pnpm exec vitest run
```

Expected: 2 FAIL (`tx` and `ty` don't exist yet), 4 PASS.

- [ ] **Step 3: Replace `src/graph/layout.js`**

```javascript
const YEAR_START = 1900;
export const YEAR_END = 2025;
const NODE_HEIGHT = 36;
const CHAR_WIDTH = 7;
const NODE_PADDING_X = 20;

/**
 * Computes target positions (tx, ty) for each node and resolves edge references.
 * tx = year-based horizontal target; ty = track-centre vertical target.
 * The renderer owns x/y (current simulation positions).
 *
 * @param {object} data      - genres.json ({ genres, edges, tracks })
 * @param {number} svgWidth
 * @param {number} svgHeight
 * @returns {{ nodes, edges, tracks, trackHeight }}
 */
export function computeLayout(data, svgWidth, svgHeight) {
  const { genres, edges, tracks } = data;

  const sortedTracks = [...tracks].sort((a, b) => a.order - b.order);
  const trackIndex = Object.fromEntries(sortedTracks.map((t, i) => [t.id, i]));
  const trackCount = sortedTracks.length;
  const trackHeight = svgHeight / trackCount;

  const xScale = year => ((year - YEAR_START) / (YEAR_END - YEAR_START)) * svgWidth;
  const yScale = trackId => {
    const idx = trackIndex[trackId];
    if (idx === undefined) {
      console.warn(`computeLayout: unknown trackId "${trackId}"`);
      return 0;
    }
    return (idx + 0.5) * trackHeight;
  };

  const nodes = genres.map(genre => {
    const width = Math.max(genre.name.length * CHAR_WIDTH + NODE_PADDING_X * 2, 60);
    const tx = xScale(genre.year_start);
    const ty = yScale(genre.track);
    return { ...genre, tx, ty, width, height: NODE_HEIGHT };
  });

  const nodeById = Object.fromEntries(nodes.map(n => [n.id, n]));

  const resolvedEdges = edges
    .map(edge => {
      const source = nodeById[edge.from];
      const target = nodeById[edge.to];
      if (!source || !target) return null;
      return { ...edge, source, target };
    })
    .filter(Boolean);

  return { nodes, edges: resolvedEdges, tracks: sortedTracks, trackHeight };
}
```

- [ ] **Step 4: Run tests — expect all 6 pass**

```bash
pnpm exec vitest run
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/graph/layout.js tests/graph/layout.test.js
git commit -m "refactor: layout computes tx/ty target positions, drops assignRows"
```

---

## Task 2: Update `renderer.js` — force simulation + drag

Replace the static `transform` assignment with a live D3 force simulation. Three forces keep the layout clean:
- `forceX` (strength 0.12) — gentle pull toward the year-based `tx`
- `forceY` (strength 0.9) — strong pull toward track-centre `ty`, keeps nodes in their lane
- `forceCollide` (radius = node half-width + 3px) — prevents overlap

Drag interaction: grabbing a node fixes its position; releasing it clears `fx`/`fy` so forces snap it back. Clicking a node reheats the simulation briefly (alpha 0.08) for tactile feedback. Changing filters also reheats.

**Files:**
- Modify: `src/graph/renderer.js`

- [ ] **Step 1: Replace `src/graph/renderer.js`**

```javascript
import * as d3 from 'd3';
import { computeLayout } from './layout.js';

/**
 * Creates the D3 SVG graph with force-directed layout.
 *
 * @param {HTMLElement} wrapper     - #canvas-wrapper
 * @param {HTMLElement} labelsEl    - #track-labels
 * @param {object}      data        - genres.json
 * @param {Function}    onNodeClick - callback(genreObject | null)
 * @returns {{ highlight, clearHighlight, filterTracks, filterYears, layout }}
 */
export function createRenderer(wrapper, labelsEl, data, onNodeClick) {
  const width = wrapper.clientWidth;
  const height = wrapper.clientHeight;
  const layout = computeLayout(data, width, height);

  while (labelsEl.firstChild) labelsEl.removeChild(labelsEl.firstChild);
  layout.tracks.forEach(track => {
    const div = document.createElement('div');
    div.className = 'track-label';
    div.style.height = `${layout.trackHeight}px`;
    div.style.color = track.color;
    div.textContent = track.label;
    labelsEl.appendChild(div);
  });

  const svg = d3.select(wrapper)
    .append('svg')
    .attr('class', 'graph-canvas')
    .attr('width', width)
    .attr('height', height);

  const zoomGroup = svg.append('g').attr('class', 'zoom-group');

  svg.call(
    d3.zoom().scaleExtent([0.2, 4])
      .on('zoom', e => zoomGroup.attr('transform', e.transform))
  );

  layout.tracks.forEach((_, i) => {
    if (i === 0) return;
    zoomGroup.append('line')
      .attr('class', 'track-separator')
      .attr('x1', 0).attr('y1', i * layout.trackHeight)
      .attr('x2', width).attr('y2', i * layout.trackHeight);
  });

  const edgeGroup = zoomGroup.append('g').attr('class', 'edges');
  const edgeSel = edgeGroup.selectAll('path')
    .data(layout.edges)
    .join('path')
    .attr('class', d => `edge edge--${d.type}`)
    .attr('stroke', d => {
      if (d.type === 'influence') return '#ffa657';
      const track = layout.tracks.find(t => t.id === d.target.track);
      return track ? track.color : '#4fc3f7';
    })
    .attr('stroke-dasharray', d => d.type === 'influence' ? '5,3' : null);

  const nodeGroup = zoomGroup.append('g').attr('class', 'nodes');
  const nodeSel = nodeGroup.selectAll('g.node')
    .data(layout.nodes)
    .join('g')
    .attr('class', 'node');

  nodeSel.append('rect')
    .attr('width', d => d.width)
    .attr('height', d => d.height)
    .attr('rx', 6)
    .attr('fill', d => {
      const track = layout.tracks.find(t => t.id === d.track);
      return track ? hexToFill(track.color) : '#111';
    })
    .attr('stroke', d => {
      const track = layout.tracks.find(t => t.id === d.track);
      return track ? track.color : '#888';
    })
    .attr('stroke-width', 1.5);

  nodeSel.append('text').attr('class', 'node-name')
    .attr('x', d => d.width / 2).attr('y', d => d.height / 2 - 4)
    .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
    .text(d => d.name);

  nodeSel.append('text').attr('class', 'node-year')
    .attr('x', d => d.width / 2).attr('y', d => d.height / 2 + 10)
    .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
    .text(d => d.year_start);

  // Seed simulation from target positions so nodes start at home
  layout.nodes.forEach(d => { d.x = d.tx; d.y = d.ty; });

  const simulation = d3.forceSimulation(layout.nodes)
    .force('x', d3.forceX(d => d.tx).strength(0.12))
    .force('y', d3.forceY(d => d.ty).strength(0.9))
    .force('collide', d3.forceCollide(d => d.width / 2 + 3).strength(0.9).iterations(3))
    .alphaDecay(0.015)
    .on('tick', ticked);

  function ticked() {
    nodeSel.attr('transform', d =>
      `translate(${d.x - d.width / 2},${d.y - d.height / 2})`
    );
    edgeSel.attr('d', edgePath);
  }

  // Drag: hold to displace, release to snap back via forces
  const drag = d3.drag()
    .on('start', (event, d) => {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    })
    .on('drag', (event, d) => {
      d.fx = event.x;
      d.fy = event.y;
    })
    .on('end', (event, d) => {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    });

  nodeSel.call(drag);

  nodeSel.on('click', (event, d) => {
    event.stopPropagation();
    onNodeClick(d);
    simulation.alpha(0.08).restart();
  });

  svg.on('click', () => { clearHighlight(); onNodeClick(null); });

  function highlight(nodeId) {
    const ancestorIds = new Set();
    const pathEdgeKeys = new Set();
    const visited = new Set([nodeId]);
    const queue = [nodeId];

    while (queue.length) {
      const id = queue.shift();
      layout.edges.forEach(e => {
        if (e.target.id === id && !visited.has(e.source.id)) {
          visited.add(e.source.id);
          ancestorIds.add(e.source.id);
          pathEdgeKeys.add(`${e.source.id}→${e.target.id}`);
          queue.push(e.source.id);
        }
      });
    }

    const highlightedIds = new Set([nodeId, ...ancestorIds]);

    nodeSel
      .classed('node--dimmed', d => !highlightedIds.has(d.id))
      .classed('node--selected', d => highlightedIds.has(d.id));
    edgeSel.classed('edge--dimmed',
      d => !pathEdgeKeys.has(`${d.source.id}→${d.target.id}`));
  }

  function clearHighlight() {
    nodeSel.classed('node--dimmed node--selected', false);
    edgeSel.classed('edge--dimmed', false);
  }

  let _visibleTracks = null;
  let _minYear = null;
  let _maxYear = null;

  function _applyFilters() {
    nodeSel.style('display', d => {
      if (_visibleTracks && !_visibleTracks.has(d.track)) return 'none';
      if (_minYear !== null && d.year_start < _minYear) return 'none';
      if (_maxYear !== null && d.year_start > _maxYear) return 'none';
      return null;
    });
    edgeSel.style('display', d => {
      const srcOk = (!_visibleTracks || _visibleTracks.has(d.source.track)) &&
        (_minYear === null || d.source.year_start >= _minYear) &&
        (_maxYear === null || d.source.year_start <= _maxYear);
      const tgtOk = (!_visibleTracks || _visibleTracks.has(d.target.track)) &&
        (_minYear === null || d.target.year_start >= _minYear) &&
        (_maxYear === null || d.target.year_start <= _maxYear);
      return srcOk && tgtOk ? null : 'none';
    });
    simulation.alpha(0.08).restart();
  }

  function filterTracks(visibleTrackIds) {
    _visibleTracks = visibleTrackIds ? new Set(visibleTrackIds) : null;
    _applyFilters();
  }

  function filterYears(minYear, maxYear) {
    _minYear = minYear;
    _maxYear = maxYear;
    _applyFilters();
  }

  return { highlight, clearHighlight, filterTracks, filterYears, layout };
}

function edgePath(d) {
  const sx = d.source.x + d.source.width / 2;
  const sy = d.source.y;
  const ex = d.target.x - d.target.width / 2;
  const ey = d.target.y;
  if (Math.abs(sy - ey) < 2) return `M ${sx},${sy} L ${ex},${ey}`;
  const mx = (sx + ex) / 2;
  return `M ${sx},${sy} C ${mx},${sy} ${mx},${ey} ${ex},${ey}`;
}

function hexToFill(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgb(${Math.round(r * 0.12)},${Math.round(g * 0.12)},${Math.round(b * 0.12)})`;
}
```

- [ ] **Step 2: Run full test suite**

```bash
pnpm exec vitest run && uv run pytest tests/ -q
```

Expected: 6 JS tests PASS, 40 Python tests PASS.

- [ ] **Step 3: Build and verify**

```bash
uv run python pipeline/build.py && pnpm build
```

Expected:
```
Wrote 194 genres, 55 edges -> public/data/genres.json
✓ built in ~4s
```

- [ ] **Step 4: Manual browser check**

```bash
pnpm dev
```

Open `http://localhost:5173`. Verify:
- Nodes distribute without overlap (force settling visible on load)
- Track lanes stay visually separated
- Drag a node → it follows the cursor → release → it snaps back
- Click a node → ancestor path highlights + brief settling ripple
- Year slider and track filter badges still work
- Zoom/pan still works

- [ ] **Step 5: Commit**

```bash
git add src/graph/renderer.js
git commit -m "feat: force-directed layout with drag-snap-back interaction"
```

- [ ] **Step 6: Push**

```bash
git push
```

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
  const viewWidth  = wrapper.clientWidth;
  const viewHeight = wrapper.clientHeight;

  // X: 2× wider so years have room horizontally; zoom = 0.5 fits full width.
  // Y: 4× taller so nodes can spread vertically without overlapping;
  //    rendered height (4× × 0.5zoom) = 2× viewport → user pans to see all tracks.
  const LAYOUT_SCALE   = 2;
  const LAYOUT_SCALE_Y = 4;
  const layoutWidth  = viewWidth  * LAYOUT_SCALE;
  const layoutHeight = viewHeight * LAYOUT_SCALE_Y;
  const layout = computeLayout(data, layoutWidth, layoutHeight);

  while (labelsEl.firstChild) labelsEl.removeChild(labelsEl.firstChild);
  layout.tracks.forEach(track => {
    const div = document.createElement('div');
    div.className = 'track-label';
    // Divide by LAYOUT_SCALE_Y so labels match rendered (zoomed) track height
    div.style.height = `${layout.trackHeights.get(track.id) / LAYOUT_SCALE_Y}px`;
    div.style.color = track.color;
    div.textContent = track.label;
    labelsEl.appendChild(div);
  });

  const svg = d3.select(wrapper)
    .append('svg')
    .attr('class', 'graph-canvas')
    .attr('width', viewWidth)
    .attr('height', viewHeight);

  const zoomGroup = svg.append('g').attr('class', 'zoom-group');

  const zoomBehavior = d3.zoom()
    .scaleExtent([0.15, 4])
    .on('zoom', e => zoomGroup.attr('transform', e.transform));

  svg.call(zoomBehavior);
  svg.call(zoomBehavior.transform, d3.zoomIdentity.scale(1 / LAYOUT_SCALE));

  layout.tracks.forEach((track, i) => {
    if (i === 0) return;
    const y = layout.trackTops.get(track.id);
    zoomGroup.append('line')
      .attr('class', 'track-separator')
      .attr('x1', 0).attr('y1', y)
      .attr('x2', layoutWidth).attr('y2', y);
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
    .force('x', d3.forceX(d => d.tx).strength(0.2))
    .force('y', d3.forceY(d => d.ty).strength(0.9))
    .force('collide', forceRectCollide(16, 14, 6))
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
      simulation.alpha(0.3).restart();
    });

  nodeSel.call(drag);

  nodeSel
    .on('click', (event, d) => {
      event.stopPropagation();
      onNodeClick(d);
      highlight(d.id);
      simulation.alpha(0.08).restart();
    })
    .on('mouseover', (event, d) => {
      if (!_clickHighlightId) highlightHover(d.id);
    })
    .on('mouseout', () => {
      if (!_clickHighlightId) clearHighlight();
    });

  svg.on('click', () => { _clickHighlightId = null; clearHighlight(); onNodeClick(null); });

  let _clickHighlightId = null;

  function highlight(nodeId) {
    _clickHighlightId = nodeId;
    const relatedIds = new Set([nodeId]);
    const pathEdgeKeys = new Set();
    const queue = [nodeId];
    const visited = new Set([nodeId]);

    while (queue.length) {
      const id = queue.shift();
      layout.edges.forEach(e => {
        // ancestors
        if (e.target.id === id && !visited.has(e.source.id)) {
          visited.add(e.source.id);
          relatedIds.add(e.source.id);
          pathEdgeKeys.add(`${e.source.id}→${e.target.id}`);
          queue.push(e.source.id);
        }
        // descendants
        if (e.source.id === id && !visited.has(e.target.id)) {
          visited.add(e.target.id);
          relatedIds.add(e.target.id);
          pathEdgeKeys.add(`${e.source.id}→${e.target.id}`);
          queue.push(e.target.id);
        }
      });
    }

    nodeSel
      .classed('node--dimmed', d => !relatedIds.has(d.id))
      .classed('node--selected', d => relatedIds.has(d.id));
    edgeSel.classed('edge--dimmed',
      d => !pathEdgeKeys.has(`${d.source.id}→${d.target.id}`));
  }

  function highlightHover(nodeId) {
    const neighborIds = new Set([nodeId]);
    const edgeKeys = new Set();
    layout.edges.forEach(e => {
      if (e.source.id === nodeId) { neighborIds.add(e.target.id); edgeKeys.add(`${e.source.id}→${e.target.id}`); }
      if (e.target.id === nodeId) { neighborIds.add(e.source.id); edgeKeys.add(`${e.source.id}→${e.target.id}`); }
    });
    nodeSel
      .classed('node--dimmed', d => !neighborIds.has(d.id))
      .classed('node--selected', d => d.id === nodeId);
    edgeSel.classed('edge--dimmed', d => !edgeKeys.has(`${d.source.id}→${d.target.id}`));
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

// Rectangular collision force: resolves overlap along the axis with least penetration.
// Same-year nodes → pushed vertically; adjacent-year nodes → pushed horizontally.
// Rectangular collision force with constant-strength resolution (no alpha decay).
// Resolves along the axis of least penetration:
// same-year nodes → pushed vertically; adjacent-year nodes → pushed horizontally.
function forceRectCollide(xPad = 16, yPad = 6, iterations = 6) {
  let nodes;
  function force() {
    for (let k = 0; k < iterations; k++) {
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const gapX = (a.width + b.width) / 2 + xPad;
          const gapY = (a.height + b.height) / 2 + yPad;
          if (Math.abs(dx) < gapX && Math.abs(dy) < gapY) {
            const ox = gapX - Math.abs(dx);
            const oy = gapY - Math.abs(dy);
            // Bias toward vertical resolution when same track
            const sameTrack = a.track === b.track;
            if (!sameTrack && ox < oy) {
              const s = dx === 0 ? 1 : Math.sign(dx);
              b.x += ox * 0.5 * s;
              a.x -= ox * 0.5 * s;
            } else {
              const s = dy === 0 ? 1 : Math.sign(dy);
              b.y += oy * 0.5 * s;
              a.y -= oy * 0.5 * s;
            }
          }
        }
      }
    }
  }
  force.initialize = n => { nodes = n; };
  return force;
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

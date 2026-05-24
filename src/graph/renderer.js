import * as d3 from 'd3';
import { computeLayout } from './layout.js';

/**
 * Creates the D3 SVG graph.
 *
 * @param {HTMLElement} wrapper     - #canvas-wrapper
 * @param {HTMLElement} labelsEl    - #track-labels
 * @param {object}      data        - genres.json
 * @param {Function}    onNodeClick - callback(genreObject | null)
 * @returns {{ highlight, clearHighlight, filterTracks, filterYears }}
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
    .attr('stroke-dasharray', d => d.type === 'influence' ? '5,3' : null)
    .attr('d', edgePath);

  const nodeGroup = zoomGroup.append('g').attr('class', 'nodes');
  const nodeSel = nodeGroup.selectAll('g.node')
    .data(layout.nodes)
    .join('g')
    .attr('class', 'node')
    .attr('transform', d => `translate(${d.x - d.width / 2},${d.y - d.height / 2})`)
    .on('click', (event, d) => { event.stopPropagation(); onNodeClick(d); });

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

  svg.on('click', () => { clearHighlight(); onNodeClick(null); });

  function highlight(nodeId) {
    const neighborIds = new Set(
      layout.edges
        .filter(e => e.source.id === nodeId || e.target.id === nodeId)
        .flatMap(e => [e.source.id, e.target.id])
    );
    nodeSel
      .classed('node--dimmed', d => d.id !== nodeId && !neighborIds.has(d.id))
      .classed('node--selected', d => d.id === nodeId);
    edgeSel.classed('edge--dimmed',
      d => d.source.id !== nodeId && d.target.id !== nodeId);
  }

  function clearHighlight() {
    nodeSel.classed('node--dimmed node--selected', false);
    edgeSel.classed('edge--dimmed', false);
  }

  function filterTracks(visibleTrackIds) {
    const visible = new Set(visibleTrackIds);
    nodeSel.style('display', d => visible.has(d.track) ? null : 'none');
    edgeSel.style('display',
      d => visible.has(d.source.track) && visible.has(d.target.track) ? null : 'none');
  }

  function filterYears(minYear, maxYear) {
    nodeSel.style('display', d => d.year_start >= minYear && d.year_start <= maxYear ? null : 'none');
    edgeSel.style('display',
      d => d.source.year_start >= minYear && d.target.year_start <= maxYear ? null : 'none');
  }

  return { highlight, clearHighlight, filterTracks, filterYears };
}

function edgePath(d) {
  const sx = d.source.x + d.source.width / 2;
  const sy = d.source.y;
  const tx = d.target.x - d.target.width / 2;
  const ty = d.target.y;
  if (Math.abs(sy - ty) < 2) return `M ${sx},${sy} L ${tx},${ty}`;
  const cx = (sx + tx) / 2;
  return `M ${sx},${sy} C ${cx},${sy} ${cx},${ty} ${tx},${ty}`;
}

function hexToFill(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgb(${Math.round(r * 0.12)},${Math.round(g * 0.12)},${Math.round(b * 0.12)})`;
}

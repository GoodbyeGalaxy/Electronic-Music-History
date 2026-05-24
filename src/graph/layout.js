const YEAR_START = 1900;
export const YEAR_END = 2025;
const NODE_HEIGHT = 36;
const CHAR_WIDTH = 7;      // px per character at 10px font-size
const NODE_PADDING_X = 20; // horizontal padding per side
const NODE_GAP = 6;        // min horizontal gap between nodes on the same row

/**
 * Computes x/y positions for each node and resolves edge references.
 *
 * @param {object} data      - genres.json ({ genres, edges, tracks })
 * @param {number} svgWidth  - SVG canvas width in px
 * @param {number} svgHeight - SVG canvas height in px
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
    return { ...genre, x: xScale(genre.year_start), y: yScale(genre.track), width, height: NODE_HEIGHT };
  });

  // Assign rows within each track to prevent overlap
  const rowCounts = assignRows(nodes);
  for (const node of nodes) {
    const ti = trackIndex[node.track] ?? 0;
    const nr = rowCounts[node.track] ?? 1;
    node.y = (ti + (node._row + 0.5) / nr) * trackHeight;
    delete node._row;
  }

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

function assignRows(nodes) {
  const byTrack = {};
  for (const node of nodes) {
    (byTrack[node.track] ??= []).push(node);
  }
  const rowCounts = {};
  for (const [trackId, trackNodes] of Object.entries(byTrack)) {
    trackNodes.sort((a, b) => a.x - b.x);
    const rowEnds = [];
    for (const node of trackNodes) {
      const left = node.x - node.width / 2;
      const right = node.x + node.width / 2;
      let r = rowEnds.findIndex(end => left >= end + NODE_GAP);
      if (r === -1) r = rowEnds.length;
      node._row = r;
      rowEnds[r] = right;
    }
    rowCounts[trackId] = Math.max(rowEnds.length, 1);
  }
  return rowCounts;
}

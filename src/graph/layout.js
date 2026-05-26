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

  // Pre-distribute nodes sharing the same track+year bucket vertically
  // so the force simulation starts without overlaps and doesn't need to drift horizontally.
  const buckets = new Map();
  nodes.forEach(n => {
    const key = `${n.track}:${n.year_start}`;
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(n);
  });
  buckets.forEach(bucket => {
    if (bucket.length < 2) return;
    bucket.sort((a, b) => a.name.localeCompare(b.name));
    const step = NODE_HEIGHT + 4;
    const half = (bucket.length - 1) / 2;
    const maxOffset = (trackHeight / 2) - NODE_HEIGHT / 2 - 2;
    bucket.forEach((n, i) => {
      const raw = (i - half) * step;
      n.ty += Math.max(-maxOffset, Math.min(maxOffset, raw));
    });
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

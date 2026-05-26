const YEAR_START = 1900;
export const YEAR_END = 2025;
const NODE_HEIGHT = 36;
const CHAR_WIDTH = 7;
const NODE_PADDING_X = 20;
const MIN_TRACK_H = 40;

/**
 * Computes target positions (tx, ty) for each node and resolves edge references.
 * tx = year-based horizontal target; ty = track-centre vertical target.
 * The renderer owns x/y (current simulation positions).
 *
 * @param {object} data      - genres.json ({ genres, edges, tracks })
 * @param {number} svgWidth
 * @param {number} svgHeight
 * @returns {{ nodes, edges, tracks, trackHeights, trackTops, trackHeight }}
 *   trackHeights: Map<trackId, px>
 *   trackTops:    Map<trackId, px>  (top edge of each track band)
 *   trackHeight:  number            (average, for backwards-compat)
 */
export function computeLayout(data, svgWidth, svgHeight) {
  const { genres, edges, tracks } = data;

  const sortedTracks = [...tracks].sort((a, b) => a.order - b.order);
  const trackCount = sortedTracks.length;

  // --- Dynamic track heights proportional to genre count ---
  const genreCountPerTrack = new Map(sortedTracks.map(t => [t.id, 0]));
  genres.forEach(g => {
    if (genreCountPerTrack.has(g.track)) {
      genreCountPerTrack.set(g.track, genreCountPerTrack.get(g.track) + 1);
    }
  });

  const counts = sortedTracks.map(t => genreCountPerTrack.get(t.id) ?? 0);
  const totalGenres = counts.reduce((s, c) => s + c, 0);

  // Iterative flooring: tracks with too few genres get MIN_TRACK_H;
  // remaining space is distributed proportionally among the rest.
  const rawHeights = new Array(trackCount).fill(null);
  const pending = sortedTracks.map((_, i) => i);
  let remainingH = svgHeight;
  let remainingCount = totalGenres;

  let changed = true;
  while (changed && pending.length > 0) {
    changed = false;
    const scale = remainingCount > 0 ? remainingH / remainingCount : 0;
    for (let i = pending.length - 1; i >= 0; i--) {
      const idx = pending[i];
      if (counts[idx] * scale < MIN_TRACK_H) {
        rawHeights[idx] = MIN_TRACK_H;
        remainingH -= MIN_TRACK_H;
        remainingCount -= counts[idx];
        pending.splice(i, 1);
        changed = true;
      }
    }
  }

  const finalScale = remainingCount > 0 ? remainingH / remainingCount : 0;
  const scaledHeights = rawHeights.map((h, i) =>
    h !== null ? h : Math.round(counts[i] * finalScale)
  );

  // Fix integer rounding drift on last non-floored track
  const roundingDrift = svgHeight - scaledHeights.reduce((s, h) => s + h, 0);
  const lastPendingIdx = pending[pending.length - 1];
  if (lastPendingIdx !== undefined) scaledHeights[lastPendingIdx] += roundingDrift;

  const trackHeights = new Map(sortedTracks.map((t, i) => [t.id, scaledHeights[i]]));

  // Cumulative tops
  const trackTops = new Map();
  let cumY = 0;
  sortedTracks.forEach(t => {
    trackTops.set(t.id, cumY);
    cumY += trackHeights.get(t.id);
  });

  const xScale = year => ((year - YEAR_START) / (YEAR_END - YEAR_START)) * svgWidth;
  const yScale = trackId => {
    const top = trackTops.get(trackId);
    const h = trackHeights.get(trackId);
    if (top === undefined) {
      console.warn(`computeLayout: unknown trackId "${trackId}"`);
      return 0;
    }
    return top + h / 2;
  };

  const nodes = genres.map(genre => {
    const width = Math.max(genre.name.length * CHAR_WIDTH + NODE_PADDING_X * 2, 60);
    const tx = xScale(genre.year_start);
    const ty = yScale(genre.track);
    return { ...genre, tx, ty, width, height: NODE_HEIGHT };
  });

  // Pre-distribute nodes sharing the same track+year bucket vertically
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
    const trackH = trackHeights.get(bucket[0].track) ?? MIN_TRACK_H;
    const maxOffset = trackH / 2 - NODE_HEIGHT / 2 - 2;
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

  return {
    nodes,
    edges: resolvedEdges,
    tracks: sortedTracks,
    trackHeights,
    trackTops,
    trackHeight: svgHeight / trackCount, // backwards-compat for tests
  };
}

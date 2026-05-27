const YEAR_START = 1900;
export const YEAR_END = 2025;
const NODE_HEIGHT = 36;
const CHAR_WIDTH = 7;
const NODE_PADDING_X = 20;
const MIN_TRACK_H = 150;

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

  // Power scale: exponent >1 compresses early years and stretches later ones.
  const YEAR_SCALE_EXP = 1.5;
  const xScale = year => {
    const t = (year - YEAR_START) / (YEAR_END - YEAR_START);
    return Math.pow(t, YEAR_SCALE_EXP) * svgWidth;
  };
  const yScale = trackId => {
    const top = trackTops.get(trackId);
    const h = trackHeights.get(trackId);
    if (top === undefined) {
      console.warn(`computeLayout: unknown trackId "${trackId}"`);
      return 0;
    }
    return top + h / 2;
  };

  const childCount = new Map();
  genres.forEach(g => g.parents.forEach(pid => {
    childCount.set(pid, (childCount.get(pid) ?? 0) + 1);
  }));

  const nodes = genres.map(genre => {
    const width = Math.max(genre.name.length * CHAR_WIDTH + NODE_PADDING_X * 2, 60);
    const tx = xScale(genre.year_start);
    const ty = yScale(genre.track);
    return { ...genre, tx, ty, width, height: NODE_HEIGHT, childCount: childCount.get(genre.id) ?? 0 };
  });

  // --- Subgroup bands: vertical sub-lanes within a track ---
  // Collect unique subgroups per track, ordered by earliest member year_start.
  // Collect subgroups per track; sort by explicit subgroup_order if present,
  // else fall back to min year_start.
  const trackSgMeta = new Map(); // "trackId\0subgroup" → { order, year }
  nodes.forEach(n => {
    if (!n.subgroup) return;
    const key = `${n.track}\0${n.subgroup}`;
    const cur = trackSgMeta.get(key) ?? { order: Infinity, year: Infinity };
    if (n.subgroup_order != null) cur.order = Math.min(cur.order, n.subgroup_order);
    cur.year = Math.min(cur.year, n.year_start);
    trackSgMeta.set(key, cur);
  });
  const trackSubgroupOrder = new Map();
  trackSgMeta.forEach(({ order, year }, key) => {
    const sep = key.indexOf('\0');
    const trackId = key.slice(0, sep);
    const subgroup = key.slice(sep + 1);
    if (!trackSubgroupOrder.has(trackId)) trackSubgroupOrder.set(trackId, []);
    trackSubgroupOrder.get(trackId).push({ subgroup, sortKey: isFinite(order) ? order : year });
  });
  trackSubgroupOrder.forEach((sgs, trackId) => {
    sgs.sort((a, b) => a.sortKey - b.sortKey);
    trackSubgroupOrder.set(trackId, sgs.map(s => s.subgroup));
  });

  // Override ty to subgroup band centre; store hard band boundaries.
  nodes.forEach(n => {
    const order = trackSubgroupOrder.get(n.track);
    if (!order || !n.subgroup) return;
    const idx = order.indexOf(n.subgroup);
    const numBands = order.length;
    const top = trackTops.get(n.track);
    const h = trackHeights.get(n.track);
    const bandH = h / numBands;
    n.ty = top + bandH * idx + bandH / 2;
    n._bandH = bandH;
    n._bandTop = top + bandH * idx;
    n._bandBottom = n._bandTop + bandH;
    n._subgroupIdx = idx;
    n._numSubgroups = numBands;
  });

  // Subgrouped nodes: small year-based seed offset to break symmetry so the
  // simulation can resolve collisions. Step is intentionally small — the
  // simulation does the real spreading via collision + weak forceY.
  const sgBuckets = new Map();
  nodes.forEach(n => {
    if (!n.subgroup) return;
    const key = `${n.track}\0${n.subgroup}`;
    if (!sgBuckets.has(key)) sgBuckets.set(key, []);
    sgBuckets.get(key).push(n);
  });
  sgBuckets.forEach(bucket => {
    bucket.sort((a, b) => a.year_start - b.year_start || a.name.localeCompare(b.name));
    const half = (bucket.length - 1) / 2;
    bucket.forEach((n, i) => { n.ty += (i - half) * 12; });
  });

  // Non-subgrouped nodes: full year-window bucket distribution as before.
  const buckets = new Map();
  nodes.forEach(n => {
    if (n.subgroup) return;
    const key = `${n.track}\0${Math.floor(n.year_start / 5) * 5}`;
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(n);
  });
  buckets.forEach(bucket => {
    if (bucket.length < 2) return;
    bucket.sort((a, b) => a.year_start - b.year_start || a.name.localeCompare(b.name));
    const step = NODE_HEIGHT + 40;
    const half = (bucket.length - 1) / 2;
    const ref = bucket[0];
    const trackH = trackHeights.get(ref.track) ?? MIN_TRACK_H;
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

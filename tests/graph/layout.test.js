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

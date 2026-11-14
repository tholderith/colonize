import { describe, expect, it } from 'vitest';
import { generateMap } from '../src/sim/mapgen';
import { buildingDef, placementError } from '../src/sim/placement';
import { createRng } from '../src/sim/rng';
import { hashState, runHeadless, type TimedCommand } from '../src/sim/sim';
import { TILE_CLASSES, type Building, type GameMap } from '../src/sim/types';

const classes = (m: GameMap) => Array.from(m.tiles, (t) => TILE_CLASSES[t]);

function findLand(map: GameMap, w: number, h: number): [number, number] {
  for (let y = 0; y < map.h; y++)
    for (let x = 0; x < map.w; x++) {
      const def = { id: 'x', name: 'x', footprint: [w, h] as [number, number], terrain: ['land' as const], color: '#000', height: 1 };
      if (placementError(map, [], def, x, y) === null) return [x, y];
    }
  throw new Error('no land');
}

describe('rng', () => {
  it('is deterministic per seed', () => {
    const a = createRng(42), b = createRng(42), c = createRng(43);
    const sa = Array.from({ length: 20 }, () => a.next());
    expect(Array.from({ length: 20 }, () => b.next())).toEqual(sa);
    expect(Array.from({ length: 20 }, () => c.next())).not.toEqual(sa);
    expect(sa.every((v) => v >= 0 && v < 1)).toBe(true);
  });
});

describe('mapgen', () => {
  it('same seed gives same map, different seed differs', () => {
    expect(generateMap(7).tiles).toEqual(generateMap(7).tiles);
    expect(generateMap(7).tiles).not.toEqual(generateMap(8).tiles);
  });
  it('has 3 separate islands, all tile classes, for many seeds', () => {
    for (let seed = 1; seed <= 40; seed++) {
      const m = generateMap(seed);
      expect(new Set(classes(m))).toEqual(new Set(TILE_CLASSES));
      const solid = (i: number) => m.tiles[i]! >= 2;
      const seen = new Set<number>();
      let islands = 0;
      for (let i = 0; i < m.tiles.length; i++) {
        if (!solid(i) || seen.has(i)) continue;
        islands++;
        const stack = [i];
        while (stack.length) {
          const j = stack.pop()!;
          if (seen.has(j) || !solid(j)) continue;
          seen.add(j);
          const x = j % m.w, y = Math.floor(j / m.w);
          if (x > 0) stack.push(j - 1);
          if (x < m.w - 1) stack.push(j + 1);
          if (y > 0) stack.push(j - m.w);
          if (y < m.h - 1) stack.push(j + m.w);
        }
      }
      expect(islands, `seed ${seed}`).toBe(3);
    }
  });
});

describe('placement', () => {
  const map = generateMap(1337);
  const def = buildingDef('pod_house')!;
  it('accepts land, rejects water, occupied and out of bounds', () => {
    const [x, y] = findLand(map, 2, 2);
    expect(placementError(map, [], def, x, y)).toBeNull();
    expect(placementError(map, [], def, 0, 0)).toMatch(/deep/);
    expect(placementError(map, [], def, -1, 5)).toBe('out of bounds');
    expect(placementError(map, [], def, 64, 64)).toBe('out of bounds');
    const existing: Building[] = [{ id: 1, type: 'pod_house', x, y }];
    expect(placementError(map, existing, def, x, y)).toBe('tile occupied');
  });
});

describe('headless sim', () => {
  const map = generateMap(99);
  const [x, y] = findLand(map, 2, 2);
  const cmds: TimedCommand[] = [
    { tick: 5, cmd: { type: 'placeBuilding', building: 'pod_house', x, y } },
    { tick: 6, cmd: { type: 'placeBuilding', building: 'pod_house', x, y } }, // overlaps, rejected
    { tick: 10, cmd: { type: 'setSpeed', speed: 3 } },
    { tick: 20, cmd: { type: 'pause', paused: true } },
  ];
  it('same commands give same state hash; differing commands differ', () => {
    const a = runHeadless(99, cmds, 50);
    expect(hashState(a)).toBe(hashState(runHeadless(99, cmds, 50)));
    expect(hashState(a)).not.toBe(hashState(runHeadless(99, cmds.filter((c) => c.tick !== 10), 50)));
    expect(a.buildings).toHaveLength(1);
    expect(a.speed).toBe(3);
    expect(a.tick).toBe(20); // paused at tick 20
  });
  it('demolish removes the building', () => {
    const s = runHeadless(99, [...cmds.slice(0, 1), { tick: 8, cmd: { type: 'demolish', x, y } }], 10);
    expect(s.buildings).toHaveLength(0);
  });
});

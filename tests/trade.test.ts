import { describe, expect, it } from 'vitest';
import { levyRate } from '../src/sim/concordat';
import { exchangeTile, islands } from '../src/sim/mapgen';
import { findWaterPath } from '../src/sim/nav';
import { buildingDef, placementError } from '../src/sim/placement';
import { Sim, hashState } from '../src/sim/sim';
import { traderSpawn } from '../src/sim/trade';

/** Depot + port on an island, placed by command; returns the port id. */
function setupPort(sim: Sim, island: number): number {
  const tiles = islands(sim.map)[island]!;
  const { w } = sim.map;
  const cx = tiles.reduce((t, i) => t + (i % w), 0) / tiles.length;
  const cy = tiles.reduce((t, i) => t + Math.floor(i / w), 0) / tiles.length;
  const near = (def: string, ax: number, ay: number, maxD: number) => {
    const d = buildingDef(def)!;
    return tiles
      .map((i) => [i % w, Math.floor(i / w)] as [number, number])
      .filter(([x, y]) => Math.hypot(x - ax, y - ay) <= maxD && placementError(sim.map, sim.state.buildings, d, x, y) === null)
      .sort((a, b) => Math.hypot(a[0] - ax, a[1] - ay) - Math.hypot(b[0] - ax, b[1] - ay) || a[0] - b[0] || a[1] - b[1])[0];
  };
  const place = (id: string, p: [number, number] | undefined) => {
    if (!p) throw new Error(`no spot for ${id}`);
    sim.enqueue({ type: 'placeBuilding', building: id, x: p[0], y: p[1] });
    sim.flush();
    return sim.state.buildings[sim.state.buildings.length - 1]!;
  };
  const depot = place('depot', near('depot', cx, cy, 99));
  // Port must be within depot range and on a coast: sweep radius outwards until one fits.
  let p: [number, number] | undefined;
  for (let r = 3; r <= 9 && !p; r++) p = near('port', depot.x + 1, depot.y + 1, r);
  return place('port', p).id;
}

function twoPortWorld() {
  const sim = new Sim(1337);
  sim.state.credits = 5000;
  for (const isl of sim.state.islands) isl.stock.alloy = 200;
  const a = setupPort(sim, 0);
  const b = setupPort(sim, 1);
  return { sim, a, b };
}

describe('water pathfinding', () => {
  it('finds a path over water between the exchange and the trader spawn, and none onto land', () => {
    const sim = new Sim(1337);
    const e = exchangeTile(sim.map), t = traderSpawn(sim.map);
    const path = findWaterPath(sim.map, e.x, e.y, t.x, t.y);
    expect(path).not.toBeNull();
    expect(path![0]).toEqual([e.x, e.y]);
    expect(path![path!.length - 1]).toEqual([t.x, t.y]);
    const land = islands(sim.map)[0]![0]!;
    expect(findWaterPath(sim.map, e.x, e.y, land % sim.map.w, Math.floor(land / sim.map.w))).toBeNull();
  });
});

describe('haulers', () => {
  it('a route carries cargo from one island stock to another', () => {
    const { sim, a, b } = twoPortWorld();
    const before0 = sim.state.islands[0]!.stock.rations!;
    const before1 = sim.state.islands[1]!.stock.rations!;
    sim.enqueue({ type: 'buildHauler', port: a });
    sim.flush();
    const h = sim.state.haulers[0]!;
    sim.enqueue({
      type: 'setRoute', hauler: h.id,
      route: [
        { kind: 'port', building: a, orders: [{ good: 'rations', mode: 'load', amount: 20 }] },
        { kind: 'port', building: b, orders: [{ good: 'rations', mode: 'unload', amount: 20 }] },
      ],
    });
    for (let i = 0; i < 2500; i++) sim.step();
    expect(sim.state.islands[1]!.stock.rations).toBeGreaterThanOrEqual(before1 + 20);
    expect(sim.state.islands[0]!.stock.rations).toBeLessThanOrEqual(before0 - 20);
  });
});

describe('concordat', () => {
  it('levy maths: 10% base, +5% per population step, +5% penalty, -2% relief', () => {
    expect(levyRate(0, false, false)).toBe(10);
    expect(levyRate(25, false, false)).toBe(15);
    expect(levyRate(50, true, false)).toBe(25);
    expect(levyRate(0, false, true)).toBe(8);
  });

  it('takes the levy % of the credits earned at the end of the period', () => {
    const sim = new Sim(5);
    const s = sim.state;
    s.concordat.earned = 400;
    s.credits = 1000;
    s.tick = 2999;
    sim.step(); // tick 2999 -> 3000
    expect(s.credits).toBe(1000);
    sim.step(); // tick 3000: period over
    expect(s.credits).toBe(1000 - 40);
    expect(s.concordat.earned).toBe(0);
  });

  it('a met demand pays the reward and relieves the levy; a missed one fines and surcharges', () => {
    const met = new Sim(5);
    met.state.tick = 100;
    met.state.concordat.demand = { good: 'rations', amount: 20, delivered: 20, deadline: 2000, reward: 300, fine: 150 };
    met.state.concordat.nextDemandAt = 99999;
    const c0 = met.state.credits;
    met.step();
    expect(met.state.credits).toBe(c0 + 300);
    expect(met.state.concordat.demand).toBeNull();
    expect(met.state.concordat.relief).toBe(true);

    const missed = new Sim(5);
    missed.state.tick = 2000;
    missed.state.concordat.periodStart = 1900;
    missed.state.concordat.demand = { good: 'rations', amount: 20, delivered: 5, deadline: 2000, reward: 300, fine: 150 };
    missed.state.concordat.nextDemandAt = 99999;
    const c1 = missed.state.credits;
    missed.step();
    expect(missed.state.credits).toBe(c1 - 150);
    expect(missed.state.concordat.penaltyPeriods).toBe(2);
    missed.step();
    expect(missed.state.concordat.levyPct).toBe(15);
  });

  it('is deterministic with ships and events running', () => {
    const run = () => {
      const { sim, a, b } = twoPortWorld();
      sim.enqueue({ type: 'buildHauler', port: a });
      sim.flush();
      sim.enqueue({ type: 'setRoute', hauler: sim.state.haulers[0]!.id, route: [{ kind: 'port', building: a, orders: [] }, { kind: 'exchange', orders: [] }, { kind: 'port', building: b, orders: [] }] });
      for (let i = 0; i < 9000; i++) sim.step();
      return sim.state;
    };
    const x = run();
    expect(hashState(x)).toBe(hashState(run()));
    expect(x.concordat.log.length).toBeGreaterThan(0);
  });
});

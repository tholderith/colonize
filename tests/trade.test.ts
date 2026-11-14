import { describe, expect, it } from 'vitest';
import { levyRate } from '../src/sim/concordat';
import { exchangeTile, islands } from '../src/sim/mapgen';
import { findWaterPath } from '../src/sim/nav';
import { Sim, hashState } from '../src/sim/sim';
import { traderSpawn } from '../src/sim/trade';
import { setupPort } from './helpers';

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
  it('levy maths: 6% base, +3% per population step (+7% past 100 pop), +5% penalty, -2% relief', () => {
    expect(levyRate(0, false, false)).toBe(6);
    expect(levyRate(25, false, false)).toBe(9);
    expect(levyRate(100, false, false)).toBe(18);
    expect(levyRate(150, false, false)).toBe(32);
    expect(levyRate(50, true, false)).toBe(17);
    expect(levyRate(0, false, true)).toBe(4);
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
    expect(s.credits).toBe(1000 - 24);
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
    expect(missed.state.concordat.levyPct).toBe(11);
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

describe('route editing', () => {
  it('keeps the current stop when an unrelated order is edited', () => {
    const { sim, a, b } = twoPortWorld();
    sim.enqueue({ type: 'buildHauler', port: a });
    sim.flush();
    const h = sim.state.haulers[0]!;
    const stops = [a, b].map((id) => ({ kind: 'port' as const, building: id, orders: [] as never[] }));
    sim.enqueue({ type: 'setRoute', hauler: h.id, route: stops });
    sim.flush();
    h.stop = 1;
    sim.enqueue({ type: 'setRoute', hauler: h.id, route: [{ ...stops[0]!, orders: [{ good: 'scrap', mode: 'load', amount: 5 }] }, stops[1]!] });
    sim.flush();
    expect(h.stop).toBe(1);
  });
});

import { describe, expect, it } from 'vitest';
import { exchangeTile, islands } from '../src/sim/mapgen';
import { sentimentTick } from '../src/sim/independence';
import { IND, buildingDef, newBuilding, placementError } from '../src/sim/placement';
import { Sim, hashState } from '../src/sim/sim';
import { newHauler, newVisitor } from '../src/sim/trade';
import type { Difficulty } from '../src/sim/types';
import { setupPort } from './helpers';

const run = (sim: Sim, ticks: number) => {
  for (let i = 0; i < ticks; i++) sim.step();
};
const declared = (seed = 1337, difficulty: Difficulty = 'standard') => {
  const sim = new Sim(seed, difficulty);
  sim.state.ind.sentiment = 60;
  sim.enqueue({ type: 'declare' });
  sim.flush();
  return sim;
};
/** Put a battery on the nearest valid land to (x, y), bypassing cost. */
function addBattery(sim: Sim, x: number, y: number): [number, number] {
  const def = buildingDef('coastal_battery')!;
  const w = sim.map.w;
  const spots = islands(sim.map).flat().map((i) => [i % w, Math.floor(i / w)] as [number, number]).filter(([tx, ty]) => placementError(sim.map, sim.state.buildings, def, tx, ty) === null);
  spots.sort((a, b) => Math.hypot(a[0] - x, a[1] - y) - Math.hypot(b[0] - x, b[1] - y) || a[0] - b[0] || a[1] - b[1]);
  const p = spots[0]!;
  sim.state.buildings.push(newBuilding(sim.state.nextId++, def, p[0], p[1], 0));
  return p;
}

describe('sentiment', () => {
  it('rises with levy above 15%, technicians and relays; grievance pays out; calm pulls it down', () => {
    const sim = new Sim(1);
    const s = sim.state;
    s.pop.technicians = 10;
    s.concordat.levyPct = 25;
    for (let i = 0; i < 2; i++) s.buildings.push(newBuilding(s.nextId++, buildingDef('signal_relay')!, i, 0));
    sentimentTick(s);
    const S = IND.sentiment;
    expect(s.ind.drivers.levy).toBeCloseTo(10 * S.perLevyPct);
    expect(s.ind.drivers.tech).toBeCloseTo(10 * S.perTech);
    expect(s.ind.drivers.relay).toBeCloseTo(2 * S.perRelay);
    for (let i = 0; i < 599; i++) sentimentTick(s);
    expect(s.ind.sentiment).toBeCloseTo(10 * S.perLevyPct + 10 * S.perTech + 2 * S.perRelay, 2);
    // A missed demand pays out over time, then stops.
    const before = s.ind.sentiment;
    s.ind.grievance = S.missedDemand;
    for (let i = 0; i < 6000; i++) sentimentTick(s);
    expect(s.ind.grievance).toBe(0);
    expect(s.ind.sentiment).toBeGreaterThan(before + S.missedDemand);
    // Calm (demands met) falls slowly; levy at the floor adds nothing.
    s.concordat.levyPct = 15;
    s.pop.technicians = 0;
    s.buildings = [];
    s.ind.sentiment = 20;
    s.ind.calmUntil = 1e9;
    for (let i = 0; i < 600; i++) sentimentTick(s);
    expect(s.ind.sentiment).toBeCloseTo(20 - S.calmPerMin, 2);
  });

  it('cannot declare below the threshold', () => {
    const sim = new Sim(1);
    sim.state.ind.sentiment = IND.sentiment.declareAt - 1;
    sim.enqueue({ type: 'declare' });
    sim.flush();
    expect(sim.state.ind.declared).toBe(false);
  });
});

describe('declaring independence', () => {
  it('stops the levy and demands; the exchange closes', () => {
    const control = new Sim(7);
    control.state.concordat.earned = 1000;
    run(control, 3001);
    expect(control.state.credits).toBeLessThan(2000); // levy taken
    const sim = declared(7);
    sim.state.concordat.earned = 1000;
    run(sim, 6000);
    expect(sim.state.credits).toBe(2000);
    expect(sim.state.concordat.demand).toBeNull();
    expect(sim.state.concordat.levyPct).toBe(0);
    expect(sim.state.concordat.log.some((e) => e.kind === 'levy')).toBe(false);
    expect(sim.state.patrols.length).toBeGreaterThanOrEqual(2);
  });

  it('patrol count scales with time and difficulty', () => {
    const sim = declared(3, 'hard');
    run(sim, 300);
    expect(sim.state.patrols.length).toBe(IND.difficulty.hard.patrols[0]);
    run(sim, IND.blockade.growTicks * 2);
    expect(sim.state.patrols.length).toBe(IND.difficulty.hard.patrols[1]);
  });
});

describe('blockade patrols', () => {
  it('seize the cargo of a hauler within range, and not beyond it', () => {
    const sim = declared();
    const e = exchangeTile(sim.map);
    const near = newHauler(900, { x: e.x + 2, y: e.y }, 0);
    near.cargo = { rations: 10 };
    const far = newHauler(901, { x: e.x + 14, y: e.y }, 0);
    far.cargo = { alloy: 5 };
    sim.state.haulers.push(near, far);
    const c0 = sim.state.credits;
    run(sim, 3);
    expect(sim.state.credits).toBe(c0 - IND.blockade.seizePenalty);
    expect(near.cargo).toEqual({});
    expect(near.limp).toBeGreaterThan(0);
    expect(far.cargo).toEqual({ alloy: 5 });
    expect(sim.state.ind.seized).toBe(1);
    expect(sim.state.concordat.log.some((l) => l.kind === 'seized')).toBe(true);
  });

  it('keep out of battery range', () => {
    const minDist = (withBattery: boolean) => {
      const sim = declared(21);
      const b = withBattery ? addBattery(sim, 40, 42) : (() => {
        const t = new Sim(21);
        return addBattery(t, 40, 42);
      })();
      const cx = b[0] + 1, cy = b[1] + 1;
      let min = Infinity;
      for (let i = 0; i < 2500; i++) {
        sim.step();
        for (const p of sim.state.patrols) min = Math.min(min, Math.hypot(p.x - cx, p.y - cy));
      }
      return min;
    };
    expect(minDist(false)).toBeLessThan(IND.blockade.avoidRadius); // without it they sail through
    expect(minDist(true)).toBeGreaterThanOrEqual(IND.blockade.avoidRadius);
  });
});

describe('win and lose', () => {
  it('wins after 3 blockade cycles while solvent', () => {
    const sim = declared();
    run(sim, IND.blockade.cycleTicks * 3 - 5);
    expect(sim.state.outcome).toBeNull();
    run(sim, 10);
    expect(sim.state.outcome).toMatchObject({ win: true, cause: 'victory' });
    expect(sim.state.paused).toBe(true);
    expect(sim.state.stats.peakPop).toBe(0);
  });

  it('needs population at 80% of the declaration value to win', () => {
    const sim = declared();
    const def = buildingDef('pod_house')!;
    const houses = Array.from({ length: 10 }, (_, i) => {
      const h = newBuilding(sim.state.nextId++, def, i, 0);
      h.residents = 3;
      return h;
    });
    sim.state.buildings.push(...houses);
    sim.state.ind.popAtDeclare = 40;
    sim.state.ind.declaredAt = -IND.blockade.cycleTicks * 3; // three cycles already behind us
    run(sim, 2);
    expect(sim.state.ind.cycles).toBe(3);
    expect(sim.state.outcome).toBeNull(); // 30/40 = 75%: no win, and not a collapse either
    for (const h of houses) h.residents = 4;
    run(sim, 1);
    expect(sim.state.outcome).toMatchObject({ win: true });
  });

  it('loses by bankruptcy: credits < 0 for 2 consecutive levy periods (before declaring)', () => {
    const sim = new Sim(5);
    sim.state.credits = -1;
    run(sim, 3001);
    expect(sim.state.outcome).toBeNull();
    run(sim, 3000);
    expect(sim.state.outcome).toMatchObject({ win: false, cause: 'bankruptcy' });
  });

  it('loses by bankruptcy after declaring, but one solvent period resets the count', () => {
    const sim = declared();
    sim.state.credits = -1;
    run(sim, 3001);
    sim.state.credits = 10;
    run(sim, 3000);
    expect(sim.state.ind.negPeriods).toBe(0);
    sim.state.credits = -1;
    run(sim, 6000);
    expect(sim.state.outcome).toMatchObject({ cause: 'bankruptcy' });
  });

  it('loses by collapse when population falls under 50% of the declaration value', () => {
    const sim = declared();
    sim.state.ind.popAtDeclare = 40; // actual pop is 0
    run(sim, 2);
    expect(sim.state.outcome).toMatchObject({ win: false, cause: 'collapse' });
  });

  it('is suppressed after 3 audit fines at sentiment >= 30% without declaring', () => {
    const sim = new Sim(1337);
    sim.state.credits = 5000;
    for (const isl of sim.state.islands) isl.stock.alloy = 200;
    const port = setupPort(sim, 0);
    sim.state.ind.sentiment = 40;
    const e = exchangeTile(sim.map);
    for (let n = 1; n <= 3; n++) {
      sim.state.concordat.exposure = 100;
      sim.state.visitors.push(newVisitor(sim.state.nextId++, 'patrol', e, port));
      for (let i = 0; i < 1500 && sim.state.visitors.length && !sim.state.outcome; i++) sim.step();
      expect(sim.state.ind.suppressFines).toBe(n);
    }
    sim.step();
    expect(sim.state.outcome).toMatchObject({ win: false, cause: 'suppression' });
  });

  it('audit fines below the suppression threshold do not count', () => {
    const sim = new Sim(1337);
    sim.state.credits = 5000;
    for (const isl of sim.state.islands) isl.stock.alloy = 200;
    const port = setupPort(sim, 0);
    sim.state.concordat.exposure = 100;
    sim.state.visitors.push(newVisitor(sim.state.nextId++, 'patrol', exchangeTile(sim.map), port));
    for (let i = 0; i < 1500 && sim.state.visitors.length; i++) sim.step();
    expect(sim.state.ind.suppressFines).toBe(0);
    expect(sim.state.ind.grievance + sim.state.ind.sentiment).toBeGreaterThan(0); // the fine still angers the colony
  });
});

describe('saving', () => {
  it('save then load gives an identical hash, and the run continues identically', () => {
    const sim = declared(1337, 'hard');
    sim.state.credits = 5000;
    for (const isl of sim.state.islands) isl.stock.alloy = 200;
    const a = setupPort(sim, 0);
    const b = setupPort(sim, 1);
    sim.enqueue({ type: 'buildHauler', port: a });
    sim.flush();
    sim.enqueue({ type: 'setRoute', hauler: sim.state.haulers[0]!.id, route: [{ kind: 'port', building: a, orders: [{ good: 'rations', mode: 'load', amount: 10 }] }, { kind: 'port', building: b, orders: [{ good: 'rations', mode: 'unload', amount: 10 }] }] });
    addBattery(sim, 40, 42);
    run(sim, 800);
    const text = JSON.stringify(sim.toSave());
    const copy = Sim.fromSave(JSON.parse(text));
    expect(hashState(copy.state)).toBe(hashState(sim.state));
    run(sim, 600);
    run(copy, 600);
    expect(hashState(copy.state)).toBe(hashState(sim.state));
  });

  it('rejects other save versions', () => {
    const save = new Sim(1).toSave();
    expect(() => Sim.fromSave({ ...save, version: 99 })).toThrow();
  });
});

describe('determinism', () => {
  it('the same seed with the blockade running gives the same state', () => {
    const go = () => {
      const s = declared(55);
      run(s, 1500);
      return hashState(s.state);
    };
    expect(go()).toBe(go());
  });
});

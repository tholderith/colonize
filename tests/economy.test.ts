import { describe, expect, it } from 'vitest';
import { Sim } from '../src/sim/sim';
import { buildingDef, placementError } from '../src/sim/placement';
import type { Building } from '../src/sim/types';

/** Place buildings at the nearest free spots around the start depot; returns them in order. */
function build(sim: Sim, ids: string[]): Building[] {
  const depot = sim.state.buildings[0]!;
  const out: Building[] = [];
  for (const id of ids) {
    const def = buildingDef(id)!;
    const cands: [number, number][] = [];
    for (let y = depot.y - 6; y <= depot.y + 6; y++)
      for (let x = depot.x - 6; x <= depot.x + 6; x++) cands.push([x, y]);
    cands.sort((a, b) => Math.hypot(a[0] - depot.x - 1, a[1] - depot.y - 1) - Math.hypot(b[0] - depot.x - 1, b[1] - depot.y - 1));
    const spot = cands.find(([x, y]) => placementError(sim.map, sim.state.buildings, def, x, y) === null);
    if (!spot) throw new Error(`no spot for ${id}`);
    sim.enqueue({ type: 'placeBuilding', building: id, x: spot[0], y: spot[1] });
    sim.flush();
    out.push(sim.state.buildings[sim.state.buildings.length - 1]!);
  }
  return out;
}
const run = (sim: Sim, ticks: number) => {
  for (let i = 0; i < ticks; i++) sim.step();
};
const fresh = (ids: string[], stock: Record<string, number> = {}) => {
  const sim = new Sim(1337);
  sim.state.credits = 5000;
  Object.assign(sim.state.islands[0]!.stock, { alloy: 500, goods: 0 }, stock);
  const b = build(sim, ids);
  return { sim, b };
};

describe('economy', () => {
  it('a powered, staffed hydroponics makes 4 biomass per 150 ticks', () => {
    const { sim, b } = fresh(['wind_turbine', 'hydroponics', 'pod_house'], { rations: 1000 });
    b[2]!.residents = 4;
    run(sim, 1000);
    expect(b[1]!.status).toBe('working');
    expect(sim.state.islands[0]!.stock.biomass).toBe(24); // completions at ticks 149, 299, ... 899
  });

  it('a hydroponics -> ration plant chain makes rations', () => {
    const { sim, b } = fresh(['wind_turbine', 'hydroponics', 'ration_plant', 'pod_house', 'pod_house'], { rations: 50 });
    b[3]!.residents = 4;
    b[4]!.residents = 4;
    run(sim, 1200);
    const consumed = (8 * 0.4 * 1200) / 600;
    const made = sim.state.islands[0]!.stock.rations! - 50 + consumed;
    expect(made).toBeGreaterThanOrEqual(10);
    expect(made / 5).toBeCloseTo(Math.round(made / 5), 6);
  });

  it('an unpowered building runs at half rate', () => {
    const powered = fresh(['wind_turbine', 'hydroponics', 'pod_house'], { rations: 1000 });
    powered.b[2]!.residents = 4;
    const dark = fresh(['hydroponics', 'pod_house'], { rations: 1000 });
    dark.b[1]!.residents = 4;
    run(powered.sim, 900);
    run(dark.sim, 900);
    expect(dark.b[0]!.status).toBe('unpowered');
    expect(powered.sim.state.islands[0]!.stock.biomass).toBe(24);
    expect(dark.sim.state.islands[0]!.stock.biomass).toBe(12);
  });

  it('a house without workers reports no workers and does not produce', () => {
    const { sim, b } = fresh(['wind_turbine', 'hydroponics']);
    run(sim, 500);
    expect(b[1]!.status).toBe('no workers');
    expect(sim.state.islands[0]!.stock.biomass).toBe(0);
  });

  it('a house upgrades with goods available, and downgrades without needs', () => {
    const { sim, b } = fresh(['wind_turbine', 'pod_house'], { rations: 1000, goods: 60 });
    const house = b[1]!;
    house.residents = 2;
    run(sim, 1000);
    expect(house.tier).toBe(2);
    sim.state.islands[0]!.stock.goods = 0; // tier 2 now needs goods
    run(sim, 700);
    expect(house.tier).toBe(1);
    expect(house.residents).toBeLessThanOrEqual(4);
  });
});

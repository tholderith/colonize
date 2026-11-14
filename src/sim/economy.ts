import { ECON, GOODS, buildingDef } from './placement';
import type { Building, BuildingDef, GameState, IslandState, Status, Stock } from './types';

const TICKS_PER_MIN = 600;
const FLOW_SAMPLES = 60; // one per second

const centre = (b: Building, def: BuildingDef) => ({ x: b.x + def.footprint[0] / 2, y: b.y + def.footprint[1] / 2 });

export function emptyStock(): Stock {
  return Object.fromEntries(GOODS.filter((g) => g.id !== 'credits').map((g) => [g.id, 0]));
}

export function newIsland(id: number, name: string, stock: Stock): IslandState {
  return { id, name, stock: { ...emptyStock(), ...stock }, rates: emptyStock(), power: { supply: 0, demand: 0 }, flow: [], acc: {} };
}

/** Change an island's stock (tracked in its rolling rates). */
export function add(isl: IslandState, good: string, amt: number): void {
  isl.stock[good] = (isl.stock[good] ?? 0) + amt;
  isl.acc[good] = (isl.acc[good] ?? 0) + amt;
}

/** Change global credits (tracked in the credit rate). `earned` also counts towards the Concordat levy. */
export function addCredits(s: GameState, amt: number, earned = false): void {
  s.credits += amt;
  s.creditAcc += amt;
  if (amt > 0) s.stats.creditsEarned += amt;
  if (earned) s.concordat.earned += amt;
}

const has = (isl: IslandState, inputs: Record<string, number>) => Object.entries(inputs).every(([g, n]) => (isl.stock[g] ?? 0) >= n);

/** Advance the economy by one tick: every island is its own economy. */
export function economyTick(s: GameState): void {
  let lab = 0, tech = 0, labJobs = 0, techJobs = 0;
  for (const isl of s.islands) {
    const p = islandTick(s, isl);
    lab += p.lab;
    tech += p.tech;
    labJobs += p.labJobs;
    techJobs += p.techJobs;
  }
  s.pop = { laborers: lab, technicians: tech, laborerJobs: labJobs, technicianJobs: techJobs };

  // Rolling per-minute rates from per-second samples.
  if (s.tick % 10 === 9) {
    for (const isl of s.islands) {
      isl.flow.push(isl.acc);
      if (isl.flow.length > FLOW_SAMPLES) isl.flow.shift();
      isl.acc = {};
      const rates: Record<string, number> = {};
      for (const g of GOODS) rates[g.id] = (isl.flow.reduce((t, f) => t + (f[g.id] ?? 0), 0) * 60) / isl.flow.length;
      isl.rates = rates;
    }
    s.creditFlow.push(s.creditAcc);
    if (s.creditFlow.length > FLOW_SAMPLES) s.creditFlow.shift();
    s.creditAcc = 0;
    s.creditRate = (s.creditFlow.reduce((t, f) => t + f, 0) * 60) / s.creditFlow.length;
  }
}

function islandTick(s: GameState, isl: IslandState): { lab: number; tech: number; labJobs: number; techJobs: number } {
  const list = s.buildings.filter((b) => b.island === isl.id).map((b) => ({ b, def: buildingDef(b.type) as BuildingDef }));
  const depots = list.filter((o) => o.def.id === 'depot');
  const turbines = list.filter((o) => o.def.supply);
  const within = (o: { b: Building; def: BuildingDef }, src: typeof depots) => {
    const c = centre(o.b, o.def);
    return src.some((d) => {
      const dc = centre(d.b, d.def);
      return Math.hypot(c.x - dc.x, c.y - dc.y) <= (d.def.radius ?? 0);
    });
  };

  // Coverage and power (island-wide pool, coverage required).
  let supply = 0;
  for (const t of turbines) supply += t.def.supply ?? 0;
  let demand = 0;
  const turbCovered = new Map<number, boolean>();
  for (const o of list) {
    const c = within(o, turbines);
    turbCovered.set(o.b.id, c);
    o.b.covered = within(o, depots);
    if (c && o.def.draw) demand += o.def.draw;
  }
  isl.power = { supply, demand };
  const powerOk = supply >= demand;
  for (const o of list) o.b.powered = (turbCovered.get(o.b.id) ?? false) && powerOk;

  // Population and staffing.
  let lab = 0, tech = 0, labJobs = 0, techJobs = 0;
  for (const { b, def } of list) {
    if (def.house) {
      if (b.tier === 1) lab += b.residents;
      else tech += b.residents;
    }
    if (def.jobs) {
      if (def.worker === 'technician') techJobs += def.jobs;
      else labJobs += def.jobs;
    }
  }
  // Each type fills its own jobs first; spare workers of either type fill the other's open jobs
  // (otherwise goods, which need technicians, could never bootstrap, and upgrades would starve laborer jobs).
  const labOwn = Math.min(lab, labJobs);
  const techOwn = Math.min(tech, techJobs);
  const fracL = labJobs ? Math.min(1, (labOwn + (tech - techOwn)) / labJobs) : 1;
  const fracT = techJobs ? Math.min(1, (techOwn + (lab - labOwn)) / techJobs) : 1;

  const cap = ECON.storageCap * depots.length;

  for (const { b, def } of list) {
    if (def.cycle) {
      b.staffed = def.worker === 'technician' ? fracT : fracL;
      let status: Status | null = null;
      if (!b.covered) {
        status = 'no depot';
      } else {
        if (!b.running) {
          if (has(isl, def.inputs ?? {})) {
            for (const [g, n] of Object.entries(def.inputs ?? {})) add(isl, g, -n);
            b.running = true;
            b.progress = 0;
          } else status = 'no input';
        }
        if (b.running) {
          b.progress += (b.powered ? 1 : ECON.unpoweredSpeed) * b.staffed;
          if (b.progress >= def.cycle) {
            const out = Object.entries(def.outputs ?? {});
            if (out.every(([g, n]) => (isl.stock[g] ?? 0) + n <= cap)) {
              for (const [g, n] of out) add(isl, g, n);
              b.running = false;
              b.progress = 0;
            } else {
              b.progress = def.cycle;
              status = 'storage full';
            }
          }
        }
      }
      b.status = status ?? (b.staffed < 1 ? 'no workers' : !b.powered ? 'unpowered' : 'working');
    } else if (def.house) {
      tickHouse(s, isl, b);
    }
  }
  return { lab, tech, labJobs, techJobs };
}

function tickHouse(s: GameState, isl: IslandState, b: Building): void {
  const t = ECON.tiers[b.tier - 1]!;
  const n = Math.max(b.residents, 1);
  const need: Record<string, boolean> = { depot: b.covered, power: b.powered };
  const amounts: Record<string, number> = {};
  for (const [g, rate] of Object.entries(t.needsPerResidentPerMin)) {
    amounts[g] = (n * rate) / TICKS_PER_MIN;
    need[g] = (isl.stock[g] ?? 0) >= (amounts[g] as number);
  }
  b.needs = need;
  const met = Object.values(need).every(Boolean);
  if (met) {
    if (b.residents > 0) for (const [g, a] of Object.entries(amounts)) add(isl, g, -(a * b.residents) / n);
    b.unmet = 0;
    if (b.residents < t.capacity && ++b.grow >= ECON.growTicks) {
      b.residents++;
      b.grow = 0;
    }
    b.tax = (b.residents * t.taxPerResidentPerMin);
    addCredits(s, b.tax / TICKS_PER_MIN, true);
    // Tier 1 -> 2 needs a sustained goods supply: a stocked buffer for a long time, and the upgrade itself uses goods up.
    if (b.tier === 1 && b.residents > 0) {
      if ((isl.stock.goods ?? 0) >= ECON.upgradeMinGoods) {
        if (++b.upTimer >= ECON.upgradeTicks) {
          b.tier = 2;
          b.upTimer = 0;
          b.grow = 0;
          add(isl, 'goods', -ECON.upgradeGoods);
        }
      } else b.upTimer = Math.max(0, b.upTimer - 2);
    } else b.upTimer = 0;
    b.status = 'working';
  } else {
    b.tax = 0;
    b.upTimer = 0;
    b.grow = 0;
    b.unmet++;
    if (b.unmet % ECON.decayTicks === 0 && b.residents > 0) b.residents--;
    if (b.tier === 2 && b.unmet >= ECON.downgradeTicks) {
      b.tier = 1;
      b.unmet = 0;
      b.residents = Math.min(b.residents, ECON.tiers[0]!.capacity);
    }
    b.status = !b.covered ? 'no depot' : !b.powered ? 'unpowered' : 'no input';
  }
}

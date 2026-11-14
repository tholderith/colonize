// Headless balance run: fixed build list, 20 in-game minutes, per-minute stock + population.
import { GOODS, buildingDef, placementError, stockAtTile } from '../src/sim/placement';
import { islandAt, islands } from '../src/sim/mapgen';
import { Sim } from '../src/sim/sim';

const MINUTES = 20;
/** [minute, building id, count, island (default 0)] */
const PLAN: [number, string, number, number?][] = [
  [6, 'port', 1], [6, 'depot', 1, 1], [8, 'wind_turbine', 2, 1], [8, 'scrap_yard', 1, 1], [8, 'smelter', 1, 1], [8, 'pod_house', 4, 1], [9, 'port', 1, 1],
  [0, 'hydroponics', 1], [0, 'ration_plant', 1], [0, 'scrap_yard', 1], [0, 'smelter', 1], [0, 'wind_turbine', 2], [0, 'pod_house', 5],
  [2, 'algae_skimmer', 1], [2, 'wind_turbine', 1], [2, 'pod_house', 4],
  [4, 'fabricator', 1], [6, 'refinery', 1], [4, 'wind_turbine', 1], [4, 'pod_house', 4],
  [8, 'ration_plant', 1], [8, 'pod_house', 4], [12, 'ration_plant', 1], [10, 'wind_turbine', 1], [10, 'pod_house', 4],
];

const sim = new Sim(1337);
const centre = (island: number) => {
  const tiles = islands(sim.map)[island]!;
  const w = sim.map.w;
  return { x: tiles.reduce((t, i) => t + (i % w), 0) / tiles.length, y: tiles.reduce((t, i) => t + Math.floor(i / w), 0) / tiles.length };
};

function place(id: string, island: number): boolean {
  const def = buildingDef(id)!;
  const depot = sim.state.buildings.find((b) => b.type === 'depot' && b.island === island);
  const c = depot ? { x: depot.x + 1, y: depot.y + 1 } : centre(island);
  const R = id === 'depot' ? 12 : id === 'port' ? 10 : 9;
  let best: [number, number] | null = null;
  let bd = Infinity;
  for (let y = Math.floor(c.y) - R; y <= c.y + R; y++)
    for (let x = Math.floor(c.x) - R; x <= c.x + R; x++) {
      const d = Math.hypot(x - c.x, y - c.y);
      // Turbines sit ~3 out, houses in an outer ring, industry nearest-first.
      const score = id === 'wind_turbine' ? Math.abs(d - 3) : id === 'pod_house' ? Math.abs(d - 6) : d;
      if (d <= R && score < bd && islandOf(x, y) === island && placementError(sim.map, sim.state.buildings, def, x, y, stockOf(x, y)) === null) {
        best = [x, y];
        bd = score;
      }
    }
  if (!best) return false;
  sim.enqueue({ type: 'placeBuilding', building: id, x: best[0], y: best[1] });
  sim.flush();
  return true;
}
const islandOf = (x: number, y: number) => islandAt(sim.map, x, y);
const stockOf = (x: number, y: number) => stockAtTile(sim.map, sim.state, x, y);

/** One hauler: rations A -> B, alloy B -> A. */
function setupHauler(): void {
  const ports = [0, 1].map((i) => sim.state.buildings.find((b) => b.type === 'port' && b.island === i));
  if (!ports[0] || !ports[1]) return void failed.push('hauler: missing port');
  sim.enqueue({ type: 'buildHauler', port: ports[0].id });
  sim.flush();
  const h = sim.state.haulers[0];
  if (!h) return;
  sim.enqueue({
    type: 'setRoute', hauler: h.id,
    route: [
      { kind: 'port', building: ports[0].id, orders: [{ good: 'alloy', mode: 'unload', amount: 30 }, { good: 'rations', mode: 'load', amount: 15 }] },
      { kind: 'port', building: ports[1].id, orders: [{ good: 'rations', mode: 'unload', amount: 30 }, { good: 'alloy', mode: 'load', amount: 15 }] },
    ],
  });
  sim.flush();
}

const failed: string[] = [];
const pending: [string, number][] = [];
const cols = GOODS.map((g) => g.short.padStart(5));
console.log(`min ${cols.join('')}   LAB TECH  jobsL jobsT  pow   bldg  (stock = island 0 | island 1 rations/alloy)`);
const row = (m: number) => {
  const s = sim.state;
  const stock = GOODS.map((g) => String(Math.floor(g.id === 'credits' ? s.credits : (s.islands[0]!.stock[g.id] ?? 0))).padStart(5)).join('');
  const p = s.pop;
  console.log(
    `${String(m).padStart(3)} ${stock}  ${String(p.laborers).padStart(4)} ${String(p.technicians).padStart(4)}  ${String(p.laborerJobs).padStart(5)} ${String(p.technicianJobs).padStart(5)}  ${s.islands[0]!.power.demand}/${s.islands[0]!.power.supply}  ${s.buildings.length}  | ${Math.floor(s.islands[1]!.stock.rations ?? 0)}/${Math.floor(s.islands[1]!.stock.alloy ?? 0)} levy ${s.concordat.levyPct}%`,
  );
};
for (let m = 0; m <= MINUTES; m++) {
  if (m > 0) for (let t = 0; t < 600; t++) sim.step();
  row(m);
    for (const [at, id, n, isl] of PLAN) if (at === m && m < MINUTES) for (let i = 0; i < n; i++) pending.push([id, isl ?? 0]);
  // Unaffordable entries wait and retry each minute (the colony is credit-limited).
  for (let i = 0; i < pending.length; ) {
    if (place(pending[i]![0], pending[i]![1])) pending.splice(i, 1);
    else i++;
  }
  if (!sim.state.haulers.length && [0, 1].every((i) => sim.state.buildings.some((b) => b.type === 'port' && b.island === i))) setupHauler();
}
const s = sim.state;
console.log(`haulers ${s.haulers.length}, concordat events ${s.concordat.seq}, credits earned this period ${Math.floor(s.concordat.earned)} (period start tick ${s.concordat.periodStart}, tick ${s.tick})`);
const tiers = [1, 2].map((t) => s.buildings.filter((b) => b.type === 'pod_house' && b.tier === t).length);
console.log(`houses tier1/tier2: ${tiers.join('/')}; statuses: ${JSON.stringify(Object.fromEntries([...new Set(s.buildings.map((b) => b.status))].map((k) => [k, s.buildings.filter((b) => b.status === k).length])))}`);
console.log(`rates/min: ${GOODS.map((g) => `${g.short} ${(g.id === 'credits' ? s.creditRate : (s.islands[0]!.rates[g.id] ?? 0)).toFixed(1)}`).join('  ')}`);
for (const [id, isl] of pending) failed.push(`${id}@${isl}`);
if (failed.length) console.log(`could not place: ${failed.join(', ')}`);

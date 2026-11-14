// Headless balance run: fixed build list, 20 in-game minutes, per-minute stock + population.
import { GOODS, buildingDef, placementError } from '../src/sim/placement';
import { Sim } from '../src/sim/sim';

const MINUTES = 20;
/** [minute, building id, count] */
const PLAN: [number, string, number][] = [
  [0, 'hydroponics', 1], [0, 'ration_plant', 1], [0, 'scrap_yard', 1], [0, 'smelter', 1], [0, 'wind_turbine', 2], [0, 'pod_house', 5],
  [2, 'algae_skimmer', 1], [2, 'wind_turbine', 1], [2, 'pod_house', 4],
  [4, 'fabricator', 1], [6, 'refinery', 1], [4, 'wind_turbine', 1], [4, 'pod_house', 4],
  [8, 'ration_plant', 1], [8, 'pod_house', 4], [12, 'ration_plant', 1], [10, 'wind_turbine', 1], [10, 'pod_house', 4],
];

const sim = new Sim(1337);
const depot = sim.state.buildings[0]!;
const dx = depot.x + 1, dy = depot.y + 1;
const R = 9;

function place(id: string): boolean {
  const def = buildingDef(id)!;
  let best: [number, number] | null = null;
  let bd = Infinity;
  for (let y = dy - R; y <= dy + R; y++)
    for (let x = dx - R; x <= dx + R; x++) {
      const d = Math.hypot(x - dx, y - dy);
      // Turbines sit ~3 out, houses in an outer ring, industry nearest-first.
      const score = id === 'wind_turbine' ? Math.abs(d - 3) : id === 'pod_house' ? Math.abs(d - 6) : d;
      if (d <= R && score < bd && placementError(sim.map, sim.state.buildings, def, x, y, sim.state.stock) === null) {
        best = [x, y];
        bd = score;
      }
    }
  if (!best) return false;
  sim.enqueue({ type: 'placeBuilding', building: id, x: best[0], y: best[1] });
  sim.flush();
  return true;
}

const cols = GOODS.map((g) => g.short.padStart(5));
console.log(`min ${cols.join('')}   LAB TECH  jobsL jobsT  pow   bldg`);
const row = (m: number) => {
  const s = sim.state;
  const stock = GOODS.map((g) => String(Math.floor(s.stock[g.id] ?? 0)).padStart(5)).join('');
  const p = s.pop;
  console.log(
    `${String(m).padStart(3)} ${stock}  ${String(p.laborers).padStart(4)} ${String(p.technicians).padStart(4)}  ${String(p.laborerJobs).padStart(5)} ${String(p.technicianJobs).padStart(5)}  ${s.power.demand}/${s.power.supply}  ${s.buildings.length}`,
  );
};
const failed: string[] = [];
for (let m = 0; m <= MINUTES; m++) {
  if (m > 0) for (let t = 0; t < 600; t++) sim.step();
  row(m);
  for (const [at, id, n] of PLAN) if (at === m && m < MINUTES) for (let i = 0; i < n; i++) if (!place(id)) failed.push(`min ${m}: ${id}`);
}
const s = sim.state;
const tiers = [1, 2].map((t) => s.buildings.filter((b) => b.type === 'pod_house' && b.tier === t).length);
console.log(`houses tier1/tier2: ${tiers.join('/')}; statuses: ${JSON.stringify(Object.fromEntries([...new Set(s.buildings.map((b) => b.status))].map((k) => [k, s.buildings.filter((b) => b.status === k).length])))}`);
console.log(`rates/min: ${GOODS.map((g) => `${g.short} ${(s.rates[g.id] ?? 0).toFixed(1)}`).join('  ')}`);
if (failed.length) console.log(`could not place: ${failed.join(', ')}`);

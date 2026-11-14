// Headless balance run: fixed build list, per-minute stock + population + independence sentiment.
// Declares at 50% sentiment (batteries placed beforehand) and plays the blockade out; reports time to 50% and win/loss.
import { GOODS, buildingDef, placementError, stockAtTile } from '../src/sim/placement';
import { islandAt, islands } from '../src/sim/mapgen';
import { sentimentRate } from '../src/sim/independence';
import { Sim } from '../src/sim/sim';
import type { Difficulty } from '../src/sim/types';

const RELAYS_EARLY = 2;
const RELAYS_LATE = 2;
const MINUTES = 70;
const DIFFICULTY = (process.argv[2] ?? 'standard') as Difficulty;
/** Batteries built before declaring: `npm run sim:balance -- hard 3`. */
const BATTERIES = Number(process.argv[3] ?? 2);
/** [minute, building id, count, island (default 0)] */
const PLAN: [number, string, number, number?][] = [
  [6, 'port', 1], [6, 'depot', 1, 1], [8, 'wind_turbine', 2, 1], [8, 'scrap_yard', 1, 1], [8, 'smelter', 1, 1], [8, 'pod_house', 4, 1], [9, 'port', 1, 1],
  [0, 'hydroponics', 1], [0, 'ration_plant', 1], [0, 'scrap_yard', 1], [0, 'smelter', 1], [0, 'wind_turbine', 2], [0, 'pod_house', 5],
  [2, 'algae_skimmer', 1], [2, 'wind_turbine', 1], [2, 'pod_house', 4],
  [4, 'fabricator', 1], [6, 'refinery', 1], [4, 'wind_turbine', 1], [4, 'pod_house', 4],
  [8, 'ration_plant', 1], [8, 'pod_house', 4], [12, 'ration_plant', 1], [10, 'wind_turbine', 1], [10, 'pod_house', 4],
  [14, 'wind_turbine', 1], [14, 'pod_house', 4], [14, 'fabricator', 1], [14, 'ration_plant', 1],
  // Independence: relays from minute 12, two batteries before the declaration (island 0 and 1 coasts).
  [12, 'signal_relay', RELAYS_EARLY], [18, 'signal_relay', RELAYS_LATE],
  [16, 'coastal_battery', 1], [16, 'coastal_battery', 1, 1],
  ...(Array.from({ length: Math.max(0, BATTERIES - 2) }, (_, i) => [17 + i, 'coastal_battery', 1, i % 2] as [number, string, number, number])),
];

const sim = new Sim(1337, DIFFICULTY);
const centre = (island: number) => {
  const tiles = islands(sim.map)[island]!;
  const w = sim.map.w;
  return { x: tiles.reduce((t, i) => t + (i % w), 0) / tiles.length, y: tiles.reduce((t, i) => t + Math.floor(i / w), 0) / tiles.length };
};

function place(id: string, island: number): boolean {
  const def = buildingDef(id)!;
  const depot = sim.state.buildings.find((b) => b.type === 'depot' && b.island === island);
  let c = depot ? { x: depot.x + 1, y: depot.y + 1 } : centre(island);
  // Batteries guard the sea lane: the first per island at its port, extras on the coast nearest the lane midpoint.
  const ports = [0, 1].map((i) => sim.state.buildings.find((b) => b.type === 'port' && b.island === i));
  const nBat = sim.state.buildings.filter((b) => b.type === 'coastal_battery').length;
  const port = ports[island];
  if (id === 'coastal_battery' && port) c = nBat < 2 ? { x: port.x + 1, y: port.y + 1 } : { x: (ports[0]!.x + ports[1]!.x) / 2, y: (ports[0]!.y + ports[1]!.y) / 2 };
  const R = id === 'depot' ? 12 : id === 'port' ? 10 : id === 'coastal_battery' && nBat >= 2 ? 25 : 9;
  let best: [number, number] | null = null;
  let bd = Infinity;
  for (let y = Math.floor(c.y) - R; y <= c.y + R; y++)
    for (let x = Math.floor(c.x) - R; x <= c.x + R; x++) {
      const d = Math.hypot(x - c.x, y - c.y);
      // Turbines sit ~3 out, houses in an outer ring, industry nearest-first.
      const score = id === 'coastal_battery' && nBat >= 2 ? Math.hypot(x - c.x, y - c.y) : id === 'wind_turbine' ? Math.abs(d - 3) : id === 'pod_house' ? Math.abs(d - 6) : d;
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
console.log(`min ${cols.join('')}   LAB TECH  jobsL jobsT  pow   bldg  (stock = island 0 | island 1 rations/alloy)  sentiment`);
const row = (m: number) => {
  const s = sim.state;
  const stock = GOODS.map((g) => String(Math.floor(g.id === 'credits' ? s.credits : (s.islands[0]!.stock[g.id] ?? 0))).padStart(5)).join('');
  const p = s.pop;
  console.log(
    `${String(m).padStart(3)} ${stock}  ${String(p.laborers).padStart(4)} ${String(p.technicians).padStart(4)}  ${String(p.laborerJobs).padStart(5)} ${String(p.technicianJobs).padStart(5)}  ${s.islands[0]!.power.demand}/${s.islands[0]!.power.supply}  ${s.buildings.length}  | ${Math.floor(s.islands[1]!.stock.rations ?? 0)}/${Math.floor(s.islands[1]!.stock.alloy ?? 0)} levy ${s.concordat.levyPct}%  sent ${s.ind.sentiment.toFixed(1)}% (${sentimentRate(s.ind) >= 0 ? '+' : ''}${sentimentRate(s.ind).toFixed(2)}/m)${s.ind.declared ? ` BLOCKADE cycle ${s.ind.cycles} patrols ${s.patrols.length} seized ${s.ind.seized}` : ''}`,
  );
};
let minCredits = Infinity;
let t50: number | null = null;
let declaredAtTick: number | null = null;
const batteryCount = () => sim.state.buildings.filter((b) => b.type === 'coastal_battery').length;
for (let m = 0; m <= MINUTES && !sim.state.outcome; m++) {
  if (m > 0)
    for (let t = 0; t < 600 && !sim.state.outcome; t++) {
      const s = sim.state;
      if (t50 === null && s.ind.sentiment >= 50) t50 = s.tick;
      if (!s.ind.declared && s.ind.sentiment >= 50 && batteryCount() >= BATTERIES) {
        sim.enqueue({ type: 'declare' });
        declaredAtTick = s.tick;
      }
      // No free-trader income: the scripted player must live off its own islands.
      if (s.ind.declared) minCredits = Math.min(minCredits, s.credits);
      sim.step();
    }
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
const min = (tk: number | null) => (tk === null ? 'never' : `${(tk / 600).toFixed(1)} min`);
console.log(`\nRESULT (${DIFFICULTY}): sentiment reached 50% at ${min(t50)}; declared at ${min(declaredAtTick)}; ` +
  (s.outcome ? `${s.outcome.win ? 'WON' : 'LOST'} (${s.outcome.cause}) at ${min(s.outcome.tick)}` : `no outcome by minute ${MINUTES}`) +
  `; min credits under blockade ${Math.floor(minCredits)}; seized ${s.ind.seized}; peak pop ${s.stats.peakPop}; credits ${Math.floor(s.credits)}`);
console.log(`haulers ${s.haulers.length}, concordat events ${s.concordat.seq}, credits earned this period ${Math.floor(s.concordat.earned)} (period start tick ${s.concordat.periodStart}, tick ${s.tick})`);
const tiers = [1, 2].map((t) => s.buildings.filter((b) => b.type === 'pod_house' && b.tier === t).length);
console.log(`houses tier1/tier2: ${tiers.join('/')}; statuses: ${JSON.stringify(Object.fromEntries([...new Set(s.buildings.map((b) => b.status))].map((k) => [k, s.buildings.filter((b) => b.status === k).length])))}`);
console.log(`rates/min: ${GOODS.map((g) => `${g.short} ${(g.id === 'credits' ? s.creditRate : (s.islands[0]!.rates[g.id] ?? 0)).toFixed(1)}`).join('  ')}`);
for (const [id, isl] of pending) failed.push(`${id}@${isl}`);
if (failed.length) console.log(`could not place: ${failed.join(', ')}`);

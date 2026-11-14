import { Renderer } from './render/renderer';
import type { FromWorker, ToWorker } from './sim/protocol';
import { generateMap, islandAt, islands } from './sim/mapgen';
import { buildingAt, buildingDef, placementError, stockAtTile } from './sim/placement';
import type { Command, GameState, Stop } from './sim/types';
import { Ui } from './ui/ui';

const seed = Number(new URLSearchParams(location.search).get('seed') ?? 1337);
const map = generateMap(seed);
let state: GameState | null = null;
let selected: number | null = null;
let selectedHauler: number | null = null;

const worker = new Worker(new URL('./sim/worker.ts', import.meta.url), { type: 'module' });
const send = (m: ToWorker) => worker.postMessage(m);
const command = (cmd: Command) => send({ type: 'command', cmd });

const ui = new Ui({
  onSpeed: (v) => (v === 0 ? command({ type: 'pause', paused: !state?.paused }) : (command({ type: 'pause', paused: false }), command({ type: 'setSpeed', speed: v }))),
  onSelectTool: (def) => {
    renderer.setGhost(def);
    if (def) select(null);
  },
  onDemolish: (b) => {
    command({ type: 'demolish', x: b.x, y: b.y });
    select(null);
  },
  onBuildHauler: (b) => command({ type: 'buildHauler', port: b.id }),
  onSetRoute: (hauler, route) => command({ type: 'setRoute', hauler, route }),
  onScrapHauler: (hauler) => {
    command({ type: 'scrapHauler', hauler });
    selectHauler(null);
  },
  onTrade: () => command({ type: 'tradeWithTrader' }),
  onExchangeOrder: (good, mode, amount) => {
    const h = state?.haulers.find((o) => o.id === selectedHauler);
    if (!h) return ui.toast('Select a hauler first');
    const route: Stop[] = JSON.parse(JSON.stringify(h.route));
    let stop = route.find((s) => s.kind === 'exchange');
    if (!stop) route.push((stop = { kind: 'exchange', orders: [] }));
    const o = stop.orders.find((x) => x.good === good && x.mode === mode);
    if (o) o.amount = amount;
    else stop.orders.push({ good, mode, amount });
    command({ type: 'setRoute', hauler: h.id, route });
  },
});

const renderer = new Renderer(map, {
  onTileHover: (x, y) => updatePlaceInfo(x, y),
  onTileClick: (x, y) => {
    const tool = ui.activeTool;
    const pick = ui.trade.picking;
    if (pick !== null && state) {
      const port = buildingAt(state.buildings, x, y);
      const h = state.haulers.find((o) => o.id === pick);
      if (port?.type === 'port' && h) {
        command({ type: 'setRoute', hauler: h.id, route: [...JSON.parse(JSON.stringify(h.route)), { kind: 'port', building: port.id, orders: [] }] });
        ui.trade.picking = null;
      } else ui.toast('That is not a port');
    } else if (tool) {
      const err = state ? placementError(map, state.buildings, tool, x, y, stockAtTile(map, state, x, y)) : 'loading';
      if (err === null) command({ type: 'placeBuilding', building: tool.id, x, y });
      else if (tool.id !== 'road' || !err.includes('occupied')) ui.toast(err);
    } else {
      const h = renderer.haulerAt(x, y);
      if (h !== null) selectHauler(h);
      else select(state ? (buildingAt(state.buildings, x, y)?.id ?? null) : null);
    }
  },
});

function updatePlaceInfo(x: number, y: number): void {
  const tool = ui.activeTool;
  if (!tool || !state) return;
  ui.setPlaceInfo(tool, x < 0 ? null : placementError(map, state.buildings, tool, x, y, stockAtTile(map, state, x, y)));
}

function selectHauler(id: number | null): void {
  if (id !== null) select(null);
  selectedHauler = id;
  ui.trade.selectHauler(id);
  renderer.setSelectedShip(id);
}

/** Island the HUD shows: the selection's, else the one under the camera centre. */
function hudIsland(): number {
  const b = state?.buildings.find((o) => o.id === selected);
  if (b) return b.island;
  const h = state?.haulers.find((o) => o.id === selectedHauler);
  if (h) return islandAt(map, h.x, h.y);
  const c = renderer.centreTile();
  return islandAt(map, c.x, c.y);
}

function select(id: number | null): void {
  if (id !== null && selectedHauler !== null) selectHauler(null);
  selected = id;
  renderer.setSelected(id);
  ui.showInfo(state?.buildings.find((b) => b.id === id) ?? null, state ?? undefined);
}

worker.onmessage = (e: MessageEvent<FromWorker>) => {
  state = e.data.state;
  ui.setState(state, hudIsland());
  renderer.setState(state);
  const sel = state.buildings.find((b) => b.id === selected);
  if (selected !== null && !sel) select(null);
  else if (sel) ui.updateInfo(sel, state);
};

setInterval(() => state && ui.setState(state, hudIsland()), 300); // camera moves between snapshots (and while paused)

await renderer.init(document.getElementById('map') as HTMLElement);
send({ type: 'init', seed });

// Test/tooling hook.
(window as unknown as { __foundry: unknown }).__foundry = {
  seed,
  ready: () => state !== null,
  canPlace: (id: string, x: number, y: number) => {
    const def = buildingDef(id);
    return !!def && !!state && placementError(map, state.buildings, def, x, y) === null;
  },
  tileToScreen: (x: number, y: number) => renderer.tileToScreen(x, y),
  state: () => state,
  command,
  /** Nearest tile to (cx, cy) within r where `id` can be placed (ignores cost). */
  spot: (id: string, cx: number, cy: number, r: number) => {
    const def = buildingDef(id);
    if (!def || !state) return null;
    let best: [number, number] | null = null, bd = Infinity;
    for (let y = Math.floor(cy - r); y <= cy + r; y++)
      for (let x = Math.floor(cx - r); x <= cx + r; x++) {
        const d = Math.hypot(x - cx, y - cy);
        if (d <= r && d < bd && placementError(map, state.buildings, def, x, y) === null) { best = [x, y]; bd = d; }
      }
    return best;
  },
  islandCentre: (i: number) => {
    const t = islands(map)[i] ?? [];
    return { x: t.reduce((a, k) => a + (k % map.w), 0) / t.length, y: t.reduce((a, k) => a + Math.floor(k / map.w), 0) / t.length };
  },
  shipToScreen: (id: number) => renderer.shipToScreen(id),
  place: (building: string, x: number, y: number) => command({ type: 'placeBuilding', building, x, y }),
};

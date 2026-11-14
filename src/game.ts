import { Renderer, type RendererEvents } from './render/renderer';
import type { FromWorker, ToWorker } from './sim/protocol';
import { generateMap, islandAt, islands } from './sim/mapgen';
import type { SaveData } from './sim/sim';
import { IndependenceUi } from './ui/independence-ui';
import { Objectives } from './ui/objectives';
import { downloadSave, readSave, saveMeta, writeSave, type StartDesc } from './ui/saves';
import { buildingAt, buildingDef, placementError, stockAtTile } from './sim/placement';
import { dayOf, hourOfDay } from './sim/time';
import type { Command, GameMap, GameState, Stop } from './sim/types';
import { Ui, type UiEvents } from './ui/ui';

let seed = 0;
let map!: GameMap;
let state: GameState | null = null;
let selected: number | null = null;
let selectedHauler: number | null = null;
let shiftHeld = false;
/** Dev/test override of the time of day (hours); null follows the sim. */
let hourOverride: number | null = null;
const hourNow = () => hourOverride ?? hourOfDay(state?.tick ?? 0);

const worker = new Worker(new URL('./sim/worker.ts', import.meta.url), { type: 'module' });
const send = (m: ToWorker) => worker.postMessage(m);
const command = (cmd: Command) => send({ type: 'command', cmd });

let ui!: Ui;
let renderer!: Renderer;
let ind!: IndependenceUi;
let objectives!: Objectives;
/** Last concordat log entry the renderer has reacted to (seizure flashes). */
let seenLog = -1;

const uiEvents: UiEvents = {
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
  onSave: () => send({ type: 'save', slot: 'manual' }),
  onExport: () => send({ type: 'save', slot: 'export' }),
  onLoad: () => {
    const data = readSave('manual') ?? readSave('auto');
    const meta = saveMeta(data);
    if (!data || !meta) return ui.toast('No save to load');
    if (meta.seed !== seed) return ui.toast(`That save is from seed ${meta.seed}: load it from the main menu`);
    ui.confirm(`Load the saved game (${Math.floor(meta.tick / 600)} min played)? Unsaved progress is lost.`, 'LOAD', () => {
      resetClient();
      send({ type: 'load', data });
    });
  },
};

/** Forget everything tied to the previous game before a load or restart. */
function resetClient(): void {
  select(null);
  selectHauler(null);
  ui.setTool(null);
  renderer.reset();
  ind.reset();
  objectives.reset();
  seenLog = -1;
  state = null;
}

/** Esc: drop the tool and close every open panel. */
function closePanels(): void {
  ui.setTool(null);
  ui.closeConfirm();
  select(null);
  selectHauler(null);
  for (const [panel, btn] of [['concordat', 'btn-concordat'], ['exchange', 'btn-exchange']] as const) {
    document.getElementById(panel)!.hidden = true;
    document.getElementById(btn)!.classList.remove('active');
  }
}

const rendererEvents: RendererEvents = {
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
    } else if (tool && state && tool.id !== 'road' && buildingAt(state.buildings, x, y)) {
      // Clicking an existing building selects it and disarms the tool.
      ui.setTool(null);
      select(buildingAt(state.buildings, x, y)?.id ?? null);
    } else if (tool) {
      const err = state ? placementError(map, state.buildings, tool, x, y, stockAtTile(map, state, x, y)) : 'loading';
      if (err === null) {
        command({ type: 'placeBuilding', building: tool.id, x, y });
        if (!shiftHeld && tool.id !== 'road') ui.setTool(null); // one placement per pick; Shift keeps the tool
      }
      else if (tool.id !== 'road' || !err.includes('occupied')) ui.toast(err);
    } else {
      const h = renderer.haulerAt(x, y);
      if (h !== null) selectHauler(h);
      else select(state ? (buildingAt(state.buildings, x, y)?.id ?? null) : null);
    }
  },
};

function updatePlaceInfo(x: number, y: number): void {
  const tool = ui.activeTool;
  if (!tool || !state) return;
  if (x < 0) return ui.setPlaceInfo(null, null); // cursor left the map
  ui.setPlaceInfo(tool, placementError(map, state.buildings, tool, x, y, stockAtTile(map, state, x, y)));
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
  const msg = e.data;
  if (msg.type === 'error') return ui.toast(msg.msg);
  if (msg.type === 'save') return onSave(msg.slot, msg.data);
  state = msg.state;
  ui.setState(state, hudIsland());
  ind.update(state);
  objectives.update(state);
  for (const ev of state.concordat.log) {
    if (ev.id > seenLog && seenLog >= 0 && ev.kind === 'seized' && ev.x !== undefined && ev.y !== undefined) renderer.flash(ev.x, ev.y);
  }
  seenLog = state.concordat.seq;
  renderer.setState(state);
  renderer.setHour(hourNow());
  const sel = state.buildings.find((b) => b.id === selected);
  if (selected !== null && !sel) select(null);
  else if (sel) ui.updateInfo(sel, state);
};

function onSave(slot: 'auto' | 'manual' | 'export', data: string): void {
  if (slot === 'export') {
    try {
      downloadSave(data, `foundry-${seed}-day${state ? dayOf(state.tick) : 0}.json`);
    } catch {
      ui.toast('Export failed');
    }
  } else if (!writeSave(slot, data)) ui.toast(slot === 'auto' ? 'Autosave failed (storage unavailable)' : 'Save failed (storage unavailable)');
  else if (slot === 'manual') ui.toast('Game saved', 'info');
}

/** Start (or load) a game: the menu has chosen. */
export async function startGame(desc: StartDesc): Promise<void> {
  seed = desc.kind === 'new' ? desc.seed : (JSON.parse(desc.data) as SaveData).seed;
  map = generateMap(seed);
  ui = new Ui(uiEvents);
  ind = new IndependenceUi({
    onDeclare: () => command({ type: 'declare' }),
    onNewGame: () => {
      const difficulty = state?.difficulty ?? 'standard';
      resetClient();
      send({ type: 'init', seed, difficulty });
    },
  });
  objectives = new Objectives((ids) => ui.setHighlight(ids));
  window.addEventListener('keydown', (e) => {
    shiftHeld = e.shiftKey;
    if (e.key === 'Escape') closePanels();
  });
  window.addEventListener('keyup', (e) => (shiftHeld = e.shiftKey));
  renderer = new Renderer(map, rendererEvents);
  setInterval(() => {
    if (!state) return;
    ui.setState(state, hudIsland());
    ui.setTime(hourNow(), dayOf(state.tick));
  }, 300);
  for (const [id, set, get] of [
    ['btn-bloom', (v: boolean) => renderer.setBloom(v), () => renderer.bloomOn],
    ['btn-rain', (v: boolean) => renderer.setRain(v), () => renderer.rainEnabled],
  ] as const) {
    const btn = document.getElementById(id) as HTMLButtonElement;
    btn.classList.toggle('active', get());
    btn.addEventListener('click', () => (set(!get()), btn.classList.toggle('active', get())));
  } // camera moves between snapshots (and while paused)

  await renderer.init(document.getElementById('map') as HTMLElement);
  send(desc.kind === 'new' ? { type: 'init', seed, difficulty: desc.difficulty } : { type: 'load', data: desc.data });

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
    /** Force the time of day (hours 0-24); null returns to the sim clock. */
    setHour: (h: number | null) => {
      hourOverride = h;
      renderer.setHour(hourNow());
    },
    place: (building: string, x: number, y: number) => command({ type: 'placeBuilding', building, x, y }),
  };
}

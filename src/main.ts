import { Renderer } from './render/renderer';
import type { FromWorker, ToWorker } from './sim/protocol';
import { generateMap } from './sim/mapgen';
import { buildingAt, buildingDef, placementError } from './sim/placement';
import type { Command, GameState } from './sim/types';
import { Ui } from './ui/ui';

const seed = Number(new URLSearchParams(location.search).get('seed') ?? 1337);
const map = generateMap(seed);
let state: GameState | null = null;
let selected: number | null = null;

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
});

const renderer = new Renderer(map, {
  onTileHover: (x, y) => updatePlaceInfo(x, y),
  onTileClick: (x, y) => {
    const tool = ui.activeTool;
    if (tool) {
      const err = state ? placementError(map, state.buildings, tool, x, y, state.stock) : 'loading';
      if (err === null) command({ type: 'placeBuilding', building: tool.id, x, y });
      else if (tool.id !== 'road' || !err.includes('occupied')) ui.toast(err);
    } else select(state ? (buildingAt(state.buildings, x, y)?.id ?? null) : null);
  },
});

function updatePlaceInfo(x: number, y: number): void {
  const tool = ui.activeTool;
  if (!tool || !state) return;
  ui.setPlaceInfo(tool, x < 0 ? null : placementError(map, state.buildings, tool, x, y, state.stock));
}

function select(id: number | null): void {
  selected = id;
  renderer.setSelected(id);
  ui.showInfo(state?.buildings.find((b) => b.id === id) ?? null, state ?? undefined);
}

worker.onmessage = (e: MessageEvent<FromWorker>) => {
  state = e.data.state;
  ui.setState(state);
  renderer.setState(state);
  const sel = state.buildings.find((b) => b.id === selected);
  if (selected !== null && !sel) select(null);
  else if (sel) ui.updateInfo(sel, state);
};

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
  place: (building: string, x: number, y: number) => command({ type: 'placeBuilding', building, x, y }),
};

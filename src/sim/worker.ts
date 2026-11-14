/// <reference lib="webworker" />
import type { FromWorker, ToWorker } from './protocol';
import { Sim, TICK_HZ } from './sim';

const AUTOSAVE_TICKS = 1200; // 2 in-game minutes

const ctx = self as unknown as {
  postMessage(m: FromWorker): void;
  onmessage: ((e: MessageEvent<ToWorker>) => void) | null;
};

let sim: Sim | null = null;
let last = performance.now();
let acc = 0;
let lastAuto = 0;
const post = () => sim && ctx.postMessage({ type: 'state', state: sim.state });

ctx.onmessage = (e) => {
  const msg = e.data;
  if (msg.type === 'init' || msg.type === 'load') {
    try {
      sim = msg.type === 'init' ? new Sim(msg.seed, msg.difficulty) : Sim.fromSave(JSON.parse(msg.data));
    } catch (err) {
      ctx.postMessage({ type: 'error', msg: err instanceof Error ? err.message : 'Could not load save' });
      return;
    }
    last = performance.now();
    acc = 0;
    lastAuto = sim.state.tick;
  } else if (msg.type === 'save') {
    if (sim) ctx.postMessage({ type: 'save', slot: msg.slot, data: JSON.stringify(sim.toSave()) });
    return;
  } else if (sim) {
    sim.enqueue(msg.cmd);
    sim.flush();
  }
  post();
};

// Real-time driver: accumulate speed-scaled time, run whole 100 ms ticks.
setInterval(() => {
  const now = performance.now();
  const dt = now - last;
  last = now;
  if (!sim || sim.state.paused) return;
  acc += dt * sim.state.speed;
  const period = 1000 / TICK_HZ;
  let stepped = false;
  while (acc >= period) {
    acc -= period;
    sim.step();
    stepped = true;
  }
  if (stepped) post();
  if (sim.state.tick - lastAuto >= AUTOSAVE_TICKS && !sim.state.outcome) {
    lastAuto = sim.state.tick;
    ctx.postMessage({ type: 'save', slot: 'auto', data: JSON.stringify(sim.toSave()) });
  }
}, 25);

/// <reference lib="webworker" />
import type { FromWorker, ToWorker } from './protocol';
import { Sim, TICK_HZ } from './sim';

const ctx = self as unknown as {
  postMessage(m: FromWorker): void;
  onmessage: ((e: MessageEvent<ToWorker>) => void) | null;
};

let sim: Sim | null = null;
let last = performance.now();
let acc = 0;
const post = () => sim && ctx.postMessage({ type: 'state', state: sim.state });

ctx.onmessage = (e) => {
  const msg = e.data;
  if (msg.type === 'init') {
    sim = new Sim(msg.seed);
    last = performance.now();
    acc = 0;
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
}, 25);

// Entry point.
//   ?style=<name>        style folder at styles/<name>/ (relative to the page)
//   ?styleBase=<url>     explicit style folder URL (overrides ?style)
//   ?layout=<url>        scene layout (default: layout.json next to the page)
//   ?mode=render         fixed 1920x1080 frame, no UI; sets window.__render = 'done' | 'error: ...'
import { Application } from 'pixi.js';
import { SCREEN_H, SCREEN_W, type Layout } from './scene';
import { buildOverlays, buildWorld, fetchJson, loadStyle } from './stage';
import { startViewer } from './viewer';

declare global {
  interface Window {
    __render?: string;
  }
}

const params = new URLSearchParams(location.search);

function showError(e: unknown): void {
  const msg = e instanceof Error ? `${e.message}\n${e.stack ?? ''}` : String(e);
  console.error(msg);
  window.__render = 'error: ' + msg;
  const el = document.getElementById('err')!;
  el.textContent = msg;
  el.style.display = 'block';
}

async function renderMode(): Promise<void> {
  document.body.classList.add('render');
  const style = params.get('style') ?? 'placeholder';
  const styleBase = params.get('styleBase') ?? `styles/${style}/`;
  const [layout, loaded] = await Promise.all([
    fetchJson<Layout>(params.get('layout') ?? 'layout.json'),
    loadStyle(styleBase),
  ]);
  const app = new Application();
  await app.init({
    width: SCREEN_W,
    height: SCREEN_H,
    resolution: 1,
    antialias: false,
    autoStart: false,
    preference: 'webgl',
    preserveDrawingBuffer: true,
    background: loaded.manifest.background,
  });
  document.body.appendChild(app.canvas);
  app.stage.addChild(buildWorld(loaded, layout).container, buildOverlays(loaded).container);
  app.render();
  // Two animation frames so the compositor has presented the canvas before the screenshot.
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  window.__render = 'done';
}

(params.get('mode') === 'render' ? renderMode() : startViewer(params)).catch(showError);

// Interactive viewer: drag to pan, wheel to zoom around the cursor, style switcher,
// click a building to highlight it and show its sprite key.
import { Application, Container, Graphics, type Sprite, type Texture } from 'pixi.js';
import { SCREEN_H, SCREEN_W, tileTop, type Layout } from './scene';
import {
  buildOverlays, buildWorld, fetchJson, loadStyle, unloadStyle,
  type LoadedStyle, type OverlaySprite, type WorldSprite,
} from './stage';

interface StyleEntry {
  name: string;
  title?: string;
}

const MIN_ZOOM = 0.2;
const MAX_ZOOM = 6;
const DRAG_THRESHOLD = 4;
const HIGHLIGHT_TINT = 0xffd27a;

// ---- pixel-accurate hit testing (alpha of the source image) ----
const alphaCache = new WeakMap<Texture, Uint8ClampedArray>();
function alphaAt(tex: Texture, lx: number, ly: number): number {
  const w = tex.width;
  const h = tex.height;
  if (lx < 0 || ly < 0 || lx >= w || ly >= h) return 0;
  let data = alphaCache.get(tex);
  if (!data) {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const ctx = c.getContext('2d', { willReadFrequently: true })!;
    ctx.drawImage(tex.source.resource as CanvasImageSource, 0, 0);
    data = ctx.getImageData(0, 0, w, h).data;
    alphaCache.set(tex, data);
  }
  return data[(Math.floor(ly) * w + Math.floor(lx)) * 4 + 3];
}
function spriteHit(s: Sprite, x: number, y: number): boolean {
  return s.visible && alphaAt(s.texture, x - s.x, y - s.y) > 16;
}

export async function startViewer(params: URLSearchParams): Promise<void> {
  const layoutUrl = params.get('layout') ?? 'layout.json';
  let styles: StyleEntry[] = [];
  try {
    const idx = await fetchJson<(StyleEntry | string)[]>('styles/index.json');
    styles = idx.map((e) => (typeof e === 'string' ? { name: e } : e));
  } catch {
    /* no index: fall back to whatever ?style says */
  }
  let styleName = params.get('style') ?? styles[0]?.name ?? 'placeholder';
  if (!styles.some((s) => s.name === styleName)) styles.unshift({ name: styleName });

  const layout = await fetchJson<Layout>(layoutUrl);
  let style: LoadedStyle = await loadStyle(params.get('styleBase') ?? `styles/${styleName}/`);

  const app = new Application();
  await app.init({
    resizeTo: window,
    antialias: false,
    resolution: window.devicePixelRatio || 1,
    autoDensity: true,
    preference: 'webgl',
    background: style.manifest.background,
  });
  document.body.appendChild(app.canvas);
  const canvas = app.canvas;

  // ---- scene graph: camera(world) + screen-space UI ----
  const camera = new Container();
  const ui = new Container();
  app.stage.addChild(camera, ui);
  const highlight = new Graphics();
  let world: WorldSprite[] = [];
  let overlays: OverlaySprite[] = [];
  let worldLayer: Container | null = null;
  let uiLayer: Container | null = null;
  let selected: WorldSprite | null = null;

  function mountStyle(s: LoadedStyle): void {
    select(null);
    highlight.removeFromParent(); // reused across styles: keep it out of the destroy below
    worldLayer?.destroy({ children: true });
    uiLayer?.destroy({ children: true });
    const w = buildWorld(s, layout);
    const o = buildOverlays(s);
    world = w.sprites;
    overlays = o.sprites;
    worldLayer = w.container;
    uiLayer = o.container;
    // Footprint outline sits above terrain + flat objects, below standing objects.
    const firstStanding = world.findIndex(
      (ws) => ws.item.kind === 'object' && !s.manifest.sprites[ws.item.key].flat,
    );
    worldLayer.addChildAt(
      highlight,
      firstStanding < 0 ? worldLayer.children.length : worldLayer.getChildIndex(world[firstStanding].sprite),
    );
    camera.addChild(worldLayer);
    ui.addChild(uiLayer);
    app.renderer.background.color = s.manifest.background;
    layoutUi();
  }

  // ---- camera ----
  let zoom = 1;
  function fit(): void {
    const w = app.screen.width;
    const h = app.screen.height;
    zoom = Math.min(w / SCREEN_W, h / SCREEN_H);
    camera.scale.set(zoom);
    camera.position.set((w - SCREEN_W * zoom) / 2, (h - SCREEN_H * zoom) / 2);
    updateTip();
  }
  function zoomAt(sx: number, sy: number, factor: number): void {
    const nz = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom * factor));
    const wx = (sx - camera.x) / zoom;
    const wy = (sy - camera.y) / zoom;
    zoom = nz;
    camera.scale.set(zoom);
    camera.position.set(sx - wx * zoom, sy - wy * zoom);
    updateTip();
  }

  // UI overlays are authored for a 1920x1080 frame. Scale down on small windows and pin
  // overlays from the bottom/right half of the frame to the bottom/right window edge.
  function layoutUi(): void {
    const w = app.screen.width;
    const h = app.screen.height;
    const s = Math.min(1, w / SCREEN_W, h / SCREEN_H);
    ui.scale.set(s);
    const vw = w / s;
    const vh = h / s;
    for (const { def, sprite } of overlays) {
      const [ax, ay] = def.anchor ?? [0, 0];
      sprite.x = def.pos[0] - ax + (def.pos[0] > SCREEN_W / 2 ? vw - SCREEN_W : 0);
      sprite.y = def.pos[1] - ay + (def.pos[1] > SCREEN_H / 2 ? vh - SCREEN_H : 0);
    }
  }

  // ---- selection + tooltip ----
  const tip = document.createElement('div');
  tip.id = 'tip';
  document.body.appendChild(tip);

  function select(ws: WorldSprite | null): void {
    if (selected) selected.sprite.tint = 0xffffff;
    selected = ws;
    highlight.clear();
    if (!ws) {
      tip.style.display = 'none';
      return;
    }
    ws.sprite.tint = HIGHLIGHT_TINT;
    const { x, y, fw, fh } = ws.item;
    const pts = [tileTop(x, y), tileTop(x + fw, y), tileTop(x + fw, y + fh), tileTop(x, y + fh)].flat();
    highlight.poly(pts).fill({ color: 0xffd27a, alpha: 0.25 }).stroke({ width: 3, color: 0xffd27a });
    tip.innerHTML = `<b>${ws.item.key}</b> &nbsp;tile (${x}, ${y})${fw > 1 || fh > 1 ? ` &middot; ${fw}&times;${fh}` : ''}`;
    tip.style.display = 'block';
    updateTip();
  }
  function updateTip(): void {
    if (!selected) return;
    const s = selected.sprite;
    const sx = camera.x + (s.x + s.width / 2) * zoom;
    const sy = camera.y + s.y * zoom;
    tip.style.left = `${Math.round(sx - tip.offsetWidth / 2)}px`;
    tip.style.top = `${Math.round(Math.max(4, sy - tip.offsetHeight - 6))}px`;
  }

  function pick(sx: number, sy: number): void {
    // Clicks on UI chrome do not reach the map.
    for (let i = overlays.length - 1; i >= 0; i--) {
      const sp = overlays[i].sprite;
      if (spriteHit(sp, sx / ui.scale.x, sy / ui.scale.y)) return;
    }
    const wx = (sx - camera.x) / zoom;
    const wy = (sy - camera.y) / zoom;
    for (let i = world.length - 1; i >= 0; i--) {
      const ws = world[i];
      if (ws.item.kind !== 'terrain' && spriteHit(ws.sprite, wx, wy)) {
        select(ws === selected ? null : ws);
        return;
      }
    }
    select(null);
  }

  // ---- input ----
  let drag: { id: number; x: number; y: number; moved: boolean } | null = null;
  const local = (e: PointerEvent | WheelEvent): [number, number] => {
    const r = canvas.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  };
  canvas.addEventListener('pointerdown', (e) => {
    canvas.setPointerCapture(e.pointerId);
    const [x, y] = local(e);
    drag = { id: e.pointerId, x, y, moved: false };
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!drag || drag.id !== e.pointerId) return;
    const [x, y] = local(e);
    const dx = x - drag.x;
    const dy = y - drag.y;
    if (!drag.moved && Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
    drag.moved = true;
    canvas.style.cursor = 'grabbing';
    camera.x += dx;
    camera.y += dy;
    drag.x = x;
    drag.y = y;
    updateTip();
  });
  const endDrag = (e: PointerEvent) => {
    if (!drag || drag.id !== e.pointerId) return;
    if (!drag.moved && e.type === 'pointerup') pick(...local(e));
    drag = null;
    canvas.style.cursor = '';
  };
  canvas.addEventListener('pointerup', endDrag);
  canvas.addEventListener('pointercancel', endDrag);
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const dy = e.deltaMode === 1 ? e.deltaY * 40 : e.deltaY;
    zoomAt(...local(e), Math.exp(-dy * 0.0015));
  }, { passive: false });
  window.addEventListener('keydown', (e) => {
    if (e.target instanceof HTMLSelectElement) return;
    if (e.key === 'r' || e.key === '0') fit();
    if (e.key === 'u') ui.visible = !ui.visible;
    if (e.key === 'Escape') select(null);
  });
  app.renderer.on('resize', () => {
    layoutUi();
    updateTip();
  });

  // ---- HUD: style switcher ----
  const hud = document.createElement('div');
  hud.id = 'hud';
  hud.innerHTML = `<label>Art style<select></select></label>
    <div class="hint">drag: pan &middot; wheel: zoom &middot; click: inspect<br>R: reset view &middot; U: toggle UI</div>`;
  document.body.appendChild(hud);
  const sel = hud.querySelector('select')!;
  for (const s of styles) sel.add(new Option(s.title ?? s.name, s.name, false, s.name === styleName));
  let switchToken = 0;
  sel.addEventListener('change', async () => {
    const name = sel.value;
    const token = ++switchToken;
    sel.disabled = true;
    try {
      const next = await loadStyle(`styles/${name}/`);
      if (token !== switchToken) return; // superseded (textures may be shared; leave cached)
      const prev = style;
      style = next;
      styleName = name;
      mountStyle(next);
      if (prev.base !== next.base) await unloadStyle(prev);
      const u = new URL(location.href);
      u.searchParams.set('style', name);
      u.searchParams.delete('styleBase');
      history.replaceState(null, '', u);
    } catch (err) {
      console.error(err);
      alert(`Could not load style "${name}": ${err}`);
      sel.value = styleName;
    } finally {
      if (token === switchToken) sel.disabled = false;
    }
  });

  mountStyle(style);
  fit();
}

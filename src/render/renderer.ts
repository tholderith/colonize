import { AnimatedSprite, type Texture, Application, BlurFilter, ColorMatrixFilter, Container, CullerPlugin, Graphics, Rectangle, Sprite, TilingSprite, extensions } from 'pixi.js';
import look from '../data/look.json';
import { buildingDef, placementError, stockAtTile } from '../sim/placement';
import type { Building, BuildingDef, GameMap, GameState, TileClass } from '../sim/types';
import { TILE_CLASSES } from '../sim/types';
import { loadArt, type Art, type Sprite2 } from './assets';
import { Camera } from './camera';
import { Smoke, WaterFilter, beacon, flicker, gradeAt, rainTexture, vignetteTexture } from './fx';
import { TILE_H, TILE_W, gridToWorld, worldToTile } from './iso';

// Off-screen culling for containers flagged `cullable` (terrain chunks, buildings, roads, ships).
extensions.add(CullerPlugin);
const CHUNK = 8;
const RAIN_SPEED = [900, 1500];

const TERRAIN_COLOR: Record<TileClass, number> = {
  deep: 0x0b1d33,
  shallow: 0x14506b,
  shore: 0xc2a46b,
  land: 0x3d6b4a,
};

function hex(c: string): number {
  return parseInt(c.slice(1), 16);
}
function shade(c: number, f: number): number {
  const r = Math.min(255, ((c >> 16) & 255) * f);
  const g = Math.min(255, ((c >> 8) & 255) * f);
  const b = Math.min(255, (c & 255) * f);
  return (r << 16) | (g << 8) | b;
}

/** Isometric box over footprint (x, y, w, h) in tiles. */
function drawBox(g: Graphics, x: number, y: number, w: number, h: number, height: number, color: number, alpha = 1): void {
  const i = 0.12; // inset in tiles
  const T = gridToWorld(x + i, y + i);
  const R = gridToWorld(x + w - i, y + i);
  const B = gridToWorld(x + w - i, y + h - i);
  const L = gridToWorld(x + i, y + h - i);
  const up = (p: { x: number; y: number }) => ({ x: p.x, y: p.y - height });
  g.poly([L.x, L.y, B.x, B.y, up(B).x, up(B).y, up(L).x, up(L).y]).fill({ color: shade(color, 0.7), alpha });
  g.poly([B.x, B.y, R.x, R.y, up(R).x, up(R).y, up(B).x, up(B).y]).fill({ color: shade(color, 0.5), alpha });
  g.poly([up(T).x, up(T).y, up(R).x, up(R).y, up(B).x, up(B).y, up(L).x, up(L).y]).fill({ color: shade(color, 1.1), alpha });
}

interface Ship {
  node: Container;
  kind: 'hauler' | 'trader' | 'patrol';
  dir: string;
  ring?: Graphics;
  glow?: GlowPair;
  fx: number; fy: number; tx: number; ty: number;
  cx?: number; cy?: number;
  t0: number; dur: number;
}

/** A glow sprite drawn twice: sharp (additive) and into the blurred bloom layer. */
interface GlowPair {
  sharp: Container;
  bloom: Container;
}
interface Built {
  node: Container;
  key: string;
  glow?: GlowPair;
  beacon?: boolean;
}

export interface RendererEvents {
  /** Click (not drag) on a tile. */
  onTileClick(x: number, y: number): void;
  onTileHover(x: number, y: number): void;
}

export class Renderer {
  readonly app = new Application();
  /** Camera-transformed world; waterWorld/glowWorld/bloomWorld mirror its transform. */
  private world = new Container();
  private sceneRoot = new Container();
  private waterRoot = new Container();
  private waterWorld = new Container();
  private water = new Container();
  private glowWorld = new Container();
  private glowLayer = new Container();
  private bloomRoot = new Container();
  private bloomWorld = new Container();
  private bloomLayer = new Container();
  private smokeLayer = new Container();
  private smoke = new Smoke(this.smokeLayer);
  private grade = new ColorMatrixFilter();
  private waterFilter = new WaterFilter();
  private blur = new BlurFilter({ strength: look.bloom.strength, quality: 3, resolution: 0.5 });
  private screenRect = new Rectangle();
  private rain: TilingSprite[] = [];
  private rainOn = false;
  private vignette = new Sprite();
  private hour = 19;
  private glowK = 1;
  private nightK = 1;
  private terrain = new Container();
  private objects = new Container();
  private ghost = new Container();
  private camera!: Camera;
  private art: Art = { tiles: new Map(), buildings: new Map(), units: new Map(), anims: new Map() };
  private ships = new Map<number, Ship>();
  /** Containers that mirror the camera transform (set once the layers exist). */
  private mirrors: Container[] = [this.waterWorld, this.glowWorld, this.bloomWorld];
  private selectedShip: number | null = null;
  private flashes: { g: Graphics; x: number; y: number; t0: number }[] = [];
  private lastSnap = 0;
  private snapMs = 100;
  private roads = new Container();
  private built = new Map<number, Built>();
  private painting = false;
  private lastPaint = { x: -1, y: -1 };
  private hover = { x: -1, y: -1 };
  private ghostDef: BuildingDef | null = null;
  private state: GameState | null = null;
  private selectedId: number | null = null;
  private selection = new Graphics();

  constructor(
    private map: GameMap,
    private events: RendererEvents,
  ) {}

  async init(host: HTMLElement): Promise<void> {
    await this.app.init({ resizeTo: host, background: 0x050a14, antialias: true });
    host.appendChild(this.app.canvas);
    this.art = await loadArt();
    this.objects.sortableChildren = true;
    this.ghost.zIndex = 1e6;
    this.selection.zIndex = 1e6 - 1;
    this.drawTerrain();
    this.world.addChild(this.terrain, this.roads, this.objects, this.smokeLayer);
    this.objects.addChild(this.selection, this.ghost);
    this.waterWorld.addChild(this.water);
    this.waterRoot.addChild(this.waterWorld);
    this.waterRoot.filters = [this.waterFilter];
    this.sceneRoot.addChild(this.waterRoot, this.world);
    this.sceneRoot.filters = [this.grade];
    this.glowWorld.addChild(this.glowLayer);
    this.bloomLayer.alpha = look.bloom.alpha;
    this.bloomWorld.addChild(this.bloomLayer);
    this.bloomRoot.addChild(this.bloomWorld);
    this.bloomRoot.filters = [this.blur];
    this.bloomRoot.blendMode = 'add';
    for (const r of [this.sceneRoot, this.waterRoot, this.bloomRoot]) r.filterArea = this.screenRect;
    this.vignette.texture = vignetteTexture();
    for (const [i, [seed, n, scale]] of ([[11, 70, 1], [23, 45, 1.7]] as const).entries()) {
      const t = new TilingSprite({ texture: rainTexture(seed, n), width: 1, height: 1 });
      t.tileScale.set(scale);
      t.blendMode = 'add';
      t.label = String(i);
      this.rain.push(t);
    }
    this.app.stage.addChild(this.sceneRoot, this.glowWorld, this.bloomRoot, this.vignette, ...this.rain);
    this.layoutOverlay();
    this.app.renderer.on('resize', () => this.layoutOverlay());
    this.setHour(this.hour);

    this.camera = new Camera(this.world, this.app.canvas);
    const b = this.landBounds();
    const hud = document.getElementById('hud')?.getBoundingClientRect();
    this.camera.fit(b, this.app.screen.width, this.app.screen.height, hud ? hud.bottom + 8 : 0);
    this.app.ticker.add((t) => {
      this.camera.update(t.deltaMS);
      this.moveShips();
      this.animate(t.deltaMS / 1000);
    });

    const canvas = this.app.canvas;
    const tileAtEvent = (e: PointerEvent) => {
      const r = canvas.getBoundingClientRect();
      return this.screenToTile(e.clientX - r.left, e.clientY - r.top);
    };
    canvas.addEventListener('pointerdown', (e) => {
      if (e.button !== 0 || this.ghostDef?.id !== 'road') return;
      const t = tileAtEvent(e);
      this.painting = true;
      this.lastPaint = t;
      this.events.onTileClick(t.x, t.y);
    });
    window.addEventListener('pointerup', () => (this.painting = false));
    canvas.addEventListener('pointermove', (e) => {
      const t = tileAtEvent(e);
      this.hover = t;
      this.events.onTileHover(t.x, t.y);
      if (this.painting && (t.x !== this.lastPaint.x || t.y !== this.lastPaint.y)) {
        // Walk the straight line from the last painted tile so fast drags leave no gaps.
        const n = Math.max(Math.abs(t.x - this.lastPaint.x), Math.abs(t.y - this.lastPaint.y));
        for (let i = 1; i <= n; i++)
          this.events.onTileClick(
            Math.round(this.lastPaint.x + ((t.x - this.lastPaint.x) * i) / n),
            Math.round(this.lastPaint.y + ((t.y - this.lastPaint.y) * i) / n),
          );
        this.lastPaint = t;
      }
      this.redrawGhost();
    });
    canvas.addEventListener('pointerup', (e) => {
      if (e.button !== 0 || this.camera.dragged || this.ghostDef?.id === 'road') return;
      const t = tileAtEvent(e);
      this.events.onTileClick(t.x, t.y);
    });
  }

  /** World-space box around all non-deep tiles. */
  private landBounds(): { x: number; y: number; w: number; h: number } {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    const { w, h, tiles } = this.map;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        if (tiles[y * w + x] === 0) continue;
        const p = gridToWorld(x, y);
        x0 = Math.min(x0, p.x - TILE_W / 2);
        x1 = Math.max(x1, p.x + TILE_W / 2);
        y0 = Math.min(y0, p.y - 190); // headroom for the HUD
        y1 = Math.max(y1, p.y + TILE_H);
      }
    }
    return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  }

  private drawTerrain(): void {
    const g = new Graphics();
    const wg = new Graphics();
    const chunks = new Map<number, Container>();
    const { w, h, tiles } = this.map;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const cls = TILE_CLASSES[tiles[y * w + x] as number] as TileClass;
        const p = gridToWorld(x, y);
        const key = this.tileKey(x, y, cls);
        const art = this.art.tiles.get(key) ?? (key.startsWith('land_') ? this.art.tiles.get('land') : undefined);
        if (art) {
          // Anchor sits on the tile's south corner.
          const s = gridToWorld(x + 1, y + 1);
          if (cls === 'deep' || cls === 'shallow') this.water.addChild(this.makeSprite(art, s.x, s.y));
          else {
            const ck = Math.floor(x / CHUNK) + Math.floor(y / CHUNK) * 1000;
            let chunk = chunks.get(ck);
            if (!chunk) {
              chunk = new Container();
              chunk.cullable = true;
              chunks.set(ck, chunk);
              this.terrain.addChild(chunk);
            }
            chunk.addChild(this.makeSprite(art, s.x, s.y));
          }
          continue;
        }
        // Slight per-tile checker variation so the grid reads.
        const c = shade(TERRAIN_COLOR[cls], (x + y) % 2 ? 1 : 0.94);
        (cls === 'deep' || cls === 'shallow' ? wg : g).poly([p.x, p.y, p.x + TILE_W / 2, p.y + TILE_H / 2, p.x, p.y + TILE_H, p.x - TILE_W / 2, p.y + TILE_H / 2]).fill(c);
      }
    }
    this.terrain.addChildAt(g, 0);
    this.water.addChildAt(wg, 0);
  }

  private isWater(x: number, y: number): boolean {
    const { w, h, tiles } = this.map;
    if (x < 0 || y < 0 || x >= w || y >= h) return false;
    const c = tiles[y * w + x];
    return c === 0 || c === 1;
  }

  /** Art key for a tile: water as-is, land variants inland, else a seawall autotile (N=1 E=2 S=4 W=8). */
  private tileKey(x: number, y: number, cls: TileClass): string {
    if (cls === 'deep' || cls === 'shallow') {
      const base = cls === 'deep' ? 'deep_water' : 'shallow_water';
      const v = `${base}_${(x * 7 + y * 13) % 3}`;
      return this.art.tiles.has(v) ? v : base;
    }
    const mask =
      (this.isWater(x, y - 1) ? 1 : 0) | (this.isWater(x + 1, y) ? 2 : 0) | (this.isWater(x, y + 1) ? 4 : 0) | (this.isWater(x - 1, y) ? 8 : 0);
    return mask === 0 ? `land_${(x * 7 + y * 13) % 3}` : `shore_${mask}`;
  }

  private makeSprite(s: Sprite2, x: number, y: number, additive = false): Sprite {
    const sp = new Sprite(s.tex);
    sp.pivot.set(s.anchor[0], s.anchor[1]); // anchors are pixels (not normalised)
    sp.position.set(x, y);
    if (additive) sp.blendMode = 'add';
    return sp;
  }

  screenToTile(sx: number, sy: number): { x: number; y: number } {
    return worldToTile((sx - this.world.x) / this.world.scale.x, (sy - this.world.y) / this.world.scale.y);
  }

  /** Screen (canvas-relative) centre of a tile; used by tests and tooling. */
  tileToScreen(x: number, y: number): { x: number; y: number } {
    const p = gridToWorld(x + 0.5, y + 0.5);
    return { x: p.x * this.world.scale.x + this.world.x, y: p.y * this.world.scale.y + this.world.y };
  }

  setGhost(def: BuildingDef | null): void {
    this.ghostDef = def;
    this.camera.panDisabled = def?.id === 'road';
    this.redrawGhost();
  }

  setSelected(id: number | null): void {
    this.selectedId = id;
    this.redrawSelection();
  }

  setState(state: GameState): void {
    const now = performance.now();
    if (this.lastSnap) this.snapMs = Math.min(400, Math.max(30, now - this.lastSnap));
    this.lastSnap = now;
    this.state = state;
    this.syncShips(state);
    const live = new Set<number>();
    const isRoad = new Set<number>();
    for (const b of state.buildings) if (b.type === 'road') isRoad.add(b.x + b.y * this.map.w);
    for (const b of state.buildings) {
      live.add(b.id);
      const key = this.artKey(b, isRoad);
      const cur = this.built.get(b.id);
      if (cur && cur.key === key) continue;
      if (cur) this.destroyBuilt(b.id, cur);
      this.addBuilding(b, key);
    }
    for (const [id, o] of this.built) if (!live.has(id)) this.destroyBuilt(id, o);
    for (const b of state.buildings) if (this.smoke.has(b.type)) this.smokeFor(b);
    this.redrawSelection();
    this.redrawGhost();
  }

  /** Drop every building and ship node (a different game was loaded into the same map). */
  reset(): void {
    for (const [id, o] of this.built) this.destroyBuilt(id, o);
    for (const sh of this.ships.values()) {
      sh.node.destroy({ children: true });
      sh.glow?.sharp.destroy({ children: true });
      sh.glow?.bloom.destroy({ children: true });
    }
    this.ships.clear();
    this.selectedId = null;
    this.selectedShip = null;
  }

  private destroyBuilt(id: number, o: Built): void {
    o.node.destroy({ children: true });
    o.glow?.sharp.destroy({ children: true });
    o.glow?.bloom.destroy({ children: true });
    this.smoke.remove(id);
    this.built.delete(id);
  }

  private smokeFor(b: Building): void {
    const def = buildingDef(b.type);
    const art = this.art.buildings.get(b.type);
    if (!def || !art) return;
    const c = gridToWorld(b.x + def.footprint[0], b.y + def.footprint[1]);
    this.smoke.set(b.id, b.type, c.x, c.y, b.status === 'working');
  }

  /** Both halves of a glow: sharp additive in glowLayer, a copy in the blurred bloom layer. */
  private makeGlow(s: Sprite2, x: number, y: number, custom?: () => Sprite): GlowPair {
    const mk = (layer: Container) => {
      const c = new Container();
      c.addChild(custom ? custom() : this.makeSprite(s, x, y, true));
      layer.addChild(c);
      return c;
    };
    return { sharp: mk(this.glowLayer), bloom: mk(this.bloomLayer) };
  }

  /** Time of day (hour 0-24): colour grade, glow strength, rain and sheen follow. */
  setHour(hour: number): void {
    this.hour = hour;
    const g = gradeAt(hour);
    const [r, gg, b] = g.rgb;
    this.grade.matrix = [r, 0, 0, 0, 0, 0, gg, 0, 0, 0, 0, 0, b, 0, 0, 0, 0, 0, 1, 0];
    this.glowK = g.glow;
    this.nightK = Math.min(1, Math.max(0, (g.glow - 0.2) / 0.8));
    this.vignette.alpha = 0.25 + 0.55 * this.nightK;
    this.updateRain();
  }

  setBloom(on: boolean): void {
    this.bloomRoot.visible = on;
  }
  setRain(on: boolean): void {
    this.rainOn = on;
    this.updateRain();
  }
  get bloomOn(): boolean {
    return this.bloomRoot.visible;
  }
  get rainEnabled(): boolean {
    return this.rainOn;
  }

  private updateRain(): void {
    for (const [i, r] of this.rain.entries()) {
      r.visible = this.rainOn && this.nightK > 0.05;
      r.alpha = look.rain.maxAlpha * this.nightK * (i ? 0.6 : 1);
    }
  }

  private layoutOverlay(): void {
    const { width, height } = this.app.screen;
    this.screenRect.width = width;
    this.screenRect.height = height;
    this.vignette.width = width;
    this.vignette.height = height;
    for (const r of this.rain) {
      r.width = width;
      r.height = height;
    }
  }

  /** Per frame: mirror the camera, drive water, glow flicker/beacons, rain, smoke. */
  private animate(dt: number): void {
    const t = performance.now() / 1000;
    const { x, y } = this.world;
    const z = this.world.scale.x;
    for (const c of this.mirrors) {
      c.position.set(x, y);
      c.scale.set(z);
    }
    this.waterFilter.set(t, x, y, z, 0.15 + 0.25 * this.nightK, this.nightK);
    this.blur.strength = Math.max(3, look.bloom.strength * Math.min(1.4, z + 0.3));
    for (const [id, o] of this.built) {
      if (!o.glow) continue;
      const k = this.glowK * flicker(id, t) * (o.beacon ? beacon(id, t) : 1);
      o.glow.sharp.alpha = o.glow.bloom.alpha = k;
    }
    for (const sh of this.ships.values()) if (sh.glow) sh.glow.sharp.alpha = sh.glow.bloom.alpha = this.glowK;
    this.smoke.update(Math.min(dt, 0.1), this.nightK);
    this.updateFlashes();
    for (let i = 0; i < this.rain.length; i++) {
      const r = this.rain[i]!;
      r.tilePosition.x -= RAIN_SPEED[i]! * 0.22 * dt;
      r.tilePosition.y += RAIN_SPEED[i]! * dt;
    }
  }

  /** Red expanding ring at a map position (a seized cargo). */
  flash(x: number, y: number): void {
    const g = new Graphics();
    g.zIndex = 1e5;
    this.objects.addChild(g);
    this.flashes.push({ g, x, y, t0: performance.now() });
  }

  private updateFlashes(): void {
    if (!this.flashes.length) return;
    const now = performance.now();
    this.flashes = this.flashes.filter((f) => {
      const a = (now - f.t0) / 1400;
      if (a >= 1) {
        f.g.destroy();
        return false;
      }
      const pts: number[] = [];
      const r = 0.6 + a * 2.6;
      for (let i = 0; i < 32; i++) {
        const p = gridToWorld(f.x + Math.cos((i / 32) * Math.PI * 2) * r, f.y + Math.sin((i / 32) * Math.PI * 2) * r);
        pts.push(p.x, p.y);
      }
      f.g.clear().poly(pts).stroke({ color: 0xff4d4d, width: 5 * (1 - a) + 1, alpha: 1 - a });
      return true;
    });
  }

  /** Grid tile at the centre of the screen. */
  centreTile(): { x: number; y: number } {
    return this.screenToTile(this.app.screen.width / 2, this.app.screen.height / 2);
  }

  setSelectedShip(id: number | null): void {
    this.selectedShip = id;
  }

  /** Create/remove ship nodes and retarget each tween from where it is drawn now to its new tick position. */
  private syncShips(state: GameState): void {
    const live = new Set<number>();
    for (const m of [...state.haulers, ...state.visitors, ...state.patrols]) {
      live.add(m.id);
      let sh = this.ships.get(m.id);
      if (!sh) {
        sh = { node: new Container(), kind: m.kind, dir: 'se', fx: m.x, fy: m.y, tx: m.x, ty: m.y, t0: performance.now(), dur: this.snapMs };
        sh.node.cullable = true;
        this.objects.addChild(sh.node);
        this.ships.set(m.id, sh);
        this.setShipDir(sh, 'se');
      }
      sh.fx = sh.cx ?? m.x;
      sh.fy = sh.cy ?? m.y;
      sh.tx = m.x;
      sh.ty = m.y;
      sh.t0 = performance.now();
      sh.dur = this.snapMs;
    }
    for (const [id, sh] of this.ships) {
      if (!live.has(id)) {
        sh.node.destroy({ children: true });
        sh.glow?.sharp.destroy({ children: true });
        sh.glow?.bloom.destroy({ children: true });
        this.ships.delete(id);
      }
    }
  }

  private setShipDir(sh: Ship, dir: string): void {
    for (const c of sh.node.removeChildren()) c.destroy({ children: true });
    sh.glow?.sharp.destroy({ children: true });
    sh.glow?.bloom.destroy({ children: true });
    sh.glow = undefined;
    sh.dir = dir;
    const art = this.art.units.get(`${sh.kind}_${dir}`);
    if (art) {
      sh.node.addChild(this.makeSprite(art.base, 0, 0));
      if (art.glow) sh.glow = this.makeGlow(art.glow, 0, 0);
    } else {
      const g = new Graphics();
      const color = sh.kind === 'hauler' ? 0xfbbf24 : sh.kind === 'trader' ? 0x4ade80 : 0xf87171;
      drawBox(g, -0.4, -0.4, 0.8, 0.8, sh.kind === 'hauler' ? 22 : 16, color);
      sh.node.addChild(g);
    }
    sh.ring = new Graphics();
    sh.ring.poly([0, -22, 40, 0, 0, 22, -40, 0]).stroke({ color: 0x22d3ee, width: 3 });
    sh.ring.visible = false;
    sh.node.addChild(sh.ring);
  }

  /** Per frame: ease each ship along its last-tick movement; face the direction of travel. */
  private moveShips(): void {
    const now = performance.now();
    for (const sh of this.ships.values()) {
      const a = this.state?.paused ? 1 : Math.min(1, (now - sh.t0) / sh.dur);
      const x = sh.fx + (sh.tx - sh.fx) * a;
      const y = sh.fy + (sh.ty - sh.fy) * a;
      sh.cx = x;
      sh.cy = y;
      const dx = sh.tx - sh.fx, dy = sh.ty - sh.fy;
      if (Math.hypot(dx, dy) > 1e-4) {
        const sx = dx - dy, sy = dx + dy; // screen-space direction
        const dir = sx > 0 ? (sy < 0 ? 'ne' : 'se') : sy > 0 ? 'sw' : 'nw';
        if (dir !== sh.dir) this.setShipDir(sh, dir);
      }
      const p = gridToWorld(x, y);
      sh.node.position.set(p.x, p.y);
      if (sh.glow) {
        sh.glow.sharp.position.set(p.x, p.y);
        sh.glow.bloom.position.set(p.x, p.y);
      }
      sh.node.zIndex = x + y - 0.75;
    }
    for (const [id, sh] of this.ships) if (sh.ring) sh.ring.visible = id === this.selectedShip;
  }

  /** Hauler near tile (x, y), if any. */
  haulerAt(x: number, y: number): number | null {
    let best: number | null = null;
    let bd = 1.4;
    for (const h of this.state?.haulers ?? []) {
      const sh = this.ships.get(h.id);
      const d = Math.hypot((sh?.cx ?? h.x) - (x + 0.5), (sh?.cy ?? h.y) - (y + 0.5));
      if (d < bd) { bd = d; best = h.id; }
    }
    return best;
  }

  /** Screen position (canvas-relative) of a ship; used by tests. */
  shipToScreen(id: number): { x: number; y: number } | null {
    const sh = this.ships.get(id);
    if (!sh) return null;
    return { x: sh.node.x * this.world.scale.x + this.world.x, y: sh.node.y * this.world.scale.y + this.world.y };
  }

  /** Sprite key: roads by neighbour mask, upgraded houses by tier. */
  private artKey(b: Building, isRoad: Set<number>): string {
    if (b.type === 'road') {
      const r = (x: number, y: number) => (isRoad.has(x + y * this.map.w) ? 1 : 0);
      return `road_${r(b.x, b.y - 1) | (r(b.x + 1, b.y) << 1) | (r(b.x, b.y + 1) << 2) | (r(b.x - 1, b.y) << 3)}`;
    }
    return b.type === 'pod_house' && b.tier >= 2 ? 'pod_house_t2' : b.type;
  }

  private addBuilding(b: Building, key: string): void {
    const def = buildingDef(b.type);
    if (!def) return;
    const [fw, fh] = def.footprint;
    const node = new Container();
    let glow: GlowPair | undefined;
    if (b.type === 'road') {
      const art = this.art.tiles.get(key) ?? this.art.tiles.get('road');
      if (art) {
        const c = gridToWorld(b.x + 1, b.y + 1);
        node.addChild(this.makeSprite(art, c.x, c.y));
      } else {
        const g = new Graphics();
        const T = gridToWorld(b.x + 0.1, b.y + 0.1), R = gridToWorld(b.x + 0.9, b.y + 0.1), B = gridToWorld(b.x + 0.9, b.y + 0.9), L = gridToWorld(b.x + 0.1, b.y + 0.9);
        g.poly([T.x, T.y, R.x, R.y, B.x, B.y, L.x, L.y]).fill(0x4a5568);
        node.addChild(g);
      }
      node.cullable = true;
      this.roads.addChild(node);
      this.built.set(b.id, { node, key });
      return;
    }
    const art = this.art.buildings.get(key) ?? this.art.buildings.get(def.id);
    if (art) {
      const c = gridToWorld(b.x + fw, b.y + fh); // south corner of footprint
      const anim = this.art.anims.get(key);
      if (anim) {
        const start = b.id % anim.frames.length;
        const play = (frames: Texture[]) => {
          const as = new AnimatedSprite(frames);
          as.pivot.set(anim.anchor[0], anim.anchor[1]);
          as.animationSpeed = anim.fps / 60;
          as.gotoAndPlay(start);
          return as;
        };
        node.addChild(Object.assign(play(anim.frames), { x: c.x, y: c.y }));
        if (anim.glowFrames.length) {
          glow = this.makeGlow(art.glow ?? art.base, c.x, c.y, () => Object.assign(play(anim.glowFrames), { blendMode: 'add' as const, x: c.x, y: c.y }));
        } else if (art.glow) glow = this.makeGlow(art.glow, c.x, c.y);
      } else {
        node.addChild(this.makeSprite(art.base, c.x, c.y));
        if (art.glow) glow = this.makeGlow(art.glow, c.x, c.y);
      }
    } else {
      const g = new Graphics();
      drawBox(g, b.x, b.y, fw, fh, def.height, hex(def.color));
      node.addChild(g);
    }
    node.zIndex = b.x + fw - 1 + (b.y + fh - 1);
    node.cullable = true;
    this.objects.addChild(node);
    this.built.set(b.id, { node, key, glow, beacon: b.type === 'wind_turbine' || b.type === 'port' });
  }

  private footprintOutline(g: Graphics, x: number, y: number, w: number, h: number, color: number): void {
    const T = gridToWorld(x, y);
    const R = gridToWorld(x + w, y);
    const B = gridToWorld(x + w, y + h);
    const L = gridToWorld(x, y + h);
    g.poly([T.x, T.y, R.x, R.y, B.x, B.y, L.x, L.y]).stroke({ color, width: 3 });
  }

  private redrawSelection(): void {
    this.selection.clear();
    const b = this.state?.buildings.find((o) => o.id === this.selectedId);
    const def = b && buildingDef(b.type);
    if (b && def) {
      this.footprintOutline(this.selection, b.x, b.y, def.footprint[0], def.footprint[1], 0x22d3ee);
      if (def.radius) this.radiusRing(this.selection, b.x, b.y, def.footprint[0], def.footprint[1], def.radius, def.upkeep ? 0xf87171 : 0x22d3ee);
    }
  }

  /** Coverage circle (iso ellipse) around a footprint's centre. */
  private radiusRing(g: Graphics, x: number, y: number, w: number, h: number, radius: number, color = 0x22d3ee): void {
    const pts: number[] = [];
    for (let i = 0; i < 48; i++) {
      const a = (i / 48) * Math.PI * 2;
      const p = gridToWorld(x + w / 2 + Math.cos(a) * radius, y + h / 2 + Math.sin(a) * radius);
      pts.push(p.x, p.y);
    }
    g.poly(pts).fill({ color, alpha: 0.08 }).stroke({ color, width: 2, alpha: 0.7 });
  }

  private redrawGhost(): void {
    const g = this.ghost;
    for (const c of g.removeChildren()) c.destroy({ children: true });
    const def = this.ghostDef;
    if (!def || !this.state || this.hover.x < 0) return;
    const { x, y } = this.hover;
    const ok = placementError(this.map, this.state.buildings, def, x, y, stockAtTile(this.map, this.state, x, y)) === null;
    const color = ok ? 0x4ade80 : 0xf87171;
    const [w, h] = def.footprint;
    const gfx = new Graphics();
    const T = gridToWorld(x, y), R = gridToWorld(x + w, y), B = gridToWorld(x + w, y + h), L = gridToWorld(x, y + h);
    gfx.poly([T.x, T.y, R.x, R.y, B.x, B.y, L.x, L.y]).fill({ color, alpha: 0.35 });
    const art = this.art.buildings.get(def.id);
    if (art) {
      const sp = this.makeSprite(art.base, B.x, B.y);
      sp.tint = color;
      sp.alpha = 0.5;
      g.addChild(gfx, sp);
    } else {
      drawBox(gfx, x, y, w, h, def.height, color, 0.45);
      g.addChild(gfx);
    }
    this.footprintOutline(gfx, x, y, w, h, color);
    if (def.radius) this.radiusRing(gfx, x, y, w, h, def.radius, def.upkeep ? 0xf87171 : 0x22d3ee);
  }
}

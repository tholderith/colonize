import { Application, Container, Graphics, Sprite } from 'pixi.js';
import { buildingDef, placementError } from '../sim/placement';
import type { Building, BuildingDef, GameMap, GameState, TileClass } from '../sim/types';
import { TILE_CLASSES } from '../sim/types';
import { loadArt, type Art, type Sprite2 } from './assets';
import { Camera } from './camera';
import { TILE_H, TILE_W, gridToWorld, worldToTile } from './iso';

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

export interface RendererEvents {
  /** Click (not drag) on a tile. */
  onTileClick(x: number, y: number): void;
  onTileHover(x: number, y: number): void;
}

export class Renderer {
  readonly app = new Application();
  private world = new Container();
  private terrain = new Container();
  private objects = new Container();
  private ghost = new Container();
  private camera!: Camera;
  private art: Art = { tiles: new Map(), buildings: new Map() };
  private roads = new Container();
  private built = new Map<number, { node: Container; key: string }>();
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
    this.world.addChild(this.terrain, this.roads, this.objects);
    this.objects.addChild(this.selection, this.ghost);
    this.app.stage.addChild(this.world);

    this.camera = new Camera(this.world, this.app.canvas);
    const b = this.landBounds();
    this.camera.fit(b, this.app.screen.width, this.app.screen.height);
    this.app.ticker.add((t) => this.camera.update(t.deltaMS));

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
        y0 = Math.min(y0, p.y - 80);
        y1 = Math.max(y1, p.y + TILE_H);
      }
    }
    return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  }

  private drawTerrain(): void {
    const g = new Graphics();
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
          this.terrain.addChild(this.makeSprite(art, s.x, s.y));
          continue;
        }
        // Slight per-tile checker variation so the grid reads.
        const c = shade(TERRAIN_COLOR[cls], (x + y) % 2 ? 1 : 0.94);
        g.poly([p.x, p.y, p.x + TILE_W / 2, p.y + TILE_H / 2, p.x, p.y + TILE_H, p.x - TILE_W / 2, p.y + TILE_H / 2]).fill(c);
      }
    }
    this.terrain.addChildAt(g, 0);
  }

  private isWater(x: number, y: number): boolean {
    const { w, h, tiles } = this.map;
    if (x < 0 || y < 0 || x >= w || y >= h) return false;
    const c = tiles[y * w + x];
    return c === 0 || c === 1;
  }

  /** Art key for a tile: water as-is, land variants inland, else a seawall autotile (N=1 E=2 S=4 W=8). */
  private tileKey(x: number, y: number, cls: TileClass): string {
    if (cls === 'deep') return 'deep_water';
    if (cls === 'shallow') return 'shallow_water';
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
    this.state = state;
    const live = new Set<number>();
    const isRoad = new Set<number>();
    for (const b of state.buildings) if (b.type === 'road') isRoad.add(b.x + b.y * this.map.w);
    for (const b of state.buildings) {
      live.add(b.id);
      const key = this.artKey(b, isRoad);
      const cur = this.built.get(b.id);
      if (cur && cur.key === key) continue;
      cur?.node.destroy({ children: true });
      this.addBuilding(b, key);
    }
    for (const [id, o] of this.built) {
      if (!live.has(id)) {
        o.node.destroy({ children: true });
        this.built.delete(id);
      }
    }
    this.redrawSelection();
    this.redrawGhost();
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
      this.roads.addChild(node);
      this.built.set(b.id, { node, key });
      return;
    }
    const art = this.art.buildings.get(key) ?? this.art.buildings.get(def.id);
    if (art) {
      const c = gridToWorld(b.x + fw, b.y + fh); // south corner of footprint
      node.addChild(this.makeSprite(art.base, c.x, c.y));
      if (art.glow) node.addChild(this.makeSprite(art.glow, c.x, c.y, true));
    } else {
      const g = new Graphics();
      drawBox(g, b.x, b.y, fw, fh, def.height, hex(def.color));
      node.addChild(g);
    }
    node.zIndex = b.x + fw - 1 + (b.y + fh - 1);
    this.objects.addChild(node);
    this.built.set(b.id, { node, key });
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
    if (b && def) this.footprintOutline(this.selection, b.x, b.y, def.footprint[0], def.footprint[1], 0x22d3ee);
  }

  private redrawGhost(): void {
    const g = this.ghost;
    for (const c of g.removeChildren()) c.destroy({ children: true });
    const def = this.ghostDef;
    if (!def || !this.state || this.hover.x < 0) return;
    const { x, y } = this.hover;
    const ok = placementError(this.map, this.state.buildings, def, x, y, this.state.stock) === null;
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
    if (def.radius) {
      // Coverage circle (iso ellipse) around the footprint centre.
      const pts: number[] = [];
      for (let i = 0; i < 48; i++) {
        const a = (i / 48) * Math.PI * 2;
        const p = gridToWorld(x + w / 2 + Math.cos(a) * def.radius, y + h / 2 + Math.sin(a) * def.radius);
        pts.push(p.x, p.y);
      }
      gfx.poly(pts).fill({ color: 0x22d3ee, alpha: 0.08 }).stroke({ color: 0x22d3ee, width: 2, alpha: 0.7 });
    }
  }
}

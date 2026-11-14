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
  private ghost = new Graphics();
  private camera!: Camera;
  private art: Art = { tiles: new Map(), buildings: new Map() };
  private built = new Map<number, Container>();
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
    this.world.addChild(this.terrain, this.objects);
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
    canvas.addEventListener('pointermove', (e) => {
      const t = tileAtEvent(e);
      this.hover = t;
      this.events.onTileHover(t.x, t.y);
      this.redrawGhost();
    });
    canvas.addEventListener('pointerup', (e) => {
      if (e.button !== 0 || this.camera.dragged) return;
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
        const art = this.art.tiles.get(cls);
        if (art) {
          this.terrain.addChild(this.makeSprite(art, p.x, p.y));
          continue;
        }
        // Slight per-tile checker variation so the grid reads.
        const c = shade(TERRAIN_COLOR[cls], (x + y) % 2 ? 1 : 0.94);
        g.poly([p.x, p.y, p.x + TILE_W / 2, p.y + TILE_H / 2, p.x, p.y + TILE_H, p.x - TILE_W / 2, p.y + TILE_H / 2]).fill(c);
      }
    }
    this.terrain.addChildAt(g, 0);
  }

  private makeSprite(s: Sprite2, x: number, y: number, additive = false): Sprite {
    const sp = new Sprite(s.tex);
    sp.anchor.set(s.anchor[0], s.anchor[1]);
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
    this.redrawGhost();
  }

  setSelected(id: number | null): void {
    this.selectedId = id;
    this.redrawSelection();
  }

  setState(state: GameState): void {
    this.state = state;
    const live = new Set<number>();
    for (const b of state.buildings) {
      live.add(b.id);
      if (!this.built.has(b.id)) this.addBuilding(b);
    }
    for (const [id, node] of this.built) {
      if (!live.has(id)) {
        node.destroy({ children: true });
        this.built.delete(id);
      }
    }
    this.redrawSelection();
    this.redrawGhost();
  }

  private addBuilding(b: Building): void {
    const def = buildingDef(b.type);
    if (!def) return;
    const [fw, fh] = def.footprint;
    const node = new Container();
    const art = this.art.buildings.get(def.id);
    if (art) {
      const c = gridToWorld(b.x + fw / 2, b.y + fh / 2);
      node.addChild(this.makeSprite(art.base, c.x, c.y));
      if (art.glow) node.addChild(this.makeSprite(art.glow, c.x, c.y, true));
    } else {
      const g = new Graphics();
      drawBox(g, b.x, b.y, fw, fh, def.height, hex(def.color));
      node.addChild(g);
    }
    node.zIndex = b.x + fw - 1 + (b.y + fh - 1);
    this.objects.addChild(node);
    this.built.set(b.id, node);
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
    g.clear();
    const def = this.ghostDef;
    if (!def || !this.state || this.hover.x < 0) return;
    const { x, y } = this.hover;
    const ok = placementError(this.map, this.state.buildings, def, x, y) === null;
    const color = ok ? 0x4ade80 : 0xf87171;
    const [w, h] = def.footprint;
    // Flat footprint tint plus a translucent box.
    const T = gridToWorld(x, y), R = gridToWorld(x + w, y), B = gridToWorld(x + w, y + h), L = gridToWorld(x, y + h);
    g.poly([T.x, T.y, R.x, R.y, B.x, B.y, L.x, L.y]).fill({ color, alpha: 0.35 });
    drawBox(g, x, y, w, h, def.height, color, 0.45);
    this.footprintOutline(g, x, y, w, h, color);
  }
}

import type { Container } from 'pixi.js';

export const MIN_ZOOM = 0.12;
export const MAX_ZOOM = 2;

/** Pan (drag, WASD) and cursor-anchored zoom (wheel) applied to a world container. */
export class Camera {
  private keys = new Set<string>();
  /** True once the pointer has moved past the click threshold during this press. */
  dragged = false;
  /** Set while a tool paints (road drag) so left-drag doesn't pan. */
  panDisabled = false;

  constructor(
    private world: Container,
    el: HTMLElement,
  ) {
    let down: { x: number; y: number } | null = null;
    el.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      down = { x: e.clientX, y: e.clientY };
      this.dragged = false;
    });
    window.addEventListener('pointermove', (e) => {
      if (!down || this.panDisabled) return;
      if (!this.dragged && Math.hypot(e.clientX - down.x, e.clientY - down.y) < 4) return;
      this.dragged = true;
      this.world.x += e.movementX;
      this.world.y += e.movementY;
    });
    window.addEventListener('pointerup', () => (down = null));
    el.addEventListener(
      'wheel',
      (e) => {
        e.preventDefault();
        const r = el.getBoundingClientRect();
        this.zoomAt(e.clientX - r.left, e.clientY - r.top, Math.exp(-e.deltaY * 0.0015));
      },
      { passive: false },
    );
    window.addEventListener('keydown', (e) => this.keys.add(e.key.toLowerCase()));
    window.addEventListener('keyup', (e) => this.keys.delete(e.key.toLowerCase()));
    window.addEventListener('blur', () => this.keys.clear());
  }

  zoomAt(sx: number, sy: number, factor: number): void {
    const w = this.world;
    const z = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, w.scale.x * factor));
    const k = z / w.scale.x;
    w.x = sx - (sx - w.x) * k;
    w.y = sy - (sy - w.y) * k;
    w.scale.set(z);
  }

  /** Per-frame WASD pan; dtMs is the frame time. */
  update(dtMs: number): void {
    const speed = 0.8 * dtMs;
    const k = this.keys;
    if (k.has('a')) this.world.x += speed;
    if (k.has('d')) this.world.x -= speed;
    if (k.has('w')) this.world.y += speed;
    if (k.has('s')) this.world.y -= speed;
  }

  /** Scale and position so the world-space box fills the view with a margin. */
  fit(box: { x: number; y: number; w: number; h: number }, viewW: number, viewH: number): void {
    const z = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Math.min(viewW / box.w, viewH / box.h) * 0.9));
    this.world.scale.set(z);
    this.world.x = viewW / 2 - (box.x + box.w / 2) * z;
    this.world.y = viewH / 2 - (box.y + box.h / 2) * z;
  }
}

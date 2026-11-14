import { Container, Filter, GlProgram, Sprite, Texture, UniformGroup } from 'pixi.js';
import ambient from '../data/ambient.json';
import look from '../data/look.json';

/* ---------- day/night ---------- */

export interface Grade {
  rgb: [number, number, number];
  glow: number;
}

/** Piecewise-linear keyframes from look.json at `hour` (0-24). */
export function gradeAt(hour: number): Grade {
  const k = look.grade;
  let i = 0;
  while (i < k.length - 2 && hour >= (k[i + 1] as { h: number }).h) i++;
  const a = k[i] as (typeof k)[number], b = k[i + 1] as (typeof k)[number];
  const t = Math.min(1, Math.max(0, (hour - a.h) / (b.h - a.h)));
  const l = (x: number, y: number) => x + (y - x) * t;
  return { rgb: [l(a.rgb[0]!, b.rgb[0]!), l(a.rgb[1]!, b.rgb[1]!), l(a.rgb[2]!, b.rgb[2]!)], glow: l(a.glow, b.glow) };
}

/* ---------- glow behaviour (deterministic per building id) ---------- */

function hash(a: number, b = 0): number {
  let h = Math.imul(a + 0x9e3779b9, 0x85ebca6b) ^ Math.imul(b + 0x7f4a7c15, 0xc2b2ae35);
  h = Math.imul(h ^ (h >>> 15), 0x2c1b3c6d);
  h = Math.imul(h ^ (h >>> 12), 0x297a2d39);
  return ((h ^ (h >>> 15)) >>> 0) / 4294967296;
}

/** Gentle shimmer plus an occasional brief dip. t in seconds. */
export function flicker(id: number, t: number): number {
  const slot = Math.floor(t * 3);
  const dip = hash(id, slot) < 0.045 ? 0.7 : 1;
  return dip * (0.96 + 0.04 * Math.sin(t * 1.7 + hash(id) * 6.28));
}

/** Aviation beacon: periodic pulse of the whole glow. */
export function beacon(id: number, t: number): number {
  const p = Math.max(0, Math.sin(((t + hash(id) * 3) / 2.4) * Math.PI * 2));
  return 0.55 + 0.45 * p * p * p;
}

/* ---------- water ---------- */

const WATER_VERT = `in vec2 aPosition;
out vec2 vTextureCoord;
uniform vec4 uInputSize;
uniform vec4 uOutputFrame;
uniform vec4 uOutputTexture;
void main(void){
  vec2 position = aPosition * uOutputFrame.zw + uOutputFrame.xy;
  position.x = position.x * (2.0 / uOutputTexture.x) - 1.0;
  position.y = position.y * (2.0*uOutputTexture.z / uOutputTexture.y) - uOutputTexture.z;
  gl_Position = vec4(position, 0.0, 1.0);
  vTextureCoord = aPosition * (uOutputFrame.zw * uInputSize.zw);
}`;

const WATER_FRAG = `precision highp float;
in vec2 vTextureCoord;
out vec4 finalColor;
uniform sampler2D uTexture;
uniform vec4 uInputSize;
uniform vec4 uOutputFrame;
uniform float uTime;
uniform float uCamX;
uniform float uCamY;
uniform float uZoom;
uniform float uSheen;
uniform float uNight;
void main(void){
  vec2 px = vTextureCoord * uInputSize.xy + uOutputFrame.xy;
  vec2 w = (px - vec2(uCamX, uCamY)) / uZoom;
  float t = uTime;
  vec2 d = vec2(sin(w.y*0.05 + t*0.8) + sin((w.x+w.y)*0.031 - t*0.55),
                cos(w.x*0.043 - t*0.65) + sin((w.x-w.y)*0.037 + t*0.45)) * 1.5 * uZoom;
  vec4 c = texture(uTexture, vTextureCoord + d * uInputSize.zw);
  float s1 = smoothstep(0.55, 1.0, sin(w.x*0.012 + w.y*0.02 + t*0.15 + sin(w.y*0.006 + t*0.2)*1.2));
  float s2 = smoothstep(0.6, 1.0, sin(w.x*0.016 - w.y*0.014 - t*0.1 + sin(w.x*0.007)*1.5));
  vec3 sheen = vec3(0.05, 0.28, 0.32) * s1 + vec3(0.25, 0.08, 0.22) * s2;
  c.rgb *= mix(vec3(1.0), vec3(0.5, 0.66, 0.64), uNight);
  c.rgb += (sheen * 0.12 + vec3(0.0, 0.02, 0.02)) * uSheen * c.a;
  finalColor = c;
}`;

/** Slow ripples (UV wobble) and an oily neon sheen; runs over the water layer only. */
export class WaterFilter extends Filter {
  private u: UniformGroup;
  constructor() {
    const u = new UniformGroup({
      uTime: { value: 0, type: 'f32' },
      uCamX: { value: 0, type: 'f32' },
      uCamY: { value: 0, type: 'f32' },
      uZoom: { value: 1, type: 'f32' },
      uSheen: { value: 0.3, type: 'f32' },
      uNight: { value: 0, type: 'f32' },
    });
    super({ glProgram: GlProgram.from({ vertex: WATER_VERT, fragment: WATER_FRAG, name: 'water' }), resources: { waterUniforms: u } });
    this.u = u;
  }
  set(t: number, camX: number, camY: number, zoom: number, sheen: number, night = 0): void {
    const v = this.u.uniforms as Record<string, number>;
    v.uTime = t;
    v.uCamX = camX;
    v.uCamY = camY;
    v.uZoom = zoom;
    v.uSheen = sheen;
    v.uNight = night;
  }
}

/* ---------- procedural textures ---------- */

function canvasTex(w: number, h: number, draw: (c: CanvasRenderingContext2D) => void): Texture {
  const cv = document.createElement('canvas');
  cv.width = w;
  cv.height = h;
  draw(cv.getContext('2d') as CanvasRenderingContext2D);
  return Texture.from(cv);
}

export function softTexture(): Texture {
  return canvasTex(64, 64, (c) => {
    const g = c.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    c.fillStyle = g;
    c.fillRect(0, 0, 64, 64);
  });
}

export function vignetteTexture(): Texture {
  return canvasTex(256, 256, (c) => {
    const g = c.createRadialGradient(128, 128, 60, 128, 128, 190);
    g.addColorStop(0, 'rgba(2,4,10,0)');
    g.addColorStop(1, 'rgba(2,4,10,0.85)');
    c.fillStyle = g;
    c.fillRect(0, 0, 256, 256);
  });
}

/** Tileable slanted rain streaks. */
export function rainTexture(seed: number, count: number): Texture {
  const S = 512;
  return canvasTex(S, S, (c) => {
    c.lineCap = 'round';
    for (let i = 0; i < count; i++) {
      const x = hash(seed, i) * S, y = hash(seed, i + 1000) * S, len = 14 + hash(seed, i + 2000) * 26;
      c.strokeStyle = `rgba(170,205,255,${0.25 + hash(seed, i + 3000) * 0.5})`;
      c.lineWidth = 1 + hash(seed, i + 4000);
      for (const ox of [-S, 0, S])
        for (const oy of [-S, 0, S]) {
          c.beginPath();
          c.moveTo(x + ox, y + oy);
          c.lineTo(x + ox - len * 0.22, y + oy + len);
          c.stroke();
        }
    }
  });
}

/* ---------- smoke / steam ---------- */

interface EmitterCfg {
  offsets: number[][];
  rate: number; life: number; rise: number; drift: number[]; size: number; grow: number; alpha: number; color: string;
}
interface Puff { s: Sprite; x: number; y: number; vx: number; age: number; life: number; cfg: EmitterCfg }
interface Emitter { x: number; y: number; cfg: EmitterCfg; acc: number; on: boolean }

export class Smoke {
  private tex = softTexture();
  private puffs: Puff[] = [];
  private free: Sprite[] = [];
  private emitters = new Map<number, Emitter[]>();
  private seed = 1;
  constructor(private layer: Container) {}

  private rnd(): number {
    this.seed = (Math.imul(this.seed, 1664525) + 1013904223) >>> 0;
    return this.seed / 4294967296;
  }

  has(type: string): boolean {
    return type in ambient.emitters;
  }

  /** Register (or update) a building's stacks; (ax, ay) is its sprite anchor in world px. */
  set(id: number, type: string, ax: number, ay: number, working: boolean): void {
    let list = this.emitters.get(id);
    if (!list) {
      const cfg = (ambient.emitters as Record<string, EmitterCfg>)[type];
      if (!cfg) return;
      list = cfg.offsets.map((o) => ({ x: ax + (o[0] ?? 0), y: ay + (o[1] ?? 0), cfg, acc: this.rnd(), on: false }));
      this.emitters.set(id, list);
    }
    for (const e of list) e.on = working;
  }

  remove(id: number): void {
    this.emitters.delete(id);
  }

  update(dt: number, night: number): void {
    for (const list of this.emitters.values())
      for (const e of list) {
        if (!e.on) continue;
        e.acc += dt * e.cfg.rate;
        while (e.acc >= 1) {
          e.acc -= 1;
          if (this.puffs.length >= ambient.maxParticles) break;
          const s = this.free.pop() ?? new Sprite(this.tex);
          s.anchor.set(0.5);
          s.tint = Number(e.cfg.color);
          this.layer.addChild(s);
          this.puffs.push({ s, x: e.x + (this.rnd() - 0.5) * 6, y: e.y, vx: (e.cfg.drift[0] ?? 0) + (this.rnd() - 0.5) * 6, age: 0, life: e.cfg.life * (0.8 + this.rnd() * 0.4), cfg: e.cfg });
        }
      }
    for (let i = this.puffs.length - 1; i >= 0; i--) {
      const p = this.puffs[i] as Puff;
      p.age += dt;
      if (p.age >= p.life) {
        p.s.removeFromParent();
        this.free.push(p.s);
        this.puffs.splice(i, 1);
        continue;
      }
      const f = p.age / p.life;
      p.x += p.vx * dt;
      p.y -= p.cfg.rise * dt * (1 - f * 0.5);
      p.s.position.set(p.x, p.y);
      p.s.scale.set(p.cfg.size * (1 + p.cfg.grow * f));
      p.s.alpha = p.cfg.alpha * Math.min(1, f * 8) * (1 - f) * (1 - 0.35 * night);
    }
  }
}

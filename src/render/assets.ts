import { Assets, Texture } from 'pixi.js';

interface Entry {
  file: string;
  glow?: string;
  anchor: [number, number];
}
interface Manifest {
  tiles?: Record<string, Entry>;
  buildings?: Record<string, Entry>;
  units?: Record<string, Entry>;
}

export interface Sprite2 {
  tex: Texture;
  anchor: [number, number];
}
export interface BuildingArt {
  base: Sprite2;
  glow?: Sprite2;
}

/** Optional generated art. Anything missing falls back to Graphics placeholders per key. */
export interface Art {
  tiles: Map<string, Sprite2>;
  buildings: Map<string, BuildingArt>;
  /** Ships: hauler_<dir>, trader_<dir>, patrol_<dir>. */
  units: Map<string, BuildingArt>;
}

export async function loadArt(): Promise<Art> {
  const art: Art = { tiles: new Map(), buildings: new Map(), units: new Map() };
  let manifest: Manifest;
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}assets/manifest.json`);
    if (!res.ok) return art;
    manifest = (await res.json()) as Manifest;
  } catch {
    return art;
  }
  const load = async (file: string, anchor: [number, number]): Promise<Sprite2 | undefined> => {
    try {
      // Straight-alpha PNGs: premultiply on upload so additive glow reads as light, not haze.
      const tex = await Assets.load<Texture>({
        src: `${import.meta.env.BASE_URL}assets/${file}`,
        data: { alphaMode: 'premultiply-alpha-on-upload' },
      });
      return { tex, anchor };
    } catch {
      return undefined;
    }
  };
  await Promise.all([
    ...Object.entries(manifest.tiles ?? {}).map(async ([key, e]) => {
      const s = await load(e.file, e.anchor);
      if (s) art.tiles.set(key, s);
    }),
    ...(['buildings', 'units'] as const).flatMap((section) =>
      Object.entries(manifest[section] ?? {}).map(async ([key, e]) => {
        const base = await load(e.file, e.anchor);
        if (!base) return;
        const glow = e.glow ? await load(e.glow, e.anchor) : undefined;
        art[section].set(key, { base, glow });
      }),
    ),
  ]);
  return art;
}

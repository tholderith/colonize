/** Seeded mulberry32. Same seed, same sequence. */
export interface Rng {
  /** Float in [0, 1). */
  next(): number;
  /** Integer in [0, n). */
  int(n: number): number;
  /** Float in [a, b). */
  range(a: number, b: number): number;
  /** Generator state, for saving. */
  state: number;
}

export function createRng(seed: number): Rng {
  let s = seed >>> 0;
  const next = () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  return {
    get state() {
      return s;
    },
    set state(v: number) {
      s = v >>> 0;
    },
    next,
    int: (n) => Math.floor(next() * n),
    range: (a, b) => a + next() * (b - a),
  };
}

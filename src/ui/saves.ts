import type { Difficulty } from '../sim/types';

export type StartDesc = { kind: 'new'; seed: number; difficulty: Difficulty } | { kind: 'load'; data: string };
export type Slot = 'auto' | 'manual';

const key = (slot: Slot) => `foundry.save.${slot}`;

/** localStorage can be missing, full or blocked: every access is guarded. */
export function writeSave(slot: Slot, data: string): boolean {
  try {
    localStorage.setItem(key(slot), data);
    return true;
  } catch {
    return false;
  }
}
export function readSave(slot: Slot): string | null {
  try {
    return localStorage.getItem(key(slot));
  } catch {
    return null;
  }
}
export interface SaveMeta {
  tick: number;
  seed: number;
  difficulty: Difficulty;
}
export function saveMeta(data: string | null): SaveMeta | null {
  try {
    const s = JSON.parse(data ?? '') as { seed: number; difficulty: Difficulty; state: { tick: number } };
    return { tick: s.state.tick, seed: s.seed, difficulty: s.difficulty };
  } catch {
    return null;
  }
}

/** Save to a file via a temporary download link. */
export function downloadSave(data: string, name: string): void {
  const url = URL.createObjectURL(new Blob([data], { type: 'application/json' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 5000);
}

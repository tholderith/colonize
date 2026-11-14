import type { Command, Difficulty, GameState } from './types';

export type ToWorker =
  | { type: 'init'; seed: number; difficulty: Difficulty }
  /** `data` is a save JSON string. */
  | { type: 'load'; data: string }
  | { type: 'save'; slot: 'manual' | 'export' }
  | { type: 'command'; cmd: Command };
export type FromWorker =
  | { type: 'state'; state: GameState }
  /** Save JSON string; `auto` is posted by the worker every 2 in-game minutes. */
  | { type: 'save'; slot: 'auto' | 'manual' | 'export'; data: string }
  | { type: 'error'; msg: string };

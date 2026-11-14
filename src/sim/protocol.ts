import type { Command, GameState } from './types';

export type ToWorker = { type: 'init'; seed: number } | { type: 'command'; cmd: Command };
export type FromWorker = { type: 'state'; state: GameState };

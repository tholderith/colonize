/** Deterministic time of day, derived purely from the tick count. */
export const DAY_TICKS = 4800; // 8 in-game minutes per day at 1x
export const START_HOUR = 19; // dusk

/** Hour of day in [0, 24). */
export function hourOfDay(tick: number): number {
  return (START_HOUR + (tick / DAY_TICKS) * 24) % 24;
}

/** 1-based day number. */
export function dayOf(tick: number): number {
  return Math.floor((START_HOUR / 24 + tick / DAY_TICKS)) + 1;
}

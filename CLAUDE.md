# Foundry (working title)

Real-time-with-pause colony builder: Anno-style production chains + Colonization-style
dependence → independence arc, in a retro-future industrial archipelago ("Neon Foundry" look).
The colony is chartered by the **Concordat**, which levies, taxes and audits; the player can
eventually declare independence.

Full plan: https://claude.ai/artifact/KSHkPScWG8Z69Dth5ZDsvS · Progress log: `PROGRESS.md`
Art bake-off (reference only, do not modify): branch `art-samples` — the Neon Foundry generator
lives at `art-samples/styles/neon/src/` on that branch (`git show art-samples:<path>`).

## Stack
- TypeScript, Vite, PixiJS v8 for the map; plain HTML/CSS for all UI panels (no React unless the lead approves).
- Simulation core in `src/sim/`: pure TypeScript, NO imports from DOM/Pixi/UI. Runs in a Web
  Worker at a fixed 10 Hz tick; receives commands, emits snapshots. Deterministic: seeded RNG only,
  no `Math.random`, no `Date.now` inside the sim.
- Tests: Vitest (`npm test`) for the sim; Playwright screenshot smoke test (`npm run e2e -- --trace off`).
  Chromium + Playwright are preinstalled; never run `playwright install`.
- Art: Blender 4.0.2 + Cycles scripts in `art/` (no OpenImageDenoise: `use_denoising=False`).
  Generated sprites go to `public/assets/`. Every building = base sprite + separate glow layer.
- Iso projection: 2:1 tiles, 128×64 px. Camera for 3D renders: ortho, yaw 45°, pitch 30°.

## Layout
- `src/sim/` simulation · `src/render/` Pixi renderer · `src/ui/` HTML UI · `src/data/` JSON game data
- `art/` asset generators · `public/assets/` generated assets · `tests/` · `docs/`

## Team rules (agents read this)
- Lead/PM: Opus. Builders: Sonnet. Routine checks (tests, screenshots, triage): Haiku.
- Stay inside the scope and directories your brief names. Don't refactor outside it.
- "Done" = the brief's acceptance checks pass (`npm run check` = typecheck + lint + tests).
- At most two revision rounds on visual work unless the lead asks for more. Iterate at low
  render quality; final renders once.
- Don't commit or push; the lead reviews and merges. Report briefly: what changed, how verified,
  what's left.
- Never invent results. If something can't be verified, say so.
- Don't overbake. Build what the brief asks, the simplest way that works, then stop.
- Testing is lean: unit tests only for sim logic that's easy to get wrong (determinism,
  economy maths, placement rules). No tests for UI/layout. Full checks (`npm run check`, e2e,
  screenshot review) run at milestone gates, not on every change; between gates, typecheck +
  the tests for what you touched is enough.

## Reporting to the user
- Each scheduled check-in or milestone gate: one short update with a screenshot of the
  current build and basic metrics, in a table: milestone, % of milestone tasks done, days
  elapsed vs estimate, LOC (src), tests passing, building/asset count, open issues.
- Keep it to a few lines; no essays.

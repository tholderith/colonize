# QA report: M5 (static preview of `dist/`)

Build: `npm run build` passed (tsc + vite, no errors). Served with `vite preview --port 4180`.
Browser: headless Chromium via Playwright, software WebGL. Viewport 1600x900 unless noted.
Screenshots: `/tmp/claude-0/qa/` (01-menu … 10-1920x1080, 11-info-depot.png).
Runtime: 3x speed, about 60 s real time, 5 buildings placed through the build menu.

## Summary

| Severity | Count |
| --- | --- |
| Blocker | 0 |
| Major | 2 |
| Minor | 9 |

Console: 0 errors, 0 page errors. 4 warnings (WebGL driver, see #11).
Frame rate: 16 rAF callbacks in 5 s (about 3 fps) in headless software rendering. This is not a real-GPU number.
Sim speed check: 29.7 ticks/s real time at 3x (matches 3 × 10 Hz).

## Issues

| # | severity | area | what happens | how to reproduce |
| --- | --- | --- | --- | --- |
| 1 | major | Save / Continue | After SAVE, reload, the menu's CONTINUE button is disabled ("no autosave"). CONTINUE only loads the AUTOSAVE slot, and autosave only fires every 2 in-game minutes. The manual save is reachable only through LOAD > MANUAL SLOT. A first-time player who presses SAVE and then CONTINUE will find nothing to continue. In a run where the autosave existed, CONTINUE loaded the autosave (tick 2439) and not the manual save. | New Game, wait about 10 s, click SAVE, reload, look at CONTINUE. It is disabled, with "no autosave" under it. Manual slot shows "seed … 1 min played" under LOAD. |
| 2 | major | Building selection | With a build tool still armed, clicking a built building on the map does not open the INFO panel. The click goes to placement instead (it fails on the occupied tile). The build tool stays armed after a placement (the last-placed item stays highlighted, Depot in 04/05 screenshots), with no visible hint about how to cancel it. Cause is inferred from the sequence; the placement attempt was not checked directly. | New Game, click a build item, place a building, then click the same building without choosing another item or Escape. INFO stays "Nothing selected". With no tool armed, clicking a 2x2 depot at its centre tile shows "Depot #1 at (19, 25) / Radius 10 · cap 100/good / DEMOLISH". |
| 3 | minor | Rendering performance | Headless software rendering gives about 3 fps (16 rAF callbacks in 5 s). Not representative of a real GPU. Needs a check on real hardware. | Run the page in headless Chromium, count `requestAnimationFrame` calls over 5 s. |
| 4 | minor | Panels, 1600x900 | Opening EXCHANGE while CONCORDAT is open puts EXCHANGE over the CONCORDAT panel, hiding its text (independence %, levy, demand). Nothing closes the other panel. | New Game, click CONCORDAT (on by default), then EXCHANGE. |
| 5 | minor | Panels, 1280x720 | The CONCORDAT panel sits over the lower-right corner of the top HUD bar in the screenshot. Auto overlap check (bounding boxes) reported no overlap, so this is visual only. No horizontal page scroll at 1280x720 or 1920x1080. | New Game, resize to 1280x720, view. |
| 6 | minor | Build menu | The selected Depot's button text ("2x2 · 200cr 15 alloy") is low contrast on the gold highlight. | New Game, look at the BUILD list while Depot is armed. |
| 7 | minor | Placement tooltip | The bottom-centre tooltip "Depot · cost 200cr 15 alloy · radius 10" stays on screen after the cursor leaves the map and no build item is being hovered. | Place a depot, move the mouse off the map (over the HUD). The tooltip remains. |
| 8 | minor | HUD | The HUD island name, POWER and COLONISTS figures follow the island under the camera centre, not the colony. On a fresh island after CONTINUE, HUD read "Soot Shoal / POWER 0/0 / cap 0" with no label saying this is a different island. | Pan the camera to another island, watch the HUD change. |
| 9 | minor | First-time guidance | No tutorial, objective or next-step hint. First screen after NEW GAME shows INFO "Nothing selected" and CONCORDAT "No pressure on the colony yet", with nothing saying what to build first. | New Game (Standard), look at the first screen. |
| 10 | minor | Jargon / labels | CONCORDAT panel uses terms with no explanation: "Levy 10% in 1:20 · earned 25 cr", "Demand next in 4:20", "Tariff 15% · contraband exposure 0.0". The top bar shows "POWER 2/10" with no unit or meaning. EXCHANGE says "Sell net" without saying what the net is. | Read the CONCORDAT and EXCHANGE panels on a fresh game. |
| 11 | minor | Console | Four WebGL driver warnings, verbatim (trimmed): `[.WebGL-0x383c01781a00]GL Driver Message (OpenGL, Performance, GL_CLOSE_PATH_NV, High): GPU stall due to ReadPixels` (three times, then "(this message will no longer repeat)"). Likely from the software renderer, not game code. | Load the page, New Game, play for about 60 s, read the console. |
| 12 | minor | Menu | CONTINUE's "no autosave" subtext is very small and dim, and it is hard to read. | Load the menu on a fresh profile. |

## Checks that passed (observed)

- NEW GAME (Standard) starts a game. Seed field pre-fills, RANDOM works.
- Speed buttons work: 3x gives 29.7 ticks/s real time, active class set on 3x.
- Five builds placed from the build menu (wind turbine, pod house, hydroponics, scrap yard, depot), with the building counts going up in the state.
- EXCHANGE, CONCORDAT and build menu panels open. EXCHANGE rows show SELL/BUY and amounts.
- SAVE writes the manual slot (`foundry.save.manual`). Autosave also writes after the 2-minute interval.
- Reload to menu, then CONTINUE from autosave (after autosave existed) loads the game with buildings intact.
- No horizontal page scroll at 1280x720 or 1920x1080. No bounding-box overlaps among the visible panels at either size.
- No page errors (`pageerror`) during the run.

## Not checked

- Real-GPU frame rate.
- LOAD > MANUAL SLOT and EXPORT/IMPORT paths.
- Hauler and trade routes, declare-independence flow, endings.
- Mobile widths.

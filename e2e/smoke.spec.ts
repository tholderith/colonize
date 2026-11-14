import { expect, test } from '@playwright/test';

interface Foundry {
  ready(): boolean;
  canPlace(id: string, x: number, y: number): boolean;
  tileToScreen(x: number, y: number): { x: number; y: number };
  place(id: string, x: number, y: number): void;
  state(): { tick: number; buildings: { id: number; type: string; x: number; y: number; status: string }[]; stock: Record<string, number> };
}

test('build a tiny working colony, inspect it, screenshot', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await page.locator('#map canvas').waitFor();
  await page.waitForFunction(() => (window as unknown as { __foundry: Foundry }).__foundry?.ready());
  const box = (await page.locator('#map canvas').boundingBox())!;

  // A start depot exists and the HUD shows real stock.
  await expect(page.locator('[data-good="credits"]')).toContainText('2000');
  const depot = await page.evaluate(() => (window as unknown as { __foundry: Foundry }).__foundry.state().buildings.find((b) => b.type === 'depot') ?? null);
  expect(depot).not.toBeNull();

  // Place the first turbine through the real UI (build menu + mouse) next to the depot.
  const spot = await page.evaluate((d) => {
    const f = (window as unknown as { __foundry: Foundry }).__foundry;
    for (let r = 2; r < 6; r++)
      for (let dy = -r; dy <= r; dy++)
        for (let dx = -r; dx <= r; dx++) if (f.canPlace('wind_turbine', d!.x + dx, d!.y + dy)) return [d!.x + dx, d!.y + dy] as [number, number];
    return null;
  }, depot);
  expect(spot).not.toBeNull();
  await page.click('[data-building="wind_turbine"]');
  await expect(page.locator('#place-info')).toContainText('cost');
  const p = await page.evaluate(([x, y]) => (window as unknown as { __foundry: Foundry }).__foundry.tileToScreen(x, y), spot!);
  await page.mouse.move(box.x + p.x, box.y + p.y);
  await page.mouse.click(box.x + p.x, box.y + p.y);
  await page.click('[data-building="wind_turbine"]'); // leave build mode
  await page.waitForFunction(() => (window as unknown as { __foundry: Foundry }).__foundry.state().buildings.some((b) => b.type === 'wind_turbine'));

  // Rest of the colony through the test hook, nearest free spots around the depot.
  await page.evaluate((d) => {
    const f = (window as unknown as { __foundry: Foundry }).__foundry;
    const size: Record<string, number> = { hydroponics: 2, ration_plant: 2, pod_house: 1 };
    const taken: [number, number, number][] = f.state().buildings.map((b) => [b.x, b.y, b.type === 'depot' ? 2 : 1]);
    const free = (x: number, y: number, s: number) => taken.every(([tx, ty, ts]) => x + s <= tx || tx + ts <= x || y + s <= ty || ty + ts <= y);
    const cands: [number, number][] = [];
    for (let y = d!.y - 7; y <= d!.y + 8; y++) for (let x = d!.x - 7; x <= d!.x + 8; x++) cands.push([x, y]);
    cands.sort((a, b) => Math.hypot(a[0] - d!.x - 1, a[1] - d!.y - 1) - Math.hypot(b[0] - d!.x - 1, b[1] - d!.y - 1));
    for (const id of ['hydroponics', 'ration_plant', 'pod_house', 'pod_house', 'pod_house', 'pod_house']) {
      const s = size[id]!;
      const c = cands.find(([x, y]) => f.canPlace(id, x, y) && free(x, y, s));
      if (!c) continue;
      taken.push([c[0], c[1], s]);
      f.place(id, c[0], c[1]);
    }
  }, depot);
  await page.click('[data-speed="3"]');
  await page.waitForTimeout(12_000);

  // Select the hydroponics shed: the building panel shows status.
  const hydro = await page.evaluate(() => (window as unknown as { __foundry: Foundry }).__foundry.state().buildings.find((b) => b.type === 'hydroponics') ?? null);
  expect(hydro).not.toBeNull();
  const hp = await page.evaluate(([x, y]) => (window as unknown as { __foundry: Foundry }).__foundry.tileToScreen(x + 1, y + 1), [hydro!.x, hydro!.y] as [number, number]);
  await page.mouse.click(box.x + hp.x, box.y + hp.y);
  await expect(page.locator('#info-body')).toContainText('Hydroponics');
  await expect(page.locator('#info-body')).toContainText('Status');
  await page.mouse.move(box.x + 5, box.y + box.height - 5);
  await page.screenshot({ path: 'test-results/m1.png' });

  const st = await page.evaluate(() => (window as unknown as { __foundry: Foundry }).__foundry.state());
  expect(st.stock.biomass).toBeGreaterThan(0);
  expect(errors).toEqual([]);
});

import { expect, test } from '@playwright/test';

interface Foundry {
  ready(): boolean;
  canPlace(id: string, x: number, y: number): boolean;
  tileToScreen(x: number, y: number): { x: number; y: number };
  place(id: string, x: number, y: number): void;
}

test('load, place a building via the UI, screenshot', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await page.locator('#map canvas').waitFor();
  await page.waitForFunction(() => (window as unknown as { __foundry: Foundry }).__foundry?.ready());

  // First land tile (scan order) where a pod house fits with room to spare.
  const spot = await page.evaluate(() => {
    const f = (window as unknown as { __foundry: Foundry }).__foundry;
    for (let y = 0; y < 64; y++)
      for (let x = 0; x < 64; x++) if (f.canPlace('pod_house', x, y) && f.canPlace('pod_house', x + 2, y + 2)) return [x, y] as [number, number];
    return null;
  });
  expect(spot).not.toBeNull();

  await page.click('[data-building="pod_house"]');
  const p = await page.evaluate(([x, y]) => (window as unknown as { __foundry: Foundry }).__foundry.tileToScreen(x, y), spot!);
  const box = (await page.locator('#map canvas').boundingBox())!;
  await page.mouse.move(box.x + p.x, box.y + p.y);
  await page.mouse.click(box.x + p.x, box.y + p.y);
  await page.click('[data-building="pod_house"]'); // leave build mode
  await page.mouse.click(box.x + p.x, box.y + p.y); // select it
  await expect(page.locator('#info-body')).toContainText('Pod House');
  await page.mouse.move(box.x + 5, box.y + box.height - 5);
  await page.screenshot({ path: 'test-results/m0.png' });

  // One of each building on land, spread out, for a second look.
  await page.evaluate(() => {
    const f = (window as unknown as { __foundry: Foundry }).__foundry;
    const ids = ['pod_house', 'hydroponics', 'scrap_yard', 'smelter', 'wind_turbine', 'depot'];
    const placed: [number, number][] = [];
    for (const id of ids)
      scan: for (let y = 0; y < 64; y++)
        for (let x = 0; x < 64; x++)
          if (f.canPlace(id, x, y) && placed.every(([px, py]) => Math.abs(px - x) + Math.abs(py - y) > 7)) {
            f.place(id, x, y);
            placed.push([x, y]);
            break scan;
          }
  });
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'test-results/m0-all.png' });
  expect(errors).toEqual([]);
});

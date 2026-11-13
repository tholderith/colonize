// node render.cjs <style-dir> <out.png> — serve dist/ + the style folder + layout, screenshot with Playwright.
const path = require('path');
const fs = require('fs');
const { startServer } = require('./static-server.cjs');

function loadPlaywright() {
  for (const from of [__dirname, process.cwd(), '/opt/node-tools']) {
    try { return require(require.resolve('playwright', { paths: [from] })); } catch {}
  }
  return require('playwright'); // NODE_PATH fallback
}

async function main() {
  const [styleArg, outArg] = process.argv.slice(2);
  if (!styleArg || !outArg) throw new Error('usage: render.cjs <style-dir> <out.png>');
  const styleDir = path.resolve(styleArg);
  const out = path.resolve(outArg);
  const root = path.resolve(__dirname, '..');
  const layout = path.resolve(root, '../../scene/layout.json');
  if (!fs.existsSync(path.join(styleDir, 'manifest.json'))) throw new Error(`no manifest.json in ${styleDir}`);

  const t0 = Date.now();
  const server = await startServer({
    '/': path.join(root, 'dist'),
    '/layout.json': layout,
    '/styles/__render__/': styleDir,
  });
  const url = `http://127.0.0.1:${server.address().port}/index.html?mode=render&styleBase=styles/__render__/`;
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    const logs = [];
    page.on('console', (m) => logs.push(`[${m.type()}] ${m.text()}`));
    page.on('pageerror', (e) => logs.push(`[pageerror] ${e.message}`));
    await page.goto(url);
    const state = await page.waitForFunction(() => window.__render, null, { timeout: 60000 }).then((h) => h.jsonValue());
    if (state !== 'done') throw new Error(`render failed: ${state}\n${logs.join('\n')}`);
    fs.mkdirSync(path.dirname(out), { recursive: true });
    await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1920, height: 1080 } });
    console.log(`wrote ${out} (${Date.now() - t0} ms)`);
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch((e) => { console.error(e.message || e); process.exit(1); });

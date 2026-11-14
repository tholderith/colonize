// Low-Poly art generator: three.js models -> 2:1 isometric PNG sprites (headless Chromium).
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const out = path.resolve(__dirname, '..');
const read = f => fs.readFileSync(path.join(__dirname, f), 'utf8');
const three = fs.readFileSync(path.join(__dirname, 'node_modules/three/build/three.cjs'), 'utf8');
const save = (name, url) => fs.writeFileSync(path.join(out, name), Buffer.from(url.split(',')[1], 'base64'));
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage();
  page.on('console', m => console.log('[page]', m.text())); page.on('pageerror', e => console.log('[err]', e.message));
  await page.setContent('<html><body style="margin:0"></body></html>');
  await page.addScriptTag({ content: `window.THREE=(function(){var exports={};var module={exports:exports};${three}\nreturn exports;})();` });
  await page.addScriptTag({ content: [read('lib.js'), read('models.js'), read('sprites.js')].join('\n') });
  await page.evaluate(() => { document.body.appendChild(renderer_init()); function renderer_init() { init(); return renderer.domElement; } });
  const manifest = { name: 'Low-Poly', background: '#4f86c6', filter: 'linear', sprites: {}, overlays: [] };
  const terr = { deep_water: 3, shallow_water: 3, sand: 2, grass: 4, road: 2 };
  for (const [k, n] of Object.entries(terr)) {
    const files = [];
    for (let v = 0; v < n; v++) { const r = await page.evaluate(([k, v]) => buildTerrain(k, v), [k, v]); const f = `${k}_${v}.png`; save(f, r.url); files.push(f); manifest.sprites[k] = { files, anchor: r.anchor }; }
  }
  const keys = ['tree', 'rock', 'house', 'farmhouse', 'windmill', 'lumberjack', 'chapel', 'warehouse', 'wheat_field', 'pier', 'ship', 'cart', 'colonist'];
  for (const k of keys) {
    const r = await page.evaluate(k => buildSprite(k), k);
    const files = r.urls.map((u, v) => { const f = r.urls.length > 1 ? `${k}_${v}.png` : `${k}.png`; save(f, u); return f; });
    manifest.sprites[k] = { files, anchor: r.anchor }; if (r.flat) manifest.sprites[k].flat = true;
  }
  const ui = await page.evaluate(() => buildUI()); save('ui_topbar.png', ui.top); save('ui_panel.png', ui.panel);
  manifest.overlays.push({ file: 'ui_topbar.png', pos: [0, 0], anchor: [0, 0] }, { file: 'ui_panel.png', pos: [24, 1056], anchor: [0, 300] });
  fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(manifest, null, 1));
  await browser.close();
})();

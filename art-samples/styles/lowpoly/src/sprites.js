const SPRITES = {
  tree:      { n: 3, fp: [1, 1], build: v => tree(v) },
  rock:      { n: 1, fp: [1, 1], build: () => rock() },
  house:     { n: 3, fp: [1, 1], build: v => house(v) },
  farmhouse: { n: 1, fp: [1, 1], build: farmhouse },
  windmill:  { n: 1, fp: [1, 1], build: windmill, tall: 1 },
  lumberjack:{ n: 1, fp: [1, 1], build: lumberjack },
  chapel:    { n: 1, fp: [2, 2], build: chapel, tall: 1 },
  warehouse: { n: 1, fp: [2, 2], build: warehouse },
  wheat_field:{ n: 1, fp: [2, 2], build: wheat, flat: 1 },
  pier:      { n: 1, fp: [1, 1], build: pier, flat: 1, water: 1 },
  ship:      { n: 1, fp: [2, 2], build: ship, water: 1, clip: 1, tall: 1 },
  cart:      { n: 1, fp: [1, 1], build: cart },
  colonist:  { n: 1, fp: [1, 1], build: colonist },
};
window.buildSprite = (key) => {
  const s = SPRITES[key]; const rs = []; let b = { x0: 1e9, y0: 1e9, x1: -1, y1: -1 };
  for (let v = 0; v < s.n; v++) { const r = renderObject(() => s.build(v), s.fp[0], s.fp[1], { clipY: s.clip, tall: s.tall }); rs.push(r); b = bbox(r.cvs, b); }
  const W = rs[0].cvs.width, H = rs[0].cvs.height;
  b = { x0: Math.max(0, b.x0 - 1), y0: Math.max(0, b.y0 - 1), x1: Math.min(W - 1, b.x1 + 1), y1: Math.min(H - 1, b.y1 + 1) };
  const lift = s.water ? 0 : 10; // sprites standing on land are raised by the land lip (10px)
  return { urls: rs.map(r => cropTo(r.cvs, b)), anchor: [rs[0].ax - b.x0, rs[0].ay - b.y0 + lift], flat: !!s.flat };
};
window.buildTerrain = (k, v) => terrainTile(k, v);
window.init = () => setup();

// ---------- UI (2D canvas) ----------
window.buildUI = () => {
  const font = (px, b) => `${b ? 'bold ' : ''}${px}px "DejaVu Sans", sans-serif`;
  const ink = '#2f3a5c', paper = '#fbf6ea', accent = '#6f8fc9';
  const rr = (x, c, X, Y, w, h, r) => { x.beginPath(); x.roundRect(X, Y, w, h, r); x.fillStyle = c; x.fill(); };
  function icon(x, kind, cx, cy, s) { // faceted flat icons, centred, size s
    x.save(); x.translate(cx, cy); const k = s / 40; x.scale(k, k);
    const poly = (pts, c) => { x.beginPath(); pts.forEach((p, i) => i ? x.lineTo(p[0], p[1]) : x.moveTo(p[0], p[1])); x.closePath(); x.fillStyle = c; x.fill(); };
    if (kind === 'gold') { poly([[-14, -4], [0, -16], [14, -4], [14, 6], [0, 16], [-14, 6]], '#e9b92f'); poly([[-14, -4], [0, -16], [0, 0]], '#fbe58a'); poly([[0, 0], [14, -4], [14, 6], [0, 16]], '#d19a1e'); poly([[-6, -2], [0, -6], [6, -2], [0, 2]], '#f6d055'); }
    if (kind === 'wood') { poly([[-16, -8], [16, -8], [16, 8], [-16, 8]], '#b98a5b'); poly([[-16, -8], [16, -8], [16, -2], [-16, -2]], '#d6aa73'); x.beginPath(); x.ellipse(-16, 0, 6, 8, 0, 0, 7); x.fillStyle = '#ecc791'; x.fill(); x.beginPath(); x.ellipse(-16, 0, 2.5, 3.5, 0, 0, 7); x.fillStyle = '#b98a5b'; x.fill(); poly([[-8, 8], [16, 8], [16, 16], [-8, 16]], '#8f6540'); }
    if (kind === 'brick') { poly([[-16, -10], [16, -10], [20, -4], [-12, -4]], '#f0a58f'); poly([[-12, -4], [20, -4], [20, 10], [-12, 10]], '#e0735e'); poly([[-16, -10], [-12, -4], [-12, 10], [-16, 4]], '#c65a48'); x.fillStyle = '#f6c3b4'; x.fillRect(-8, 0, 10, 2); }
    if (kind === 'tools') { x.rotate(-0.6); poly([[-3, -16], [3, -16], [3, 18], [-3, 18]], '#b98a5b'); poly([[-12, -18], [12, -18], [14, -8], [-14, -8]], '#a4a1b8'); poly([[-12, -18], [0, -18], [0, -8], [-14, -8]], '#d3d0e2'); }
    if (kind === 'food') { poly([[0, -16], [8, -4], [0, 16], [-8, -4]], '#eccb5f'); poly([[0, -16], [8, -4], [0, 0]], '#f7e58f'); poly([[-10, 2], [-18, -6], [-10, 14]], '#dcb44a'); poly([[10, 2], [18, -6], [10, 14]], '#dcb44a'); }
    if (kind === 'cloth') { poly([[-16, -12], [14, -12], [18, 12], [-12, 12]], '#c7a4e2'); poly([[-16, -12], [14, -12], [16, -4], [-15, -4]], '#e1c9f2'); poly([[-12, 4], [18, 4], [18, 12], [-12, 12]], '#a984cb'); }
    if (kind === 'pop') { poly([[-4, -2], [4, -2], [10, 16], [-10, 16]], '#6f8fc9'); x.beginPath(); x.arc(0, -9, 7, 0, 7); x.fillStyle = '#f5cfb0'; x.fill(); poly([[-8, -12], [8, -12], [0, -20]], '#e0735e'); }
    x.restore();
  }
  window.__icon = icon;
  // top bar
  const tb = document.createElement('canvas'); tb.width = 1920; tb.height = 72; let x = tb.getContext('2d');
  let g = x.createLinearGradient(0, 0, 0, 72); g.addColorStop(0, '#3d4f86'); g.addColorStop(1, '#2f3f72'); x.fillStyle = g; x.fillRect(0, 0, 1920, 72);
  x.fillStyle = 'rgba(255,255,255,0.10)'; x.fillRect(0, 0, 1920, 3); x.fillStyle = 'rgba(20,28,60,0.45)'; x.fillRect(0, 68, 1920, 4);
  // faceted flourish
  x.fillStyle = 'rgba(255,255,255,0.04)'; for (let i = 0; i < 24; i++) { x.beginPath(); x.moveTo(i * 90, 0); x.lineTo(i * 90 + 60, 72); x.lineTo(i * 90 - 20, 72); x.fill(); }
  const res = [['gold', '2,480', '+12'], ['wood', '186', '+4'], ['brick', '74', '+1'], ['tools', '32', '0'], ['food', '215', '+9'], ['cloth', '58', '-2'], ['pop', '143', '+5']];
  const cw = 196, x0 = 36;
  res.forEach((r, i) => {
    const X = x0 + i * (cw + 10);
    rr(x, 'rgba(255,255,255,0.12)', X, 12, cw, 46, 23);
    rr(x, '#fbf6ea', X + 5, 17, 36, 36, 18); icon(x, r[0], X + 23, 35, 32);
    x.fillStyle = '#fbf6ea'; x.font = font(21, true); x.textBaseline = 'middle'; x.fillText(r[1], X + 52, 33);
    x.font = font(13, true); x.fillStyle = r[2].startsWith('-') ? '#ffb4a6' : r[2] === '0' ? '#c8cfe8' : '#b9f0b0'; x.fillText(r[2], X + 52 + x.measureText(r[1]).width * 0 + 76, 36);
  });
  x.textAlign = 'right'; x.font = font(18, true); x.fillStyle = '#fbf6ea'; x.fillText('Spring 1612', 1884, 28); x.font = font(13); x.fillStyle = '#c8cfe8'; x.fillText('Harbour of Saltmere   ||  x2', 1884, 49);
  // info panel
  const pn = document.createElement('canvas'); pn.width = 360; pn.height = 300; x = pn.getContext('2d');
  x.shadowColor = 'rgba(30,40,80,0.35)'; x.shadowBlur = 14; x.shadowOffsetY = 4; rr(x, paper, 8, 8, 344, 284, 18); x.shadowColor = 'transparent';
  rr(x, '#3d4f86', 8, 8, 344, 54, 18); x.fillStyle = '#3d4f86'; x.fillRect(8, 40, 344, 22);
  rr(x, '#fbf6ea', 20, 18, 34, 34, 8);
  // warehouse mini icon
  x.fillStyle = '#e3b98a'; x.fillRect(25, 33, 24, 14); x.beginPath(); x.moveTo(22, 34); x.lineTo(37, 22); x.lineTo(52, 34); x.closePath(); x.fillStyle = '#58a9a0'; x.fill();
  x.textAlign = 'left'; x.textBaseline = 'middle'; x.fillStyle = '#fff'; x.font = font(20, true); x.fillText('Harbour Warehouse', 66, 29); x.font = font(12); x.fillStyle = '#c8cfe8'; x.fillText('Storage 412 / 600   -   Level 2', 66, 49);
  const rows = [['wood', 'Timber', 186, 0.62], ['brick', 'Bricks', 74, 0.25], ['food', 'Grain', 215, 0.72], ['cloth', 'Cloth', 58, 0.2], ['tools', 'Tools', 32, 0.11]];
  rows.forEach((r, i) => {
    const Y = 76 + i * 40;
    rr(x, '#efe6d0', 20, Y, 320, 34, 10); icon(x, r[0], 40, Y + 17, 26);
    x.fillStyle = ink; x.font = font(15, true); x.fillText(r[1], 64, Y + 17);
    rr(x, '#d9d0b8', 150, Y + 12, 120, 10, 5); rr(x, [accent, '#e0735e', '#e7b84f', '#a984cb', '#58a9a0'][i], 150, Y + 12, 120 * r[3], 10, 5);
    x.textAlign = 'right'; x.font = font(16, true); x.fillStyle = ink; x.fillText(String(r[2]), 328, Y + 17); x.textAlign = 'left';
  });
  rr(x, accent, 20, 268 - 8, 150, 0.1, 0);
  return { top: tb.toDataURL(), panel: pn.toDataURL() };
};

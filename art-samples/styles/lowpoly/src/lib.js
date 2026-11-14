// Browser-side library: runs inside headless Chromium with global THREE.
const S = 90.50966799187809;           // px per world unit along the ground axes (1 tile -> 128x64 diamond)
const SS = 2;                          // supersampling
const LAND_H = 10 / (S * Math.cos(Math.atan(0.5))); // land top lifted exactly 10px on screen
const PITCH = Math.atan(0.5);

const C = (h) => new THREE.Color(h);
function mat(hex, o = {}) { return new THREE.MeshLambertMaterial(Object.assign({ color: hex, flatShading: true }, o)); }
const mcache = {};
function M(hex) { return mcache[hex] || (mcache[hex] = mat(hex)); }

// deterministic rng
function rng(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }

function flat(geo) { const g = geo.index ? geo.toNonIndexed() : geo; g.computeVertexNormals(); return g; }
function mesh(geo, color, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(flat(geo), M(color)); m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; return m;
}
function jitter(geo, amt, seed) {
  const r = rng(seed); const p = geo.attributes.position; const map = new Map();
  for (let i = 0; i < p.count; i++) {
    const k = [p.getX(i), p.getY(i), p.getZ(i)].map(v => v.toFixed(4)).join();
    if (!map.has(k)) map.set(k, [(r() - .5) * amt, (r() - .5) * amt, (r() - .5) * amt]);
    const d = map.get(k); p.setXYZ(i, p.getX(i) + d[0], p.getY(i) + d[1], p.getZ(i) + d[2]);
  }
  return geo;
}
// box with base centred at (x,y,z)
function box(w, h, d, color, x = 0, y = 0, z = 0) { return mesh(new THREE.BoxGeometry(w, h, d), color, x, y + h / 2, z); }
function cyl(rt, rb, h, seg, color, x = 0, y = 0, z = 0) { return mesh(new THREE.CylinderGeometry(rt, rb, h, seg), color, x, y + h / 2, z); }
function cone(r, h, seg, color, x = 0, y = 0, z = 0) { return cyl(0.0001, r, h, seg, color, x, y, z); }
// gable roof along X: footprint w (x) by d (z), ridge height h, eaves at y
function gable(w, d, h, color, x = 0, y = 0, z = 0) {
  const a = w / 2, b = d / 2;
  const v = [[-a, 0, -b], [a, 0, -b], [a, 0, b], [-a, 0, b], [-a, h, 0], [a, h, 0]];
  const pos = [];
  const tris = [[0, 5, 1], [0, 4, 5], [3, 2, 5], [3, 5, 4], [0, 3, 4], [1, 5, 2], [0, 1, 2], [0, 2, 3]];
  for (const f of tris) for (const i of f) pos.push(...v[i]);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  const m = mesh(g, color, x, y, z); m.material = M(color).clone(); m.material.side = THREE.DoubleSide; return m;
}
function grp(...c) { const g = new THREE.Group(); c.forEach(o => g.add(o)); return g; }

// ---------- renderer ----------
let renderer, scene, cam, sun, hemi, shadowPlane;
function setup() {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true, premultipliedAlpha: false });
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setClearColor(0x000000, 0);
  renderer.localClippingEnabled = true;
}
function lights(scn, fw, fh, shadows) {
  const cx = fw / 2, cz = fh / 2;
  hemi = new THREE.HemisphereLight(0xdcecff, 0xf3e2cf, 1.55); scn.add(hemi);
  sun = new THREE.DirectionalLight(0xfff0d8, 2.7);
  const L = new THREE.Vector3(-1, 1.55, 1).normalize();
  sun.position.set(cx + L.x * 12, L.y * 12, cz + L.z * 12); sun.target.position.set(cx, 0, cz);
  sun.castShadow = shadows;
  const e = Math.max(fw, fh) * 1.6 + 3.5;
  Object.assign(sun.shadow.camera, { left: -e, right: e, top: e, bottom: -e, near: 1, far: 30 });
  sun.shadow.mapSize.set(2048, 2048); sun.shadow.radius = 5; sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
  scn.add(sun, sun.target);
  if (shadows) {
    const p = new THREE.Mesh(new THREE.PlaneGeometry(fw + 8, fh + 8), new THREE.ShadowMaterial({ color: 0x3b3a78, opacity: 0.30 }));
    p.rotation.x = -Math.PI / 2; p.position.set(cx, 0.002, cz); p.receiveShadow = true; scn.add(p);
  }
}
// render scene so that world point (px,0,pz) lands on pixel (ax,ay) of a W x H canvas
function shoot(scn, W, H, ax, ay, P) {
  const cvs = renderer.domElement; renderer.setPixelRatio(1); renderer.setSize(W * SS, H * SS, false);
  const c = new THREE.OrthographicCamera(-ax / S, (W - ax) / S, ay / S, -(H - ay) / S, 0.1, 100);
  const d = 30, h = Math.cos(PITCH) / Math.SQRT2;
  c.position.set(P.x + d * h, P.y + d * Math.sin(PITCH), P.z + d * h); c.lookAt(P);
  c.updateProjectionMatrix();
  renderer.render(scn, c);
  const out = document.createElement('canvas'); out.width = W; out.height = H;
  const x = out.getContext('2d'); x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high';
  x.drawImage(cvs, 0, 0, W, H); return out;
}
function bbox(cvs, b) {
  const W = cvs.width, H = cvs.height, d = cvs.getContext('2d').getImageData(0, 0, W, H).data;
  let { x0, y0, x1, y1 } = b;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (d[(y * W + x) * 4 + 3] > 6) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  return { x0, y0, x1, y1 };
}
function cropTo(cvs, b) {
  const o = document.createElement('canvas'); o.width = b.x1 - b.x0 + 1; o.height = b.y1 - b.y0 + 1;
  o.getContext('2d').drawImage(cvs, -b.x0, -b.y0); return o.toDataURL();
}

// render an object model. fw,fh footprint; lift: sits on land (raised by LAND_H)
function renderObject(build, fw, fh, opts = {}) {
  const scn = new THREE.Scene();
  lights(scn, fw, fh, !opts.noShadow);
  const g = build(); g.position.set(fw / 2, 0, fh / 2); scn.add(g);
  if (opts.clipY) { g.traverse(o => { if (o.material) { o.material = o.material.clone(); o.material.clippingPlanes = [new THREE.Plane(new THREE.Vector3(0, 1, 0), 0.0)]; } }); }
  const W = Math.round(fw * 128 + 160), H = Math.round(opts.tall ? 520 : 360) + fh * 64;
  const ax = Math.round(fw * 64 + 80 + (fh - 1) * 0), ay = H - 70; // generous canvas, trimmed later
  // south corner of footprint (fw,0,fh) maps to (ax,ay)
  const cvs = shoot(scn, W, H, ax, ay, new THREE.Vector3(fw, 0, fh));
  return { cvs, ax, ay };
}

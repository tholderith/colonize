// ---------- palette (soft saturated pastels) ----------
const P = {
  deep: 0x4f86c6, deep2: 0x4b82c2, shallow: 0x6fc3d8, shallow2: 0x76c8db, foam: 0xeafcff,
  sand: 0xf0dca4, sandSide: 0xd9b985, grass: 0x9bd477, grass2: 0x8fcc6e, grassSide: 0x9a7a5a, road: 0xdcc59a, road2: 0xcdb386,
  wood: 0xb98a5b, woodDk: 0x8f6540, woodLt: 0xd6aa73, plank: 0xcfa271,
  wallCream: 0xf7ead0, wallPeach: 0xf6cfb0, wallBlue: 0xcfe0f2, wallMint: 0xd2ecd6, wallWhite: 0xf6f1e6,
  roofRed: 0xe0735e, roofBlue: 0x6f8fc9, roofMustard: 0xe7b84f, roofTeal: 0x58a9a0, roofSlate: 0x7a86b8,
  stone: 0xc9c6d6, stoneDk: 0xa4a1b8, door: 0x8a5a4a, glass: 0x8fc4ea,
  leaf1: 0x6fc27a, leaf2: 0x86d17f, leaf3: 0x5db38a, pine: 0x4aa77a, trunk: 0x9c6f4c,
  sailW: 0xfaf4e4, sailS: 0xe27a68, hull: 0x9a6a4b, hullLt: 0xc48f63, hullStripe: 0xf4e3b8,
  gold: 0xf2c94c, wheat: 0xeccb5f, wheat2: 0xdcb44a, soil: 0xb08a5e,
};

// ---------- terrain ----------
function terrainTile(kind, variant) {
  const scn = new THREE.Scene(); lights(scn, 1, 1, false);
  const r = rng(kind.length * 977 + variant * 131 + 7);
  const land = ['sand', 'grass', 'road'].includes(kind);
  const base = { deep_water: [P.deep, P.deep2], shallow_water: [P.shallow, P.shallow2], sand: [P.sand, 0xebd49a], grass: [P.grass, P.grass2], road: [P.road, P.road2] }[kind];
  const y0 = land ? LAND_H : 0, o = 0.03, o2 = 0.0105; // overscan so adjacent tiles never leave hairline seams
  const ct = new THREE.Vector3(0.5 + (r() - .5) * 0.25, y0 + (land ? 0.014 : 0.008) * (r() > .5 ? 1 : 0.4) * (kind === 'road' ? 0.3 : 1), 0.5 + (r() - .5) * 0.25);
  const corners = [[-o, -o], [1 + o, -o], [1 + o, 1 + o], [-o, 1 + o]];
  const mids = corners.map((c, i) => { const n = corners[(i + 1) % 4]; return [(c[0] + n[0]) / 2, (c[1] + n[1]) / 2]; });
  // 8 fan triangles around the (slightly displaced) centre: corner, mid, centre ...
  const ring = []; for (let i = 0; i < 4; i++) { ring.push(corners[i]); ring.push(mids[i]); }
  const pos = [], col = [];
  for (let i = 0; i < 8; i++) {
    const a = ring[i], b = ring[(i + 1) % 8];
    pos.push(a[0], y0, a[1], ct.x, ct.y, ct.z, b[0], y0, b[1]);
    const c = C(base[(i + variant) % 2 === 0 ? 0 : 1]); const j = 1 + (r() - .5) * (land ? 0.035 : 0.018); c.multiplyScalar(j);
    for (let k = 0; k < 3; k++) col.push(c.r, c.g, c.b);
  }
  // little decorative facets
  const deco = [];
  const addTri = (x, z, s, color, h = 0.012) => deco.push([x, z, s, color, h]);
  if (kind === 'grass') { for (let i = 0; i < 3 + variant; i++) addTri(0.2 + r() * .6, 0.2 + r() * .6, 0.05 + r() * .05, [0x7fc363, 0xaee28a, 0xf6e27a, 0xf3a9b4][i === 0 && variant === 2 ? 2 : (r() * 2) | 0], 0.02); }
  if (kind === 'road') { for (let i = 0; i < 6; i++) addTri(0.15 + r() * .7, 0.15 + r() * .7, 0.05 + r() * .04, [0xbfa578, 0xe9d8b2, 0xc7ae82][(r() * 3) | 0], 0.01); }
  if (kind === 'sand') { for (let i = 0; i < 3; i++) addTri(0.2 + r() * .6, 0.2 + r() * .6, 0.04 + r() * .04, [0xf8e8bd, 0xdcc084][(r() * 2) | 0], 0.008); }
  if (kind.endsWith('water') && variant > 0) { for (let i = 0; i < 2; i++) { const x = 0.25 + r() * .5, z = 0.25 + r() * .5; deco.push([x, z, 0.09 + r() * .05, kind === 'deep_water' ? 0x6ea2dc : 0xa4e4ee, 0.004, true]); } }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true })); m.receiveShadow = false; scn.add(m);
  for (const [x, z, s, color, h, wide] of deco) {
    const dg = new THREE.BufferGeometry();
    const pts = wide ? [[x - s * 1.6, z + s * .3], [x + s * 1.6, z - s * .3], [x, z + s * .9]] : [[x - s, z + s * .6], [x + s, z + s * .6], [x, z - s]];
    const pp = []; pts.forEach(p => pp.push(p[0], y0 + h * 0.2, p[1])); pp.push(x, y0 + h, z + 0.0);
    const idx = [0, 1, 3, 1, 2, 3, 2, 0, 3];
    const arr = []; idx.forEach(i => arr.push(pp[i * 3], pp[i * 3 + 1], pp[i * 3 + 2]));
    dg.setAttribute('position', new THREE.Float32BufferAttribute(arr, 3)); dg.computeVertexNormals();
    scn.add(new THREE.Mesh(dg, new THREE.MeshLambertMaterial({ color, flatShading: true, side: THREE.DoubleSide })));
  }
  if (land) { // earth/cliff sides (only visible where land meets water)
    const sideCol = kind === 'sand' ? P.sandSide : P.grassSide;
    const s1 = new THREE.Mesh(new THREE.BoxGeometry(1 + 2 * o2, y0, 1 + 2 * o2), M(kind === 'road' ? P.grassSide : sideCol)); s1.position.set(0.5, y0 / 2 - 0.0008, 0.5); scn.add(s1);
  }
  const W = 128, H = 64 + 10 + 2, ax = 64, ay = 64 + 10 + 1; // south corner at (1,0,1)
  const cvs = shoot(scn, W, H, ax, ay, new THREE.Vector3(1, 0, 1));
  return { url: cvs.toDataURL(), anchor: [ax, ay], size: [W, H] };
}

// ---------- vegetation / props ----------
function tree(v) {
  const g = new THREE.Group();
  if (v === 0) { // conifer
    g.add(cyl(0.05, 0.07, 0.25, 5, P.trunk, 0, 0, 0));
    [[0.34, 0.38, 0.18], [0.27, 0.34, 0.45], [0.19, 0.3, 0.7]].forEach(([r, h, y], i) => g.add(mesh(jitter(new THREE.ConeGeometry(r, h, 6), 0.03, 11 + i), i % 2 ? P.pine : 0x57b585, 0, y + h / 2, 0)));
  } else if (v === 1) { // round broadleaf
    g.add(cyl(0.06, 0.085, 0.4, 5, P.trunk));
    g.add(mesh(jitter(new THREE.IcosahedronGeometry(0.33, 0), 0.05, 5), P.leaf1, 0, 0.62, 0));
    g.add(mesh(jitter(new THREE.IcosahedronGeometry(0.2, 0), 0.04, 6), P.leaf2, 0.14, 0.82, -0.05));
  } else { // tall poplar-ish / two-blob
    g.add(cyl(0.05, 0.075, 0.45, 5, P.trunk));
    g.add(mesh(jitter(new THREE.IcosahedronGeometry(0.26, 0), 0.04, 8), P.leaf3, -0.06, 0.62, 0.03));
    g.add(mesh(jitter(new THREE.IcosahedronGeometry(0.22, 0), 0.04, 9), P.leaf2, 0.06, 0.9, -0.03));
    g.add(mesh(jitter(new THREE.IcosahedronGeometry(0.14, 0), 0.03, 4), P.leaf1, 0.0, 1.1, 0));
  }
  return g;
}
function rock() {
  const g = new THREE.Group();
  const a = mesh(jitter(new THREE.IcosahedronGeometry(0.26, 0), 0.08, 3), P.stone, 0, 0.14, 0); a.scale.set(1.2, 0.8, 1);
  const b = mesh(jitter(new THREE.IcosahedronGeometry(0.16, 0), 0.06, 4), P.stoneDk, 0.26, 0.09, 0.12);
  const c = mesh(jitter(new THREE.IcosahedronGeometry(0.1, 0), 0.04, 5), 0xdcdae8, -0.2, 0.07, 0.2);
  g.add(a, b, c); return g;
}
function windowsFor(g, w, d, y, color, onX, onZ, n = 1) {
  // windows on +x face and +z face (the ones the camera sees)
  if (onX) for (let i = 0; i < n; i++) g.add(box(0.012, 0.13, 0.11, color, w / 2 + 0.002, y, (i - (n - 1) / 2) * 0.26 * d));
  if (onZ) for (let i = 0; i < n; i++) g.add(box(0.11, 0.13, 0.012, color, (i - (n - 1) / 2) * 0.3 * w, y, d / 2 + 0.002));
}
function house(v) {
  const g = new THREE.Group();
  const walls = [P.wallCream, P.wallPeach, P.wallBlue][v], roofs = [P.roofRed, P.roofBlue, P.roofMustard][v];
  const w = [0.62, 0.56, 0.66][v], d = [0.5, 0.58, 0.46][v], h = [0.36, 0.42, 0.34][v];
  g.add(box(w, h, d, walls, 0, 0, 0));
  g.add(box(w + 0.03, 0.04, d + 0.03, P.woodLt, 0, 0, 0)); // plinth
  const rg = gable(w + 0.14, d + 0.14, 0.3 + 0.04 * v, roofs, 0, h, 0); if (v === 1) rg.rotation.y = Math.PI / 2; g.add(rg);
  if (v !== 1) g.add(box(0.1, 0.22, 0.1, P.stoneDk, -w * 0.25, h + 0.1, d * 0.1));
  else g.add(box(0.1, 0.22, 0.1, P.stoneDk, w * 0.05, h + 0.14, -d * 0.25));
  g.add(box(0.1, 0.19, 0.012, P.door, v === 0 ? 0.12 : -0.1, 0.03, d / 2 + 0.002));
  g.add(box(0.1, 0.12, 0.012, P.glass, v === 0 ? -0.18 : 0.15, 0.17, d / 2 + 0.002));
  g.add(box(0.012, 0.12, 0.1, P.glass, w / 2 + 0.002, 0.17, 0.05));
  g.add(box(0.012, 0.12, 0.1, P.glass, w / 2 + 0.002, 0.17, -0.14));
  if (v === 2) g.add(box(0.18, 0.1, 0.1, 0xb4e0a0, 0.2, 0, d / 2 + 0.07)); // flower box / hedge
  return g;
}
function farmhouse() {
  const g = new THREE.Group();
  g.add(box(0.74, 0.4, 0.5, 0xf2c6a4, 0, 0, 0.05));
  g.add(gable(0.88, 0.64, 0.34, P.roofRed, 0, 0.4, 0.05));
  g.add(box(0.1, 0.2, 0.1, P.stoneDk, 0.22, 0.58, 0.1));
  g.add(box(0.12, 0.2, 0.012, P.door, -0.18, 0.03, 0.31)); g.add(box(0.12, 0.13, 0.012, P.glass, 0.12, 0.2, 0.31));
  g.add(box(0.012, 0.13, 0.12, P.glass, 0.371, 0.2, 0.05));
  // silo
  g.add(cyl(0.13, 0.13, 0.55, 8, 0xe6e0d8, -0.3, 0, -0.32)); g.add(cone(0.15, 0.17, 8, P.roofSlate, -0.3, 0.55, -0.32));
  // hay bale + fence
  g.add(box(0.14, 0.1, 0.1, P.wheat, 0.33, 0, -0.32));
  for (let i = 0; i < 4; i++) g.add(box(0.025, 0.12, 0.025, P.woodDk, -0.25 + i * 0.2, 0, 0.42));
  g.add(box(0.62, 0.025, 0.02, P.woodLt, 0.05, 0.08, 0.42));
  return g;
}
function windmill() {
  const g = new THREE.Group();
  g.add(cyl(0.2, 0.3, 0.2, 8, P.stone));
  g.add(mesh(new THREE.CylinderGeometry(0.17, 0.27, 0.75, 8), P.wallWhite, 0, 0.62, 0));
  g.add(cyl(0.2, 0.22, 0.05, 8, P.woodDk, 0, 0.98, 0));
  g.add(cone(0.26, 0.28, 8, P.roofRed, 0, 1.0, 0));
  g.add(box(0.12, 0.2, 0.012, P.door, 0.0, 0.2, 0.3).rotateY(0));
  const hub = new THREE.Group(); hub.position.set(0, 0.88, 0);
  hub.rotation.y = Math.PI / 4; // face camera diagonal (+x,+z)
  const axle = box(0.07, 0.07, 0.3, P.woodDk, 0, -0.035, 0.18); hub.add(axle);
  const blades = new THREE.Group(); blades.position.set(0, 0, 0.36); blades.rotation.z = 0.35;
  for (let i = 0; i < 4; i++) {
    const arm = new THREE.Group(); arm.rotation.z = i * Math.PI / 2;
    arm.add(box(0.05, 0.84, 0.03, P.woodDk, 0, 0, 0).translateY(0.0));
    arm.children[0].position.set(0, 0.42, 0);
    const sail = box(0.2, 0.55, 0.012, P.sailW, 0.1, 0.25, 0.02); const bar = box(0.2, 0.05, 0.014, P.sailS, 0.1, 0.78, 0.02);
    arm.add(sail); arm.add(bar); blades.add(arm);
  }
  hub.add(blades); g.add(hub);
  return sailify(g);
}
function lumberjack() {
  const g = new THREE.Group();
  g.add(box(0.5, 0.28, 0.42, 0xc99a68, -0.12, 0, -0.1));
  g.add(gable(0.62, 0.54, 0.26, P.roofTeal, -0.12, 0.28, -0.1));
  g.add(box(0.1, 0.17, 0.012, P.door, -0.2, 0.02, 0.112));
  g.add(box(0.012, 0.1, 0.1, P.glass, 0.139, 0.12, -0.1));
  // log pile
  for (let r = 0; r < 3; r++) for (let i = 0; i < 3 - r; i++) {
    const l = cyl(0.05, 0.05, 0.3, 7, r % 2 ? P.woodLt : P.wood, 0.18 + i * 0.1 + r * 0.05, 0.05 + r * 0.085, 0.3); l.rotation.z = Math.PI / 2; l.rotation.set(Math.PI / 2, 0, 0); l.position.set(-0.05 + i * 0.1 + r * 0.05, 0.05 + r * 0.085, 0.3); g.add(l);
  }
  // chopping block + axe
  g.add(cyl(0.08, 0.09, 0.12, 7, P.wood, 0.3, 0, 0.0)); g.add(box(0.02, 0.15, 0.02, P.woodDk, 0.3, 0.12, 0.0)); g.add(box(0.07, 0.04, 0.015, P.stoneDk, 0.32, 0.23, 0));
  // stacked planks / stump
  g.add(box(0.2, 0.05, 0.12, P.plank, 0.25, 0, -0.3)); g.add(box(0.2, 0.05, 0.12, P.woodLt, 0.25, 0.05, -0.3));
  return g;
}
function chapel() { // 2x2, centred
  const g = new THREE.Group();
  g.add(box(1.0, 0.1, 1.6, P.stone, 0, 0, 0.0).translateX(0));
  g.add(box(0.84, 0.5, 1.4, P.wallWhite, 0, 0.1, 0.0));
  g.add(gable(1.02, 1.56, 0.4, P.roofBlue, 0, 0.6, 0).rotateY(Math.PI / 2));
  // tower at +z end? tower front
  g.add(box(0.5, 0.95, 0.5, P.wallCream, 0, 0.1, -0.62));
  g.add(box(0.56, 0.06, 0.56, P.stoneDk, 0, 1.05, -0.62));
  const sp = mesh(new THREE.ConeGeometry(0.34, 0.6, 4), P.roofRed, 0, 1.4, -0.62); sp.rotation.y = Math.PI / 4; g.add(sp);
  g.add(box(0.03, 0.2, 0.03, P.gold, 0, 1.7, -0.62)); g.add(box(0.12, 0.03, 0.03, P.gold, 0, 1.82, -0.62));
  // bell opening
  g.add(box(0.14, 0.2, 0.012, 0x6a6fa0, 0, 0.78, -0.62 + 0.256)); g.add(box(0.012, 0.2, 0.14, 0x6a6fa0, 0.256, 0.78, -0.62));
  // windows + door (visible faces +x and +z)
  for (let i = 0; i < 3; i++) g.add(box(0.012, 0.25, 0.1, P.glass, 0.422, 0.28, -0.1 + i * 0.35));
  g.add(box(0.2, 0.3, 0.012, P.door, 0, 0.1, 0.702)); g.add(mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.012, 8, 1, false, 0, Math.PI), P.door, 0, 0.4, 0.702).rotateX(Math.PI / 2));
  g.add(box(0.1, 0.1, 0.012, P.glass, 0, 0.5, 0.702));
  // fenced yard bits
  [[-.55, .62], [.55, .62]].forEach(([x, z]) => { g.add(cyl(0.03, 0.03, 0.14, 5, P.woodDk, x, 0, z)); });
  g.add(box(0.5, 0.04, 0.5, 0xb8e2a0, 0.0, 0, 0.92).translateY(0)); // lawn patch
  return g;
}
function warehouse() { // 2x2
  const g = new THREE.Group();
  g.add(box(1.3, 0.06, 0.95, P.stoneDk, -0.05, 0, -0.1));
  g.add(box(1.2, 0.46, 0.8, 0xe3b98a, -0.05, 0.06, -0.1));
  // plank lines
  for (let i = 0; i < 7; i++) g.add(box(0.012, 0.44, 0.012, P.woodDk, -0.6 + 0.09 + i * 0.17, 0.07, 0.302 - 0.1 + 0.002));
  g.add(gable(1.36, 1.0, 0.42, P.roofTeal, -0.05, 0.52, -0.1));
  g.add(box(0.3, 0.32, 0.012, P.woodDk, 0.0, 0.06, 0.302)); // big door
  g.add(box(0.012, 0.15, 0.12, P.glass, 0.552, 0.3, -0.2)); g.add(box(0.012, 0.15, 0.12, P.glass, 0.552, 0.3, 0.1));
  // loft crane arm
  g.add(box(0.04, 0.3, 0.04, P.woodDk, 0.38, 0.52, 0.32)); g.add(box(0.3, 0.035, 0.035, P.woodDk, 0.5, 0.78, 0.32).translateX(-0.12));
  // crates & barrels
  g.add(box(0.2, 0.2, 0.2, P.woodLt, 0.4, 0, 0.55)); g.add(box(0.16, 0.16, 0.16, P.wood, 0.58, 0, 0.45)); g.add(box(0.15, 0.15, 0.15, P.plank, 0.44, 0.2, 0.55));
  g.add(cyl(0.08, 0.08, 0.18, 8, 0xa0714a, -0.5, 0, 0.58)); g.add(cyl(0.08, 0.08, 0.18, 8, 0xa0714a, -0.34, 0, 0.62)); g.add(cyl(0.08, 0.08, 0.18, 8, 0xb88259, -0.42, 0.18, 0.6).translateX(0));
  g.add(box(0.2, 0.16, 0.16, 0xe8c76a, 0.75, 0, 0.1)); // sack bale
  g.add(box(0.6, 0.012, 0.08, P.sailS, 0.0, 0.42, 0.302 + 0.002));
  return g;
}
function sailify(g) { g.traverse(o => { if (o.isMesh && (o.material.color.getHex() === P.sailW)) { o.material = o.material.clone(); o.material.emissive = C(0x5a5448); } }); return g; }
function wheat() { // 2x2 flat, ground-level crops
  const g = new THREE.Group();
  const soil = box(1.9, 0.03, 1.9, P.soil, 0, 0, 0); g.add(soil);
  const r = rng(21);
  for (let i = 0; i < 9; i++) for (let j = 0; j < 12; j++) {
    const z = -0.82 + i * 0.205, x = -0.9 + j * 0.16 + (i % 2) * 0.04;
    if (r() < 0.06) continue;
    const c = (i % 2 ? P.wheat : P.wheat2);
    const h = 0.11 + r() * 0.05; const m = mesh(new THREE.ConeGeometry(0.075, h, 4), c, x, 0.03 + h / 2, z); m.rotation.y = r() * 3; g.add(m);
  }
  [[-0.95, 0.96], [0.96, -0.95]].forEach(() => {});
  return g;
}
function pier() { // 1x1 flat, deck along +x from shore, on water
  const g = new THREE.Group();
  const deckY = LAND_H + 0.01;
  g.add(box(1.0, 0.04, 0.36, P.plank, 0, deckY - 0.04, 0));
  for (let i = 0; i < 6; i++) g.add(box(0.12, 0.03, 0.37, i % 2 ? P.woodLt : P.wood, -0.45 + i * 0.18, deckY - 0.005, 0));
  [[-0.45, -0.17], [-0.45, 0.17], [0.0, -0.17], [0.0, 0.17], [0.45, -0.17], [0.45, 0.17]].forEach(([x, z]) => g.add(cyl(0.032, 0.036, deckY + 0.2, 6, P.woodDk, x, -0.2, z)));
  g.add(box(0.045, 0.1, 0.045, P.woodDk, 0.46, deckY, 0.18)); g.add(box(0.045, 0.1, 0.045, P.woodDk, 0.46, deckY, -0.18));
  g.add(cyl(0.05, 0.05, 0.1, 8, P.woodDk, 0.3, deckY, 0.0)); // bollard
  const foam = new THREE.Mesh(new THREE.PlaneGeometry(1.15, 0.5), new THREE.MeshBasicMaterial({ color: P.foam, transparent: true, opacity: 0.35 })); foam.rotation.x = -Math.PI / 2; foam.position.y = 0.01; g.add(foam);
  return g;
}
function ship() { // 2x2, along +x
  const g = new THREE.Group();
  const secs = []; // x, halfwidth@deck, keel depth
  const N = 9;
  for (let i = 0; i < N; i++) { const t = i / (N - 1) * 2 - 1; const hw = 0.3 * Math.pow(Math.max(0, 1 - Math.pow(Math.max(t, 0), 2.4)), 0.7) * (1 - 0.35 * Math.max(0, -t - 0.5) * 2) + 0.012; secs.push({ x: t * 0.95, hw, ty: 0.42 + 0.1 * Math.max(0, -t) * Math.max(0, -t - 0.2) * 3 + 0.11 * Math.max(0, t - 0.6) }); }
  // hull: each section = 5 points (deck port, mid port, keel, mid stbd, deck stbd)
  const sec = s => [[s.x, s.ty, -s.hw], [s.x, 0.12, -s.hw * 0.88], [s.x, -0.2, 0], [s.x, 0.12, s.hw * 0.88], [s.x, s.ty, s.hw]];
  const pos = []; const cols = [];
  const tri = (a, b, c, col) => { pos.push(...a, ...b, ...c); const cc = C(col); for (let k = 0; k < 3; k++) cols.push(cc.r, cc.g, cc.b); };
  for (let i = 0; i < N - 1; i++) {
    const A = sec(secs[i]), B = sec(secs[i + 1]);
    for (let j = 0; j < 4; j++) {
      const col = j === 0 || j === 3 ? (i % 4 < 2 ? P.hullStripe : P.hullLt) : P.hull;
      const cj = (j === 0 || j === 3) ? (i % 2 ? P.hullLt : P.hullStripe) : (j === 1 || j === 2 ? P.hull : P.hull);
      tri(A[j], A[j + 1], B[j], cj); tri(A[j + 1], B[j + 1], B[j], cj);
    }
  }
  // bow & stern caps
  const fb = sec(secs[N - 1]); const bowTip = [secs[N - 1].x + 0.18, secs[N - 1].ty + 0.08, 0];
  for (let j = 0; j < 4; j++) tri(fb[j], fb[j + 1], [secs[N - 1].x + 0.02, 0.1, 0], P.hullLt);
  const sb = sec(secs[0]); for (let j = 0; j < 4; j++) tri(sb[j + 1], sb[j], [secs[0].x - 0.03, 0.3, 0], P.hull);
  const hg = new THREE.BufferGeometry(); hg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); hg.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3)); hg.computeVertexNormals();
  const hm = new THREE.Mesh(hg, new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, side: THREE.DoubleSide })); hm.castShadow = true; hm.receiveShadow = true; g.add(hm);
  // deck
  const dk = []; for (let i = 0; i < N; i++) dk.push(secs[i]);
  const dpos = []; for (let i = 0; i < N - 1; i++) { const a = secs[i], b = secs[i + 1]; const ya = a.ty - 0.02, yb = b.ty - 0.02; dpos.push(a.x, ya, -a.hw, b.x, yb, -b.hw, b.x, yb, b.hw, a.x, ya, -a.hw, b.x, yb, b.hw, a.x, ya, a.hw); }
  const dg = new THREE.BufferGeometry(); dg.setAttribute('position', new THREE.Float32BufferAttribute(dpos, 3)); dg.computeVertexNormals();
  const dm = new THREE.Mesh(dg, new THREE.MeshLambertMaterial({ color: P.woodLt, side: THREE.DoubleSide })); dm.receiveShadow = true; g.add(dm);
  // bowsprit, castle
  g.add(box(0.5, 0.045, 0.045, P.woodDk, 1.0, 0.43, 0).rotateZ(0)); g.children[g.children.length - 1].rotation.z = 0.18; g.children[g.children.length - 1].position.set(1.12, 0.55, 0);
  g.add(box(0.34, 0.14, 0.44, P.hullLt, -0.72, 0.5, 0)); g.add(box(0.36, 0.03, 0.46, P.hull, -0.72, 0.64, 0));
  g.add(box(0.012, 0.07, 0.07, P.glass, -0.55, 0.55, 0.12)); g.add(box(0.012, 0.07, 0.07, P.glass, -0.55, 0.55, -0.12));
  // masts & sails
  const masts = [[-0.45, 1.35, 0.52, 0.34], [0.1, 1.6, 0.62, 0.4], [0.62, 1.25, 0.46, 0.3]];
  masts.forEach(([x, h, sw, sh], k) => {
    g.add(cyl(0.025, 0.035, h, 6, P.woodDk, x, 0.4, 0));
    g.add(box(0.03, 0.03, sw + 0.12, P.woodDk, x, 0.4 + h * 0.62, 0));
    const sailH = h * 0.5; const s1 = box(0.035, sailH, sw, P.sailW, x + 0.02, 0.4 + h * 0.12, 0); s1.geometry; g.add(s1);
    g.add(box(0.045, 0.05, sw * 0.98, P.sailS, x + 0.025, 0.4 + h * 0.12 + sailH * 0.42, 0));
    const top = box(0.03, h * 0.2, sw * 0.7, P.sailW, x + 0.02, 0.4 + h * 0.67, 0); g.add(top);
  });
  // pennant
  const pen = box(0.01, 0.07, 0.2, P.sailS, 0.1, 2.0 + 0.0, -0.1); pen.position.set(0.1, 1.95, -0.1); g.add(pen);
  return sailify(g);
}
function cart() {
  const g = new THREE.Group();
  g.add(box(0.3, 0.06, 0.2, P.wood, 0.0, 0.12, 0));
  g.add(box(0.3, 0.1, 0.02, P.woodLt, 0.0, 0.16, 0.1)); g.add(box(0.3, 0.1, 0.02, P.woodLt, 0.0, 0.16, -0.1)); g.add(box(0.02, 0.1, 0.2, P.woodLt, -0.15, 0.16, 0));
  g.add(box(0.2, 0.09, 0.14, P.wheat, 0.0, 0.2, 0));
  for (const z of [-0.12, 0.12]) { const w = cyl(0.09, 0.09, 0.025, 8, P.woodDk, 0, 0, z); w.rotation.x = Math.PI / 2; w.position.set(0, 0.09, z); g.add(w); }
  // ox
  const ox = new THREE.Group(); ox.position.set(0.34, 0, 0);
  ox.add(box(0.2, 0.13, 0.12, 0xb98a6c, 0, 0.1, 0)); ox.add(box(0.1, 0.1, 0.1, 0xa87a5e, 0.14, 0.18, 0));
  [[-.06, -.04], [-.06, .04], [.07, -.04], [.07, .04]].forEach(([x, z]) => ox.add(box(0.03, 0.1, 0.03, 0x8c6249, x, 0, z)));
  ox.add(box(0.02, 0.05, 0.02, 0xf4ecd8, 0.17, 0.27, 0.05)); ox.add(box(0.02, 0.05, 0.02, 0xf4ecd8, 0.17, 0.27, -0.05));
  g.add(ox); g.add(box(0.14, 0.02, 0.02, P.woodDk, 0.2, 0.15, 0));
  g.rotation.y = 0; return g;
}
function colonist() {
  const g = new THREE.Group();
  g.add(box(0.05, 0.1, 0.05, 0x4e5a8a, -0.03, 0, 0)); g.add(box(0.05, 0.1, 0.05, 0x4e5a8a, 0.03, 0, 0));
  g.add(mesh(new THREE.CylinderGeometry(0.06, 0.08, 0.2, 6), 0xe0735e, 0, 0.1 + 0.1, 0));
  g.add(mesh(new THREE.IcosahedronGeometry(0.052, 0), 0xf5cfb0, 0, 0.36, 0));
  g.add(cyl(0.03, 0.075, 0.035, 6, 0x7a86b8, 0, 0.37, 0)); g.add(cyl(0.001, 0.045, 0.06, 6, 0x7a86b8, 0, 0.395, 0));
  g.add(box(0.03, 0.12, 0.03, 0xe0735e, 0.075, 0.14, 0));
  return g;
}

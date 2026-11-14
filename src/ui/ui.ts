import { BUILDINGS, ECON, GOODS, TRADE, affordError, buildingDef } from '../sim/placement';
import type { Building, BuildingDef, GameState, Order, Stock, Stop } from '../sim/types';
import { TradeUi } from './trade-ui';

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;

export interface UiEvents {
  onSpeed(speed: 0 | 1 | 2 | 3): void;
  onSelectTool(def: BuildingDef | null): void;
  onDemolish(b: Building): void;
  onBuildHauler(port: Building): void;
  onSetRoute(hauler: number, route: Stop[]): void;
  onScrapHauler(hauler: number): void;
  onTrade(): void;
  onExchangeOrder(good: string, mode: Order['mode'], amount: number): void;
  onSave(): void;
  onExport(): void;
  onLoad(): void;
}

const costText = (cost: Stock) =>
  Object.entries(cost)
    .map(([g, n]) => `${n}${g === 'credits' ? 'cr' : ' ' + g}`)
    .join(' ');
const goodName = (id: string) => GOODS.find((g) => g.id === id)?.name ?? id;
const flowText = (f: Stock | undefined) =>
  Object.entries(f ?? {})
    .map(([g, n]) => `${n} ${goodName(g).toLowerCase()}`)
    .join(' + ');

const perMin = (f: Stock, cycle: number) =>
  Object.entries(f)
    .map(([g, n]) => `${n} ${goodName(g).toLowerCase()}`)
    .join(' + ') + ` / ${Math.round(cycle / 10)}s`;

/** HUD card tooltip: what the resource is for and what makes / uses it (derived from the data files). */
function hudTip(k: string): string | null {
  if (k === 'island') return '<b>Island</b><br>The stock shown is for this island: the one selected, else under the camera. Move goods between islands with haulers.';
  if (k === 'pop') return '<b>Colonists</b><br>L = laborers (Pod House tier 1), T = technicians (tier 2). They pay tax, eat rations and staff buildings. Technicians also raise independence.';
  if (k === 'power') return '<b>Power</b><br>Demand / supply on this island. Wind turbines supply 10 each within their radius; short power halves production speed.';
  if (k === 'credits')
    return '<b>Credits</b> (shared by all islands)<br>Earned from colonist tax and trade. Spent on building. The Concordat takes a levy share of what you earn each period.<br><span class="k">Rate = net per minute.</span>';
  const g = GOODS.find((o) => o.id === k);
  if (!g) return null;
  const makers = BUILDINGS.filter((b) => b.outputs?.[k]).map((b) => b.name);
  const users = BUILDINGS.filter((b) => b.inputs?.[k] || b.upkeep?.[k]).map((b) => b.name);
  if (ECON.tiers.some((t) => t.needsPerResidentPerMin[k])) users.push('Pod Houses');
  const cost = BUILDINGS.filter((b) => b.cost[k]).length;
  return `<b>${g.name}</b> (this island)<br><span class="k">Made by:</span> ${makers.join(', ') || '-'}<br><span class="k">Used by:</span> ${users.join(', ') || '-'}${cost ? '<br><span class="k">Also a building cost.</span>' : ''}<br><span class="k">Rate = net per minute.</span>`;
}

function buildTip(id: string): string | null {
  const d = buildingDef(id);
  if (!d) return null;
  const lines = [`<b>${d.name}</b>`, d.desc ?? ''];
  if (d.cycle && d.outputs) lines.push(`<span class="k">In:</span> ${d.inputs ? perMin(d.inputs, d.cycle) : '-'}<br><span class="k">Out:</span> ${perMin(d.outputs, d.cycle)}`);
  if (d.draw) lines.push(`<span class="k">Power:</span> uses ${d.draw}`);
  if (d.supply) lines.push(`<span class="k">Power:</span> supplies ${d.supply}, radius ${d.radius}`);
  if (d.jobs) lines.push(`<span class="k">Jobs:</span> ${d.jobs} ${d.worker}s`);
  if (d.upkeep) lines.push(`<span class="k">Upkeep:</span> ${flowText(d.upkeep)} / min`);
  lines.push(`<span class="k">Cost:</span> ${costText(d.cost)} <span class="k">&middot; ${d.footprint[0]}x${d.footprint[1]}</span>`);
  return lines.filter(Boolean).join('<br>');
}

export class Ui {
  private tool: BuildingDef | null = null;
  private buttons = new Map<string, HTMLButtonElement>();
  readonly trade: TradeUi;
  /** Goods whose icon PNG (public/assets/ui/icons/<good>.png) loaded; the rest show a text tag. */
  private icons = new Set<string>();

  constructor(private events: UiEvents) {
    for (const g of GOODS) {
      const img = new Image();
      img.onload = () => this.icons.add(g.id);
      img.src = `${import.meta.env.BASE_URL}assets/ui/icons/${g.id}.png`;
    }
    this.trade = new TradeUi({
      onSetRoute: events.onSetRoute,
      onScrap: events.onScrapHauler,
      onTrade: events.onTrade,
      onExchangeOrder: events.onExchangeOrder,
      toast: (m, k) => this.toast(m, k),
    });
    document.querySelectorAll<HTMLButtonElement>('#topbar [data-speed]').forEach((btn) => {
      btn.addEventListener('click', () => events.onSpeed(Number(btn.dataset.speed) as 0 | 1 | 2 | 3));
    });
    $('btn-save').addEventListener('click', () => events.onSave());
    $('btn-export').addEventListener('click', () => events.onExport());
    const menu = $('build-menu');
    let group = '';
    for (const def of BUILDINGS) {
      if (def.group !== group) {
        group = def.group;
        const h = document.createElement('h3');
        h.textContent = group.toUpperCase();
        menu.appendChild(h);
      }
      const btn = document.createElement('button');
      btn.dataset.building = def.id;
      btn.innerHTML = `<span>${def.name}</span><span class="dim">${def.footprint[0]}x${def.footprint[1]} &middot; ${costText(def.cost)}</span>`;
      btn.addEventListener('click', () => this.setTool(this.tool?.id === def.id ? null : def));
      menu.appendChild(btn);
      this.buttons.set(def.id, btn);
    }
    $('btn-load').addEventListener('click', () => events.onLoad());
    this.initTooltips();
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.setTool(null);
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (e.ctrlKey || e.metaKey || e.altKey || tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
      if (e.key === ' ') {
        e.preventDefault();
        if (!e.repeat) events.onSpeed(0);
      } else if (e.key === '1' || e.key === '2' || e.key === '3') events.onSpeed(Number(e.key) as 1 | 2 | 3);
    });
    // A focused button would also "click" on Space; keep Space for pause only.
    window.addEventListener('keyup', (e) => {
      if (e.key === ' ') e.preventDefault();
    });
    window.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      this.setTool(null);
    });
  }

  /** Pulse these build-menu items (objective hints). */
  setHighlight(ids: string[]): void {
    for (const [id, btn] of this.buttons) btn.classList.toggle('hint', ids.includes(id));
  }

  /** In-page confirm box; `yes` runs on the confirm button. */
  confirm(text: string, yesLabel: string, yes: () => void): void {
    $('confirm-text').textContent = text;
    $('confirm-yes').textContent = yesLabel;
    const box = $('confirm');
    const close = () => {
      box.hidden = true;
      $('confirm-yes').onclick = $('confirm-no').onclick = null;
    };
    $('confirm-yes').onclick = () => (close(), yes());
    $('confirm-no').onclick = close;
    box.hidden = false;
  }

  closeConfirm(): void {
    $('confirm-no').click();
  }

  /** One floating tooltip for the HUD cards and build-menu items (the HUD is rebuilt every snapshot, so no title attributes). */
  private initTooltips(): void {
    const tip = $('tip');
    let key = '';
    const hide = () => ((tip.hidden = true), (key = ''));
    const bind = (root: HTMLElement, sel: string, html: (el: HTMLElement) => string | null) => {
      root.addEventListener('mousemove', (e) => {
        const el = (e.target as HTMLElement).closest<HTMLElement>(sel);
        const k = el ? (el.dataset.good ?? el.dataset.hud ?? el.dataset.building ?? '') : '';
        if (!el || !k) return hide();
        if (k !== key || tip.hidden) {
          const h = html(el);
          if (!h) return hide();
          key = k;
          tip.innerHTML = h;
          tip.hidden = false;
        }
        const w = tip.offsetWidth, hh = tip.offsetHeight;
        const x = e.clientX + 14 + w > window.innerWidth ? e.clientX - w - 14 : e.clientX + 14;
        tip.style.left = `${Math.max(4, x)}px`;
        tip.style.top = `${Math.max(4, Math.min(window.innerHeight - hh - 4, e.clientY + 16))}px`;
      });
      root.addEventListener('mouseleave', hide);
    };
    bind($('hud'), '[data-good], [data-hud]', (el) => hudTip(el.dataset.good ?? el.dataset.hud ?? ''));
    bind($('build-menu'), 'button[data-building]', (el) => buildTip(el.dataset.building ?? ''));
    window.addEventListener('keydown', hide);
  }

  get activeTool(): BuildingDef | null {
    return this.tool;
  }

  setTool(def: BuildingDef | null): void {
    this.tool = def;
    for (const [id, btn] of this.buttons) btn.classList.toggle('active', id === def?.id);
    this.setPlaceInfo(def, null);
    this.events.onSelectTool(def);
  }

  /** Default kind is a red warning; events pass 'info'. */
  toast(msg: string, kind: 'info' | 'bad' = 'bad'): void {
    const t = $('toast');
    const d = document.createElement('div');
    d.textContent = msg;
    d.className = kind;
    t.appendChild(d);
    while (t.children.length > 4) t.firstChild?.remove();
    window.setTimeout(() => d.remove(), kind === 'bad' ? 2200 : 4500);
  }

  /** Cost / radius / error line shown while placing. */
  setPlaceInfo(def: BuildingDef | null, error: string | null): void {
    const el = $('place-info');
    el.hidden = !def;
    if (!def) return;
    const extra = def.radius ? ` &middot; radius ${def.radius}` : '';
    el.innerHTML = `<b>${def.name}</b> &middot; cost ${costText(def.cost)}${extra}${error ? `<br><span class="warn">${error}</span>` : ''}`;
  }

  /** `island` is the island whose stock the HUD shows (selection, else camera centre). */
  setState(s: GameState, island: number): void {
    $('tick').textContent = String(s.tick);
    document.querySelectorAll<HTMLButtonElement>('#topbar [data-speed]').forEach((btn) => {
      const v = Number(btn.dataset.speed);
      btn.classList.toggle('active', v === 0 ? s.paused : !s.paused && v === s.speed);
    });
    const isl = s.islands[island] ?? (s.islands[0] as NonNullable<GameState['islands'][number]>);
    const rate = (r: number) => `<em class="${r > 0.05 ? 'pos' : r < -0.05 ? 'neg' : 'dim'}">${r >= 0 ? '+' : ''}${r.toFixed(0)}/m</em>`;
    const cap = ECON.storageCap * s.buildings.filter((b) => b.type === 'depot' && b.island === isl.id).length;
    const card = (attr: string, label: string, ic: string, value: string, extra: string, cls = '') =>
      `<span class="g card ${cls}" ${attr}><i class="ic">${ic}</i><span class="lab">${label}${extra}</span><b>${value}</b></span>`;
    const goods = GOODS.map((g) => {
      const credits = g.id === 'credits';
      const ic = this.icons.has(g.id) ? `<img src="${import.meta.env.BASE_URL}assets/ui/icons/${g.id}.png" alt="">` : `<span class="tag">${g.short}</span>`;
      return card(`data-good="${g.id}"`, g.name, ic, String(Math.floor(credits ? s.credits : (isl.stock[g.id] ?? 0))), rate(credits ? s.creditRate : (isl.rates[g.id] ?? 0)));
    }).join('');
    const p = s.pop;
    const pw = isl.power;
    $('hud').innerHTML =
      card('data-hud="island"', 'Island', '', isl.name, '', 'island') +
      goods +
      card('data-hud="pop"', 'Colonists', '', `${p.laborers + p.technicians}`, `<em class="dim">L${p.laborers} T${p.technicians}</em>`, 'pop') +
      card('data-hud="power"', 'Power', '', `${pw.demand}/${pw.supply}`, '', pw.demand > pw.supply ? 'bad' : 'power') +
      `<span class="g dim cap">cap ${cap}</span>`;
    this.trade.update(s);
    for (const [id, btn] of this.buttons) {
      const def = buildingDef(id);
      btn.classList.toggle('poor', !!def && affordError({ ...isl.stock, credits: s.credits }, def) !== null);
    }
  }

  /** Time-of-day clock in the top bar. */
  setTime(hour: number, day: number): void {
    const h = Math.floor(hour), m = Math.floor((hour - h) * 60);
    $('clock').textContent = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    $('day').textContent = String(day).padStart(3, '0');
    $('tod').className = hour >= 6.5 && hour < 18 ? 'day' : 'night';
  }

  /** Static part of the info panel (rebuilt only on selection change, so the button stays clickable). */
  showInfo(b: Building | null, state?: GameState): void {
    const body = $('info-body');
    const def = b && buildingDef(b.type);
    if (!b || !def) {
      body.className = 'dim';
      body.textContent = 'Nothing selected';
      return;
    }
    body.className = '';
    body.innerHTML = `<b>${def.name}</b> #${b.id} <span class="dim">at (${b.x}, ${b.y})</span><div id="info-dyn"></div>`;
    const btn = document.createElement('button');
    btn.id = 'btn-demolish';
    btn.textContent = 'DEMOLISH';
    btn.addEventListener('click', () => this.events.onDemolish(b));
    body.appendChild(btn);
    if (def.id === 'port') {
      const hb = document.createElement('button');
      hb.id = 'btn-build-hauler';
      hb.textContent = `BUILD HAULER (${costText(TRADE.hauler.cost)})`;
      hb.addEventListener('click', () => this.events.onBuildHauler(b));
      const tb = document.createElement('button');
      tb.id = 'btn-trade';
      tb.hidden = true;
      tb.addEventListener('click', () => this.events.onTrade());
      body.append(hb, tb);
    }
    if (state) this.updateInfo(b, state);
  }

  /** Live part of the info panel; call every snapshot. */
  updateInfo(b: Building, s: GameState): void {
    const def = buildingDef(b.type);
    const dyn = document.getElementById('info-dyn');
    if (!def || !dyn) return;
    const lines: string[] = [];
    if (def.house) {
      const t = ECON.tiers[b.tier - 1]!;
      lines.push(`Tier ${b.tier} &middot; ${b.residents}/${t.capacity} ${t.worker === 'laborer' ? 'Laborers' : 'Technicians'}`);
      for (const [k, ok] of Object.entries(b.needs)) lines.push(`${ok ? '<span class="pos">met</span>' : '<span class="neg">UNMET</span>'} ${k}`);
      lines.push(`Tax <b>${b.tax.toFixed(1)}</b> cr/min`);
    } else if (def.cycle) {
      const pct = Math.min(100, (b.progress / def.cycle) * 100);
      lines.push(`Status: <b class="${b.status === 'working' ? 'pos' : 'warn'}">${b.status}</b>`);
      lines.push(`Cycle <span class="bar"><i style="width:${pct}%"></i></span> ${pct.toFixed(0)}%`);
      lines.push(`Workers ${Math.round(b.staffed * (def.jobs ?? 0))}/${def.jobs} ${def.worker}s`);
      lines.push(`In: ${flowText(def.inputs) || '-'} &rarr; Out: ${flowText(def.outputs)}`);
    } else if (def.id === 'port') {
      const mine = s.haulers.filter((h) => h.home === b.island).length;
      lines.push(`Haulers from ${s.islands[b.island]?.name}: <b>${mine}</b>`);
      const tr = s.visitors.find((v) => v.kind === 'trader' && v.phase === 'dock' && v.target === b.id && v.offer && !v.offer.done);
      const tb = document.getElementById('btn-trade') as HTMLButtonElement | null;
      if (tb) tb.hidden = !tr?.offer;
      if (tr?.offer && tb) {
        const o = tr.offer;
        tb.textContent = `FREE TRADER ${o.side === 'buys' ? 'BUYS' : 'SELLS'} ${o.qty} ${o.good} @ ${o.price}`;
        lines.push('<span class="pos">Free trader docked</span>');
      }
    } else if (def.id === 'depot') {
      lines.push(`Radius ${def.radius} &middot; cap ${ECON.storageCap}/good`);
    } else if (def.supply) {
      lines.push(`Supplies ${def.supply} power &middot; radius ${def.radius} &middot; island ${s.islands[b.island]?.power.demand}/${s.islands[b.island]?.power.supply}`);
    } else {
      lines.push(`<span class="dim">${def.footprint[0]}x${def.footprint[1]} &middot; ${def.terrain.join(', ')}</span>`);
    }
    dyn.innerHTML = lines.join('<br>');
  }
}

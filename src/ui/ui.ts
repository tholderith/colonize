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
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.setTool(null);
    });
    window.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      this.setTool(null);
    });
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

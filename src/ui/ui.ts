import { BUILDINGS, ECON, GOODS, affordError, buildingDef } from '../sim/placement';
import type { Building, BuildingDef, GameState, Stock } from '../sim/types';

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;

export interface UiEvents {
  onSpeed(speed: 0 | 1 | 2 | 3): void;
  onSelectTool(def: BuildingDef | null): void;
  onDemolish(b: Building): void;
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
  private toastTimer = 0;

  constructor(private events: UiEvents) {
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

  toast(msg: string): void {
    const t = $('toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(this.toastTimer);
    this.toastTimer = window.setTimeout(() => (t.hidden = true), 1800);
  }

  /** Cost / radius / error line shown while placing. */
  setPlaceInfo(def: BuildingDef | null, error: string | null): void {
    const el = $('place-info');
    el.hidden = !def;
    if (!def) return;
    const extra = def.radius ? ` &middot; radius ${def.radius}` : '';
    el.innerHTML = `<b>${def.name}</b> &middot; cost ${costText(def.cost)}${extra}${error ? `<br><span class="warn">${error}</span>` : ''}`;
  }

  setState(s: GameState): void {
    const secs = s.tick / 10;
    $('clock').textContent = `${String(Math.floor(secs / 60)).padStart(2, '0')}:${(secs % 60).toFixed(1).padStart(4, '0')}`;
    $('tick').textContent = String(s.tick);
    document.querySelectorAll<HTMLButtonElement>('#topbar [data-speed]').forEach((btn) => {
      const v = Number(btn.dataset.speed);
      btn.classList.toggle('active', v === 0 ? s.paused : !s.paused && v === s.speed);
    });
    const rate = (g: string) => {
      const r = s.rates[g] ?? 0;
      return `<span class="${r > 0.05 ? 'pos' : r < -0.05 ? 'neg' : 'dim'}">${r >= 0 ? '+' : ''}${r.toFixed(0)}/m</span>`;
    };
    const cap = ECON.storageCap * s.buildings.filter((b) => b.type === 'depot').length;
    const goods = GOODS.map((g) => `<span class="g" data-good="${g.id}">${g.name} <b>${Math.floor(s.stock[g.id] ?? 0)}</b> ${rate(g.id)}</span>`).join('');
    const p = s.pop;
    const pw = s.power;
    $('hud').innerHTML =
      goods +
      `<span class="g" data-hud="pop">Laborers <b>${p.laborers}</b> Technicians <b>${p.technicians}</b></span>` +
      `<span class="g ${pw.demand > pw.supply ? 'neg' : ''}" data-hud="power">Power <b>${pw.demand}/${pw.supply}</b></span>` +
      `<span class="g dim">storage cap ${cap}</span>`;
    for (const [id, btn] of this.buttons) {
      const def = buildingDef(id);
      btn.classList.toggle('poor', !!def && affordError(s.stock, def) !== null);
    }
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
    } else if (def.id === 'depot') {
      lines.push(`Radius ${def.radius} &middot; cap ${ECON.storageCap}/good`);
    } else if (def.supply) {
      lines.push(`Supplies ${def.supply} power &middot; radius ${def.radius} &middot; colony ${s.power.demand}/${s.power.supply}`);
    } else {
      lines.push(`<span class="dim">${def.footprint[0]}x${def.footprint[1]} &middot; ${def.terrain.join(', ')}</span>`);
    }
    dyn.innerHTML = lines.join('<br>');
  }
}

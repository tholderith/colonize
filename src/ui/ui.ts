import { BUILDINGS, buildingDef } from '../sim/placement';
import type { Building, BuildingDef, GameState } from '../sim/types';

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;

export interface UiEvents {
  onSpeed(speed: 0 | 1 | 2 | 3): void;
  onSelectTool(def: BuildingDef | null): void;
  onDemolish(b: Building): void;
}

export class Ui {
  private tool: BuildingDef | null = null;
  private buttons = new Map<string, HTMLButtonElement>();

  constructor(private events: UiEvents) {
    document.querySelectorAll<HTMLButtonElement>('#topbar [data-speed]').forEach((btn) => {
      btn.addEventListener('click', () => events.onSpeed(Number(btn.dataset.speed) as 0 | 1 | 2 | 3));
    });
    const menu = $('build-menu');
    for (const def of BUILDINGS) {
      const btn = document.createElement('button');
      btn.dataset.building = def.id;
      btn.innerHTML = `<span>${def.name}</span><span class="dim">${def.footprint[0]}x${def.footprint[1]}</span>`;
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
    this.events.onSelectTool(def);
  }

  setState(s: GameState): void {
    const secs = s.tick / 10;
    $('clock').textContent = `${String(Math.floor(secs / 60)).padStart(2, '0')}:${(secs % 60).toFixed(1).padStart(4, '0')}`;
    $('tick').textContent = String(s.tick);
    document.querySelectorAll<HTMLButtonElement>('#topbar [data-speed]').forEach((btn) => {
      const v = Number(btn.dataset.speed);
      btn.classList.toggle('active', v === 0 ? s.paused : !s.paused && v === s.speed);
    });
  }

  showInfo(b: Building | null, status?: string): void {
    const body = $('info-body');
    const def = b && buildingDef(b.type);
    if (!b || !def) {
      body.className = 'dim';
      body.textContent = status ?? 'Nothing selected';
      return;
    }
    body.className = '';
    body.innerHTML = `<b>${def.name}</b> #${b.id}<br>at (${b.x}, ${b.y}) &middot; ${def.footprint[0]}x${def.footprint[1]}<br><span class="dim">terrain: ${def.terrain.join(', ')}</span><br>`;
    const btn = document.createElement('button');
    btn.id = 'btn-demolish';
    btn.textContent = 'DEMOLISH';
    btn.addEventListener('click', () => this.events.onDemolish(b));
    body.appendChild(btn);
  }
}

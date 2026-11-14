import { IND } from '../sim/placement';
import type { GameState } from '../sim/types';

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const KEY = 'foundry.objectives.dismissed';

interface Step {
  title: string;
  done(s: GameState): boolean;
  /** One-line hint for this step, and the build-menu items to highlight. */
  hint(s: GameState): [string, string[]];
}

const count = (s: GameState, type: string) => s.buildings.filter((b) => b.type === type).length;
const has = (s: GameState, type: string) => count(s, type) > 0;
const pop = (s: GameState) => s.pop.laborers + s.pop.technicians;
/** A hauler whose route stops at ports on two different islands. */
const linked = (s: GameState) =>
  s.haulers.some((h) => new Set(h.route.flatMap((st) => (st.kind === 'port' ? [s.buildings.find((b) => b.id === st.building)?.island] : []))).size >= 2);

const STEPS: Step[] = [
  { title: 'Place a wind turbine', done: (s) => has(s, 'wind_turbine'), hint: () => ['Everything needs power. Pick Wind Turbine and click land near your depot.', ['wind_turbine']] },
  {
    title: 'Build hydroponics, then a ration plant',
    done: (s) => has(s, 'hydroponics') && has(s, 'ration_plant'),
    hint: (s) => (has(s, 'hydroponics') ? ['Ration plants turn biomass into rations. Place one near the turbine.', ['ration_plant']] : ['Hydroponics grow biomass. Place one inside turbine range.', ['hydroponics']]),
  },
  { title: 'House 20 colonists', done: (s) => pop(s) >= 20, hint: (s) => [`Pod houses need rations nearby. Colonists ${pop(s)}/20. They pay tax and staff your buildings.`, ['pod_house', 'ration_plant']] },
  {
    title: 'Start alloy: scrap yard, then smelter',
    done: (s) => has(s, 'scrap_yard') && has(s, 'smelter'),
    hint: (s) => (has(s, 'scrap_yard') ? ['The smelter turns scrap into alloy, which most buildings cost.', ['smelter']] : ['Scrap yards make scrap. Build one, then a smelter.', ['scrap_yard']]),
  },
  {
    title: 'Port, hauler, link two islands',
    done: linked,
    hint: (s) => {
      const depots = new Set(s.buildings.filter((b) => b.type === 'depot').map((b) => b.island)).size;
      const ports = new Set(s.buildings.filter((b) => b.type === 'port').map((b) => b.island)).size;
      if (depots < 2) return ['Claim a second island: place a Depot on it.', ['depot']];
      if (ports < 2) return ['Each island needs a Port on its coast, facing open water east.', ['port']];
      if (!s.haulers.length) return ['Select a port and press BUILD HAULER.', []];
      return ['Select the hauler, then add each port to its route (set load/unload orders).', []];
    },
  },
  {
    title: 'Meet a Concordat demand',
    done: (s) => s.ind.calmUntil > 0,
    hint: (s) => {
      const d = s.concordat.demand;
      return [d ? `Deliver ${d.amount - d.delivered} ${d.good} to the exchange (EXCHANGE panel, hauler orders) for ${d.reward} cr.` : 'A demand will arrive soon. Keep a hauler and some stock ready.', []];
    },
  },
  {
    title: 'Reach 50% independence',
    done: (s) => s.ind.sentiment >= IND.sentiment.declareAt || s.ind.declared,
    hint: (s) => [`Independence ${Math.floor(s.ind.sentiment)}%. Signal relays and technicians raise it; a heavy levy angers the colony.`, ['signal_relay']],
  },
  {
    title: 'Declare and survive the blockade',
    done: (s) => !!s.outcome?.win,
    hint: (s) =>
      s.ind.declared
        ? [`Blockade cycle ${Math.min(s.ind.cycles, IND.blockade.cyclesToWin)}/${IND.blockade.cyclesToWin}. Keep haulers away from patrols, stay solvent and keep your people fed.`, []]
        : [`Build 3 coastal batteries (${count(s, 'coastal_battery')} so far) and stock alloy, then DECLARE in the Concordat panel.`, ['coastal_battery']],
  },
];

/** Auto-advancing checklist: steps tick off from the game state. Hidden state persists in localStorage. */
export class Objectives {
  private done = new Set<number>();
  private last = '';
  private shown = true;

  constructor(private highlight: (ids: string[]) => void) {
    try {
      this.shown = localStorage.getItem(KEY) !== '1';
    } catch {
      /* storage blocked: stay visible */
    }
    $('obj-close').addEventListener('click', () => this.show(false));
    $('btn-objectives').addEventListener('click', () => this.show(!this.shown));
    this.show(this.shown);
  }

  private show(on: boolean): void {
    this.shown = on;
    $('objectives').hidden = !on;
    $('btn-objectives').classList.toggle('active', on);
    try {
      localStorage.setItem(KEY, on ? '0' : '1');
    } catch {
      /* ignore */
    }
    if (!on) this.highlight([]);
    this.last = '';
  }

  reset(): void {
    this.done.clear();
    this.last = '';
  }

  update(s: GameState): void {
    STEPS.forEach((st, i) => {
      if (!this.done.has(i) && st.done(s)) this.done.add(i);
    });
    const cur = STEPS.findIndex((_, i) => !this.done.has(i));
    const [hint, build] = cur < 0 ? ['All objectives complete. Freedom.', []] : STEPS[cur]!.hint(s);
    const html =
      STEPS.map((st, i) => `<li class="${this.done.has(i) ? 'done' : i === cur ? 'now' : ''}">${st.title}</li>`).join('') + `\u0000${hint}`;
    if (html === this.last) return;
    this.last = html;
    const [list, text] = html.split('\u0000');
    $('obj-list').innerHTML = list ?? '';
    $('obj-hint').textContent = text ?? '';
    this.highlight(this.shown ? build : []);
  }
}

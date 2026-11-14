import { IND } from '../sim/placement';
import { sentimentRate } from '../sim/independence';
import type { EndCause, GameState } from '../sim/types';

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const sign = (n: number) => `${n >= 0 ? '+' : '-'}${Math.abs(n).toFixed(1)}`;
const mmss = (ticks: number) => {
  const s = Math.max(0, Math.floor(ticks / 10));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
};
const CAUSES: Record<EndCause, [string, string]> = {
  victory: ['VICTORY', 'The blockade is broken. The Concordat withdraws its patrols and the colony is free.'],
  bankruptcy: ['BANKRUPT', 'Credits stayed below zero for two levy periods. The creditors have taken the foundry.'],
  collapse: ['COLONY COLLAPSED', 'The population fell below half of what it was at the declaration. Nobody is left to hold the line.'],
  suppression: ['SUPPRESSED', 'Repeated audit fines while the colony stirred. The Concordat has dissolved the charter by force.'],
};

export interface IndependenceEvents {
  onDeclare(): void;
  onNewGame(): void;
}

/** Sentiment meter, drivers, declare button (with in-page confirm), blockade strip and the end screen. */
export class IndependenceUi {
  private confirming = false;
  private ended = false;

  constructor(private ev: IndependenceEvents) {
    $('btn-declare').addEventListener('click', () => {
      this.confirming = true;
      this.sync();
    });
    $('btn-declare-no').addEventListener('click', () => {
      this.confirming = false;
      this.sync();
    });
    $('btn-declare-yes').addEventListener('click', () => {
      this.confirming = false;
      this.ev.onDeclare();
      this.sync();
    });
    $('btn-endmenu').addEventListener('click', () => location.reload());
    $('btn-endnew').addEventListener('click', () => this.ev.onNewGame());
  }

  /** Back to a fresh game or a loaded save: hide the end screen. */
  reset(): void {
    this.ended = false;
    this.confirming = false;
    $('endscreen').hidden = true;
  }

  private canDeclare = false;
  private sync(): void {
    $('btn-declare').hidden = !this.canDeclare || this.confirming;
    $('declare-confirm').hidden = !this.canDeclare || !this.confirming;
  }

  update(s: GameState): void {
    const ind = s.ind;
    const pct = ind.sentiment;
    $('ind-pct').textContent = `${Math.floor(pct)}%`;
    $('ind-fill').style.width = `${pct}%`;
    $('ind-fill').classList.toggle('hot', pct >= IND.sentiment.declareAt);
    $('ind-drivers').hidden = ind.declared;
    $('ind-blockade').hidden = !ind.declared;
    if (!ind.declared) {
      const d = ind.drivers;
      const relays = s.buildings.filter((b) => b.type === 'signal_relay').length;
      const row = (label: string, v: number, extra = '') => (Math.abs(v) < 0.005 ? '' : `<div><span>${label}${extra}</span><b class="${v > 0 ? 'neg' : 'pos'}">${sign(v)}/m</b></div>`);
      const rows =
        row('Levy', d.levy, ` <em>${s.concordat.levyPct}%</em>`) + row('Technicians', d.tech, ` <em>${s.pop.technicians}</em>`) + row('Signal relays', d.relay, ` <em>${relays}</em>`) +
        row('Grievances', d.grievance) + row('Demands met', d.calm);
      $('ind-drivers').innerHTML = `${rows || '<div class="dim">No pressure on the colony yet</div>'}<div class="net"><span>Net</span><b>${sign(sentimentRate(ind))}/m</b></div>`;
    } else {
      const B = IND.blockade;
      const patrols = s.patrols.length;
      const elapsed = s.tick - ind.declaredAt;
      const pop = s.pop.laborers + s.pop.technicians;
      const need = Math.ceil(B.popWinPct * ind.popAtDeclare);
      const ok = (v: boolean, text: string) => `<span class="${v ? 'pos' : 'neg'}">${v ? 'OK' : 'NO'}</span> ${text}`;
      $('ind-blockade').innerHTML =
        `<div class="strip"><span>BLOCKADE</span><b>cycle ${Math.min(ind.cycles, B.cyclesToWin)}/${B.cyclesToWin}</b><span>patrols <b>${patrols}</b></span><span>seized <b>${ind.seized}</b></span></div>` +
        `<span class="bar wide"><i style="width:${Math.min(100, (elapsed / (B.cycleTicks * B.cyclesToWin)) * 100)}%"></i></span> next cycle in ${mmss(B.cycleTicks - (elapsed % B.cycleTicks))}<br>` +
        `${ok(s.credits >= 0, `solvent (${Math.floor(s.credits)} cr)`)} &middot; ${ok(pop >= need, `population ${pop}/${need} needed`)}`;
    }
    this.canDeclare = !ind.declared && !s.outcome && pct >= IND.sentiment.declareAt;
    if (!this.canDeclare) this.confirming = false;
    this.sync();
    if (s.outcome && !this.ended) {
      this.ended = true;
      const [title, text] = CAUSES[s.outcome.cause];
      $('end-title').textContent = title;
      $('end-title').className = s.outcome.win ? 'pos' : 'neg';
      $('end-cause').textContent = text;
      const st = s.stats;
      $('end-stats').innerHTML = [
        ['Time played', mmss(s.outcome.tick)], ['Peak population', String(st.peakPop)], ['Credits earned', String(Math.floor(st.creditsEarned))], ['Cargo moved', String(Math.floor(st.cargoMoved))],
      ].map(([k, v]) => `<tr><td class="dim">${k}</td><td><b>${v}</b></td></tr>`).join('');
      $('endscreen').hidden = false;
    }
  }
}

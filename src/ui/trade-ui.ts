import { GOODS, TRADE } from '../sim/placement';
import type { GameState, Hauler, Order, Stop } from '../sim/types';

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const tradeGoods = GOODS.filter((g) => g.price);
const goodName = (id: string) => GOODS.find((g) => g.id === id)?.name ?? id;
const mmss = (ticks: number) => {
  const s = Math.max(0, Math.ceil(ticks / 10));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
};

export interface TradeEvents {
  onSetRoute(hauler: number, route: Stop[]): void;
  onScrap(hauler: number): void;
  onTrade(): void;
  /** Exchange panel: add/replace an order on the selected hauler's exchange stop. */
  onExchangeOrder(good: string, mode: Order['mode'], amount: number): void;
  toast(msg: string, kind?: 'info' | 'bad'): void;
}

/** Concordat, exchange and hauler panels. */
export class TradeUi {
  /** Set while the player is choosing a port on the map for this hauler's route. */
  picking: number | null = null;
  private hauler: number | null = null;
  private haulerKey = '';
  private exchangeKey = '';
  private seen = -1;

  constructor(private ev: TradeEvents) {
    $('btn-concordat').addEventListener('click', () => {
      const p = $('concordat');
      p.hidden = !p.hidden;
      $('btn-concordat').classList.toggle('active', !p.hidden);
      if (!p.hidden) this.closeOther('exchange');
    });
    $('btn-exchange').addEventListener('click', () => {
      const p = $('exchange');
      p.hidden = !p.hidden;
      $('btn-exchange').classList.toggle('active', !p.hidden);
      this.exchangeKey = '';
      if (!p.hidden) this.closeOther('concordat');
    });
  }

  /** Concordat and exchange share the same screen area: opening one closes the other. */
  private closeOther(id: 'concordat' | 'exchange'): void {
    $(id).hidden = true;
    $(`btn-${id}`).classList.remove('active');
  }

  selectHauler(id: number | null): void {
    this.hauler = id;
    this.picking = null;
    this.haulerKey = '';
    $('hauler-panel').hidden = id === null;
  }
  get selected(): number | null {
    return this.hauler;
  }

  update(s: GameState): void {
    this.concordat(s);
    this.exchange(s);
    this.haulerPanel(s);
  }

  private concordat(s: GameState): void {
    const c = s.concordat;
    // Toasts for new events (first snapshot only records what already happened).
    if (this.seen < 0) this.seen = c.seq;
    for (const e of c.log) if (e.id > this.seen) this.ev.toast(e.text, e.kind === 'demand_missed' || e.kind === 'levy' || e.kind === 'seized' || e.kind === 'declared' || (e.kind === 'audit' && !e.text.endsWith('clean')) ? 'bad' : 'info');
    this.seen = c.seq;
    const next = c.periodStart + TRADE.levy.periodTicks - s.tick;
    const d = c.demand;
    const trader = s.visitors.find((v) => v.kind === 'trader' && v.phase === 'dock');
    const lines = s.ind.declared ? [
      '<span class="dim">Levy, demands and audits ended. The exchange is closed: free traders are your lifeline (+50% prices).</span>',
      trader ? `<span class="pos">Free trader docked</span> <span class="dim">(${mmss(trader.wait)} left)</span>` : '',
      '<div class="dim log">' + (c.log.slice(-5).reverse().map((e) => `${mmss(e.tick)} ${e.text}`).join('<br>') || 'No events yet') + '</div>',
    ] : [
      `<span data-tip="Levy: the Concordat takes this share of the credits you earn each period (5 min). It rises with population. A big levy also builds independence sentiment.">Levy</span> <b>${c.levyPct}%</b> in ${mmss(next)} &middot; earned <b>${Math.floor(c.earned)}</b> cr${c.penaltyPeriods ? ' <span class="neg">(+penalty)</span>' : ''}${c.relief ? ' <span class="pos">(-relief)</span>' : ''}`,
      d
        ? `<span data-tip="Demand: the Concordat orders goods delivered to its exchange by the deadline. Meet it for a credit reward and a lower levy; miss it and you are fined and taxed more.">Demand</span> <b>${d.amount} ${goodName(d.good)}</b> by ${mmss(d.deadline - s.tick)}<br><span class="bar"><i style="width:${Math.min(100, (d.delivered / d.amount) * 100)}%"></i></span> ${d.delivered}/${d.amount} &middot; +${d.reward} / -${d.fine} cr`
        : `<span data-tip="Demand: the Concordat orders goods delivered to its exchange by the deadline. Meet it for a credit reward and a lower levy; miss it and you are fined and taxed more.">Demand</span> <span class="dim">next in ${mmss(c.nextDemandAt - s.tick)}</span>`,
      `<span data-tip="Tariff: the cut the Concordat keeps when you sell at its exchange. Free traders at your ports pay better and charge no tariff.">Tariff</span> <b>${Math.round(c.tariff * 100)}%</b> &middot; <span data-tip="Contraband exposure: grows with every untaxed deal with a free trader. The higher it is, the likelier the next Concordat audit finds it and fines you (which also angers the colony).">contraband exposure</span> <b class="${c.exposure > 5 ? 'neg' : ''}">${c.exposure.toFixed(1)}</b>`,
      trader ? `<span class="pos">Free trader docked</span> <span class="dim">(${mmss(trader.wait)} left)</span>` : '',
      '<div class="dim log">' + (c.log.slice(-5).reverse().map((e) => `${mmss(e.tick)} ${e.text}`).join('<br>') || 'No events yet') + '</div>',
    ];
    $('concordat-body').innerHTML = lines.filter(Boolean).join('<br>');
  }

  private exchange(s: GameState): void {
    if ($('exchange').hidden) return;
    const c = s.concordat;
    const key = `${c.demand?.good}|${c.tariff}`;
    if (s.ind.declared) {
      this.exchangeKey = 'closed';
      $('exchange-body').innerHTML = '<span class="neg">CLOSED.</span> The Concordat blockade has shut the exchange. Trade with free traders at the ports.';
      return;
    }
    if (key === this.exchangeKey) return;
    this.exchangeKey = key;
    const rows = tradeGoods
      .map((g) => {
        const p = g.price as number;
        const hot = c.demand?.good === g.id ? ' class="hot"' : '';
        return `<tr${hot}><td>${g.name}</td><td>${p}</td><td>${(p * (1 - c.tariff)).toFixed(1)}</td><td><input type="number" min="1" value="10" data-amt="${g.id}"></td>` +
          `<td><button data-sell="${g.id}">SELL</button> <button data-buy="${g.id}">BUY</button></td></tr>`;
      })
      .join('');
    $('exchange-body').innerHTML =
      `<div class="dim">Tariff ${Math.round(c.tariff * 100)}% on sales. Buying costs the base price. Orders are added to the selected hauler's exchange stop.</div>` +
      `<table><tr class="dim"><td>Good</td><td>Price</td><td data-tip="What you receive per unit after the Concordat tariff is taken off the price.">Sell net</td><td>Amount</td><td></td></tr>${rows}</table>`;
    $('exchange-body').querySelectorAll<HTMLButtonElement>('button').forEach((b) =>
      b.addEventListener('click', () => {
        const good = b.dataset.sell ?? (b.dataset.buy as string);
        const amt = Number(($('exchange-body').querySelector(`[data-amt="${good}"]`) as HTMLInputElement).value) || 1;
        this.ev.onExchangeOrder(good, b.dataset.sell ? 'unload' : 'load', amt);
      }),
    );
  }

  private stopLabel(s: GameState, st: Stop): string {
    if (st.kind === 'exchange') return 'Concordat Exchange';
    const b = s.buildings.find((o) => o.id === st.building);
    return b ? `${s.islands[b.island]?.name} port #${b.id}` : '<span class="neg">missing port</span>';
  }

  private haulerPanel(s: GameState): void {
    const h = s.haulers.find((o) => o.id === this.hauler);
    if (this.hauler !== null && !h) this.selectHauler(null);
    if (!h) return;
    const key = JSON.stringify(h.route) + (this.picking === h.id);
    if (key !== this.haulerKey) {
      this.haulerKey = key;
      this.buildHauler(s, h);
    }
    const cargo = Object.entries(h.cargo).map(([g, n]) => `${n} ${goodName(g).toLowerCase()}`).join(', ') || 'empty';
    const used = Object.values(h.cargo).reduce((t, n) => t + n, 0);
    const stop = h.route[h.stop];
    $('hauler-live').innerHTML = `${h.phase === 'dock' ? 'Docked at' : 'Sailing to'} <b>${stop ? this.stopLabel(s, stop) : '-'}</b><br>Cargo ${used}/${TRADE.hauler.capacity}: ${cargo}`;
  }

  private buildHauler(s: GameState, h: Hauler): void {
    const body = $('hauler-body');
    const goodOpts = (sel: string) => tradeGoods.map((g) => `<option value="${g.id}"${g.id === sel ? ' selected' : ''}>${g.name}</option>`).join('');
    const edit = (fn: (route: Stop[]) => void) => {
      const route: Stop[] = JSON.parse(JSON.stringify(h.route));
      fn(route);
      this.ev.onSetRoute(h.id, route);
    };
    body.innerHTML = `<b>Hauler #${h.id}</b> <span class="dim">cap ${TRADE.hauler.capacity}, ${TRADE.hauler.slots} slots</span><div id="hauler-live"></div><div id="route"></div>` +
      `<div class="row"><button id="add-port"${this.picking === h.id ? ' class="active"' : ''}>${this.picking === h.id ? 'CLICK A PORT...' : '+ PORT (click map)'}</button> <button id="add-ex">+ EXCHANGE</button> <button id="scrap">SCRAP</button></div>`;
    const route = body.querySelector('#route') as HTMLElement;
    h.route.forEach((st, i) => {
      const div = document.createElement('div');
      div.className = 'stop';
      div.innerHTML = `<div><span class="dim">${i + 1}.</span> <b>${this.stopLabel(s, st)}</b> <button data-rm>x</button></div>` +
        st.orders.map((o, j) =>
          `<div class="order"><select data-mode="${j}"><option value="load"${o.mode === 'load' ? ' selected' : ''}>${st.kind === 'exchange' ? 'buy' : 'load'}</option><option value="unload"${o.mode === 'unload' ? ' selected' : ''}>${st.kind === 'exchange' ? 'sell' : 'unload'}</option></select>` +
          `<select data-good="${j}">${goodOpts(o.good)}</select><input type="number" min="1" max="${TRADE.hauler.capacity}" value="${o.amount}" data-amt="${j}"><button data-del="${j}">x</button></div>`).join('') +
        '<div><button data-add>+ order</button></div>';
      div.querySelector('[data-rm]')?.addEventListener('click', () => edit((r) => r.splice(i, 1)));
      div.querySelector('[data-add]')?.addEventListener('click', () => edit((r) => r[i]?.orders.push({ good: 'rations', mode: 'load', amount: 10 })));
      div.querySelectorAll<HTMLElement>('[data-del]').forEach((e) => e.addEventListener('click', () => edit((r) => r[i]?.orders.splice(Number(e.dataset.del), 1))));
      div.querySelectorAll<HTMLSelectElement>('[data-mode]').forEach((e) => e.addEventListener('change', () => edit((r) => { (r[i]?.orders[Number(e.dataset.mode)] as Order).mode = e.value as Order['mode']; })));
      div.querySelectorAll<HTMLSelectElement>('[data-good]').forEach((e) => e.addEventListener('change', () => edit((r) => { (r[i]?.orders[Number(e.dataset.good)] as Order).good = e.value; })));
      div.querySelectorAll<HTMLInputElement>('[data-amt]').forEach((e) => e.addEventListener('change', () => edit((r) => { (r[i]?.orders[Number(e.dataset.amt)] as Order).amount = Number(e.value) || 1; })));
      route.appendChild(div);
    });
    body.querySelector('#add-port')?.addEventListener('click', () => {
      this.picking = this.picking === h.id ? null : h.id;
      this.haulerKey = '';
      if (this.picking !== null) this.ev.toast('Click a port on the map to add it as a stop');
    });
    body.querySelector('#add-ex')?.addEventListener('click', () => edit((r) => r.push({ kind: 'exchange', orders: [] })));
    body.querySelector('#scrap')?.addEventListener('click', () => this.ev.onScrap(h.id));
  }
}

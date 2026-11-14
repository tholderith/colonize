import { IND } from '../sim/placement';
import type { Difficulty } from '../sim/types';
import { readSave, saveMeta, type Slot, type StartDesc } from './saves';

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const SAVE_SLOTS: [Slot, string][] = [['auto', 'AUTOSAVE'], ['manual', 'MANUAL SLOT']];

/** The start menu. Resolves with what to start; the overlay is hidden afterwards. */
export function showMenu(): Promise<StartDesc> {
  const menu = $('menu');
  const img = new Image();
  img.onload = () => (menu.style.backgroundImage = `linear-gradient(rgba(5,10,20,0.35), rgba(5,10,20,0.75)), url(${img.src})`);
  img.src = `${import.meta.env.BASE_URL}assets/ui/title.png`;

  const seedInput = $<HTMLInputElement>('m-seed');
  const fromUrl = new URLSearchParams(location.search).get('seed');
  const roll = () => String(Math.floor(Math.random() * 1_000_000));
  seedInput.value = fromUrl ?? roll();
  $('m-dice').addEventListener('click', () => (seedInput.value = roll()));
  const diffs = $('m-diff');
  (Object.keys(IND.difficulty) as Difficulty[]).forEach((d) => {
    const label = document.createElement('label');
    label.innerHTML = `<input type="radio" name="diff" value="${d}"${d === 'standard' ? ' checked' : ''}> ${IND.difficulty[d].label.toUpperCase()}`;
    diffs.appendChild(label);
  });

  const info = (slot: Slot) => {
    const m = saveMeta(readSave(slot));
    return m ? `seed ${m.seed} &middot; ${m.difficulty} &middot; ${Math.floor(m.tick / 600)} min played` : null;
  };
  const cont = $<HTMLButtonElement>('m-continue');
  const autoInfo = info('auto');
  cont.disabled = !autoInfo;
  $('m-continue-info').innerHTML = autoInfo ?? 'no autosave';

  return new Promise((resolve) => {
    const start = (d: StartDesc) => {
      menu.hidden = true;
      resolve(d);
    };
    const msg = (t: string) => ($('m-msg').textContent = t);
    $('m-new').addEventListener('click', () => {
      const raw = seedInput.value.trim();
      const seed = /^-?\d+$/.test(raw) ? Number(raw) : [...raw].reduce((h, c) => (Math.imul(h, 31) + c.charCodeAt(0)) | 0, 7);
      const difficulty = (document.querySelector<HTMLInputElement>('input[name="diff"]:checked')?.value ?? 'standard') as Difficulty;
      start({ kind: 'new', seed, difficulty });
    });
    cont.addEventListener('click', () => {
      const data = readSave('auto');
      if (data) start({ kind: 'load', data });
    });
    $('m-load').addEventListener('click', () => {
      const list = $('m-slots');
      list.innerHTML = '';
      for (const [slot, name] of SAVE_SLOTS) {
        const b = document.createElement('button');
        const i = info(slot);
        b.disabled = !i;
        b.innerHTML = `${name}<span class="dim">${i ?? 'empty'}</span>`;
        b.addEventListener('click', () => {
          const data = readSave(slot);
          if (data) start({ kind: 'load', data });
        });
        list.appendChild(b);
      }
      $('menu-main').hidden = true;
      $('menu-load').hidden = false;
    });
    $('m-back').addEventListener('click', () => {
      $('menu-main').hidden = false;
      $('menu-load').hidden = true;
      msg('');
    });
    $<HTMLInputElement>('m-file').addEventListener('change', async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      const data = await file.text();
      if (saveMeta(data)) start({ kind: 'load', data });
      else msg('That file is not a Foundry save.');
    });
  });
}

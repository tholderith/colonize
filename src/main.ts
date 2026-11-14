import { showMenu } from './ui/menu';

const desc = await showMenu();
const { startGame } = await import('./game');
await startGame(desc);

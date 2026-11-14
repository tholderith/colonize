import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist', 'test-results', 'playwright-report', 'node_modules', 'public', 'art'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    // The sim must stay deterministic and DOM-free.
    files: ['src/sim/**/*.ts'],
    ignores: ['src/sim/worker.ts'],
    rules: {
      'no-restricted-properties': [
        'error',
        { object: 'Math', property: 'random', message: 'Use the seeded RNG.' },
        { object: 'Date', property: 'now', message: 'No wall-clock time in the sim.' },
        { object: 'performance', property: 'now', message: 'No wall-clock time in the sim.' },
      ],
      'no-restricted-globals': ['error', 'window', 'document', 'localStorage'],
    },
  },
);

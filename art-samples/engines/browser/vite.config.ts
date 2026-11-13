import { defineConfig } from 'vite';

// base: './' => every asset URL in dist/index.html is relative, so dist/ can be
// dropped into any static host path (or opened from a sub-folder).
export default defineConfig({
  base: './',
  build: { outDir: 'dist', emptyOutDir: true, chunkSizeWarningLimit: 2000 },
});

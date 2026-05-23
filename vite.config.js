import { defineConfig } from 'vite';

export default defineConfig({
  base: '/electronic-music-history/',
  build: { outDir: 'dist' },
  test: { environment: 'node' },
});

import { defineConfig } from 'vite';

export default defineConfig({
  base: '/Electronic-Music-History/',
  build: { outDir: 'dist' },
  test: { environment: 'node' },
});

import { resolve } from 'node:path';

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: 'dist-react',
    rollupOptions: {
      input: {
        react: resolve(__dirname, 'react-index.html'),
      },
    },
  },
});

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

// Electron build mode
const isElectronBuild = process.env.ELECTRON_BUILD === 'true'

export default defineConfig({
  plugins: [react()],
  base: isElectronBuild ? './' : '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    // The Ant Design + rc-* runtime is intentionally bundled as a shared
    // design-system chunk. The ceiling is raised to the actual post-split size
    // so build output stays signal-rich instead of flagging the deliberate bucket.
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
      },
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-router': ['react-router-dom'],
          'vendor-data': ['axios', '@hey-api/client-fetch', '@tanstack/react-query'],
          'vendor-utils': ['dayjs', 'zustand'],
          'vendor-icons': ['@ant-design/icons'],
          'vendor-pro': ['@ant-design/pro-components'],
          'vendor-antd': ['antd'],
        },
      },
    },
  },
  esbuild: {
    target: 'es2020',
  },
})

if (!isElectronBuild) {
  // Development-only branch reserved for future Vite HMR tweaks.
}

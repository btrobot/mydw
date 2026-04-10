import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

// Electron 构建模式
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
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
      },
    },
  },
  // 生产环境构建配置
  esbuild: {
    target: 'es2020',
  },
})

// 热模块替换配置
if (!isElectronBuild) {
  // 开发模式配置
}

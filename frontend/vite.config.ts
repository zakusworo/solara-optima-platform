import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      // Isolate the heavy plotly bundle into its own on-demand chunk (loaded
      // only when a <LazyPlot> renders); keep all other node_modules in one
      // shared vendor chunk so the initial app-shell bundle stays small. We
      // deliberately do not split react into its own chunk — doing so created a
      // vendor <-> react-vendor circular chunk.
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('react-plotly') || id.includes('plotly.js')) return 'plotly'
          return 'vendor'
        },
      },
    },
  },
})

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue(), vueJsx()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      // 用户服务代理
      '/api/v1/users': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path,
      },
      '/api/v1/collections': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path,
      },
      // 视频服务代理
      '/api/v1/videos': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path,
      },
      // 洞察服务代理
      '/api/v1/insights': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path) => path,
      },
      // 数据采集服务代理（包括 viral alerts）
      '/api/v1/collector': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path,
      },
      '/api/v1/viral': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path,
      },
      // 竞品监控服务代理
      '/api/v1/competitor': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        rewrite: (path) => path,
      },
      // 报表服务代理
      '/api/v1/reports': {
        target: 'http://localhost:8006',
        changeOrigin: true,
        rewrite: (path) => path,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'echarts': ['echarts', 'vue-echarts']
        }
      }
    }
  }
})
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { VantResolver } from '@vant/auto-import-resolver'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [VantResolver()],
    }),
    Components({
      resolvers: [VantResolver()],
    }),
  ],
  define: {
    __API_BASE_URL__: JSON.stringify('https://zuowen.papierkran.top/api'),
  },
  server: {
    host: '::',
    port: 5173,
    allowedHosts: ['zuowen.papierkran.top', '.papierkran.top'],
    proxy: {
      '/api': {
        target: 'http://localhost:6886',
        changeOrigin: true,
      },
    },
  },
})

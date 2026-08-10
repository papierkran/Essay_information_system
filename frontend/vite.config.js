import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { VantResolver } from '@vant/auto-import-resolver'

export default defineConfig(({ mode }) => {
  const isDev = mode === 'development'
  return {
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
      // dev 模式用相对路径 /api（走 vite proxy → localhost:6886），局域网可直接访问
      // 生产构建保留公网后端域名
      __API_BASE_URL__: JSON.stringify(isDev ? '' : 'https://zwhd.papierkran.top'),
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
  }
})

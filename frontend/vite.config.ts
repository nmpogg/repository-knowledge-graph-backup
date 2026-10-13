import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const upstream = process.env.RKG_API_UPSTREAM ?? 'http://127.0.0.1:8000'
const apiProxy = { '/api': { target: upstream, changeOrigin: false } }

export default defineConfig({
  plugins: [react()],
  envDir: '..',
  server: { proxy: apiProxy },
  preview: { proxy: apiProxy },
})

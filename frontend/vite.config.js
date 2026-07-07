import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Django serves this directory as a static app (see settings/base.py
    // STATICFILES_DIRS); fixed, unhashed filenames so base.html can
    // reference them directly without reading a Vite manifest.
    outDir: '../src/kava_varasto/static/frontend',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'main.js',
        assetFileNames: 'main.[ext]',
      },
    },
  },
  server: {
    // Let `npm run dev` talk to a locally running Django dev server
    // (`manage.py runserver`) without CORS/CSRF headaches.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/i18n': 'http://127.0.0.1:8000',
    },
  },
})

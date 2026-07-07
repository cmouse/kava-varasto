import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Django serves this directory as a static app (see settings/base.py
    // STATICFILES_DIRS). Hashed filenames + manifest so repeat deploys
    // bust caches; spa.html resolves the real filenames via the
    // `vite_asset`/`vite_css` template tags (kava_varasto/templatetags/vite.py).
    outDir: '../src/kava_varasto/static/frontend',
    emptyOutDir: true,
    manifest: true,
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

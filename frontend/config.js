/**
 * config.js – TaskFlow2 API Configuration
 *
 * Local:
 *   http://localhost:3000  → http://localhost:8000
 *   http://127.0.0.1:3000 → http://127.0.0.1:8000
 *
 * Production:
 *   Netlify → Railway backend
 */

(function (window) {
  'use strict';

  const BACKEND_PORT = '8000';

  const PRODUCTION_API_BASE =
    'https://taskflow2-manish.up.railway.app';

  const Config = {

    getApiBase() {

      // 1. Manual override
      const override =
        localStorage.getItem('taskflow_api_override');

      if (override) {
        const base = override.replace(/\/$/, '');

        console.log(
          '[Config] Using manual API override:',
          base
        );

        return base;
      }

      const protocol = window.location.protocol;
      const hostname = window.location.hostname;
      const port = window.location.port;

      // 2. Backend itself
      if (port === BACKEND_PORT) {

        const base =
          `${protocol}//${hostname}:${BACKEND_PORT}`;

        console.log(
          '[Config] Backend port detected:',
          base
        );

        return base;
      }

      // 3. Local development
      if (
        hostname === 'localhost' ||
        hostname === '127.0.0.1' ||
        hostname === '0.0.0.0'
      ) {

        const base =
          `${protocol}//${hostname}:${BACKEND_PORT}`;

        console.log(
          '[Config] Local development:',
          base
        );

        return base;
      }

      // 4. Production
      console.log(
        '[Config] Production frontend detected. Railway backend:',
        PRODUCTION_API_BASE
      );

      return PRODUCTION_API_BASE;
    },

    setApiOverride(url) {

      const cleanUrl =
        url.replace(/\/$/, '');

      localStorage.setItem(
        'taskflow_api_override',
        cleanUrl
      );

      console.log(
        '[Config] API override saved:',
        cleanUrl
      );
    },

    clearApiOverride() {

      localStorage.removeItem(
        'taskflow_api_override'
      );

      console.log(
        '[Config] API override cleared'
      );
    },

    async testConnection() {

      const apiBase =
        this.getApiBase();

      try {

        const res =
          await fetch(`${apiBase}/health`);

        const data =
          res.ok
            ? await res.json()
            : null;

        if (res.ok) {

          console.log(
            '[Config] ✅ Backend reachable:',
            apiBase,
            data
          );

          return {
            success: true,
            apiBase,
            data
          };
        }

        console.warn(
          '[Config] ⚠️ Backend returned HTTP',
          res.status
        );

        return {
          success: false,
          apiBase,
          error: `HTTP ${res.status}`
        };

      } catch (err) {

        console.error(
          '[Config] ❌ Backend connection failed:',
          err.message
        );

        return {
          success: false,
          apiBase,
          error: err.message
        };
      }
    }
  };

  window.Config = Config;

  window.addEventListener(
    'DOMContentLoaded',
    () => Config.testConnection()
  );

})(window);
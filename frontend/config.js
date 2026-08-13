/**
 * config.js – Single source of truth for the backend API base URL.
 *
 * Rules (in priority order):
 *  1. localStorage override  → use it as-is
 *  2. Frontend IS on port 8000 → backend is same origin
 *  3. Frontend is on localhost / 127.0.0.1 (any port) → backend is :8000
 *  4. Anything else (deployed domain) → same origin (backend serves frontend)
 *
 * Never uses window.location.origin as the backend URL when the frontend
 * is running on a dev port (3000, 5500, 5173, etc.).
 */
(function (window) {
  'use strict';

  // ── Hardcoded default backend port ──────────────────────────────────────
  const BACKEND_PORT = '8000';

  const Config = {
    /**
     * Returns the base URL for all API requests.
     * @returns {string}  e.g. "http://127.0.0.1:8000"
     */
    getApiBase() {
      // 1. Manual override (set via Config.setApiOverride() in the console)
      const override = localStorage.getItem('taskflow_api_override');
      if (override) {
        console.log('[Config] Using manual API override:', override);
        return override.replace(/\/$/, ''); // strip trailing slash
      }

      const protocol = window.location.protocol; // "http:" | "https:"
      const hostname = window.location.hostname; // "localhost" | "127.0.0.1" | "example.com"
      const port     = window.location.port;     // "3000" | "5500" | "" | "8000"

      // 2. Already on the backend port → same origin
      if (port === BACKEND_PORT) {
        const base = `${protocol}//${hostname}:${BACKEND_PORT}`;
        console.log('[Config] Backend port detected, using same origin:', base);
        return base;
      }

      // 3. Local development on any port → always point to :8000 on same host
      if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0') {
        const base = `${protocol}//${hostname}:${BACKEND_PORT}`;
        console.log('[Config] Local dev detected (port ' + (port || 'none') + '), using backend:', base);
        return base;
      }

      // 4. Deployed / other domain → assume backend is co-located on same origin
      const base = `${protocol}//${hostname}${port ? ':' + port : ''}`;
      console.log('[Config] Production / unknown host, using same origin:', base);
      return base;
    },

    /**
     * Permanently override the API base URL (useful for testing).
     * Call from browser console: Config.setApiOverride("http://192.168.1.5:8000")
     */
    setApiOverride(url) {
      localStorage.setItem('taskflow_api_override', url);
      console.log('[Config] API override saved:', url);
    },

    /** Remove the manual override and revert to auto-detection. */
    clearApiOverride() {
      localStorage.removeItem('taskflow_api_override');
      console.log('[Config] API override cleared');
    },

    /** Non-blocking connectivity test — logs result to console. */
    async testConnection() {
      const apiBase = this.getApiBase();
      try {
        const res  = await fetch(`${apiBase}/health`, { method: 'GET' });
        const data = res.ok ? await res.json() : null;
        if (res.ok) {
          console.log('[Config] ✅ Backend reachable at', apiBase, data);
          return { success: true, apiBase, data };
        }
        console.warn('[Config] ⚠️ Backend returned HTTP', res.status, 'at', apiBase);
        return { success: false, apiBase, error: `HTTP ${res.status}` };
      } catch (err) {
        console.error('[Config] ❌ Cannot reach backend at', apiBase, '—', err.message);
        console.log('[Config] 💡 Override with: Config.setApiOverride("http://YOUR_HOST:8000")');
        return { success: false, apiBase, error: err.message };
      }
    },
  };

  // Expose globally
  window.Config = Config;

  // Non-blocking health check on page load
  window.addEventListener('DOMContentLoaded', () => Config.testConnection());

})(window);

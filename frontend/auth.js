/**
 * auth.js – Authentication utilities for TaskFlow2
 * 
 * Shared by both login.html and index.html
 * Handles JWT storage, retrieval, and automatic injection into fetch requests
 */

(function(window) {
  'use strict';

  const TOKEN_KEY = 'taskflow_token';
  const USER_KEY = 'taskflow_user';

  const Auth = {
    /**
     * Get the stored JWT token
     * @returns {string|null}
     */
    getToken() {
      return localStorage.getItem(TOKEN_KEY);
    },

    /**
     * Store the JWT token
     * @param {string} token
     */
    setToken(token) {
      localStorage.setItem(TOKEN_KEY, token);
    },

    /**
     * Clear the stored token
     */
    clearToken() {
      localStorage.removeItem(TOKEN_KEY);
    },

    /**
     * Get the cached user profile
     * @returns {object|null}
     */
    getUser() {
      try {
        const raw = localStorage.getItem(USER_KEY);
        return raw ? JSON.parse(raw) : null;
      } catch (e) {
        return null;
      }
    },

    /**
     * Store the user profile
     * @param {object} user
     */
    setUser(user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    },

    /**
     * Clear the cached user profile
     */
    clearUser() {
      localStorage.removeItem(USER_KEY);
    },

    /**
     * Check if user is logged in (has a token)
     * @returns {boolean}
     */
    isLoggedIn() {
      return !!this.getToken();
    },

    /**
     * Guard a page – redirect to login if not authenticated
     * Call this at the top of index.html's script
     */
    guardPage() {
      if (!this.isLoggedIn()) {
        window.location.href = 'login.html';
      }
    },

    /**
     * Logout – clear storage and redirect to login
     */
    logout() {
      this.clearToken();
      this.clearUser();
      window.location.href = 'login.html';
    },

    /**
     * Fetch wrapper that automatically injects Authorization header
     * If response is 401, automatically logout
     * 
     * @param {string} url
     * @param {object} options - fetch options
     * @returns {Promise<Response>}
     */
    async fetchWithAuth(url, options = {}) {
      const token = this.getToken();
      
      // Build headers
      const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
      };

      // Inject Authorization if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const config = {
        ...options,
        headers,
      };

      try {
        const response = await fetch(url, config);

        // If 401 Unauthorized, token is invalid/expired – logout
        if (response.status === 401) {
          console.warn('Unauthorized (401) – logging out');
          this.logout();
          throw new Error('Session expired. Please log in again.');
        }

        return response;
      } catch (error) {
        // Network error or logout redirect
        throw error;
      }
    },
  };

  // Expose Auth to global scope
  window.Auth = Auth;

})(window);

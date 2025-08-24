import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { csrfApi } from 'src/services/web';

export const useCSRFStore = defineStore('csrf', {
  state: () => ({
    token: null as string | null,
    isInitialized: false,
  }),

  getters: {
    hasToken: (state): boolean => state.token !== null,
  },

  actions: {
    getCsrfTokenFromCookie(): string | null {
      const name = 'csrftoken';
      if (!document.cookie) return null;

      const cookies = document.cookie.split(';');
      for (const cookie of cookies) {
        const trimmed = cookie.trim();
        if (trimmed.startsWith(`${name}=`)) {
          return decodeURIComponent(trimmed.substring(name.length + 1));
        }
      }
      return null;
    },

    async fetchToken(): Promise<void> {
      try {
        // Try cookie first
        let token = this.getCsrfTokenFromCookie();

        if (!token) {
          // Make request to get CSRF token
          const response = await csrfApi.getToken();
          token = response.data.csrfToken || this.getCsrfTokenFromCookie();
        }

        this.token = token;
      } catch (error) {
        console.warn('Failed to fetch CSRF token:', error);
      }
    },

    setupInterceptor(): void {
      if (this.isInitialized) return;

      api.interceptors.request.use(async (config) => {
        const method = config.method?.toLowerCase();
        if (['post', 'put', 'patch', 'delete'].includes(method || '')) {
          if (!this.token) {
            await this.fetchToken();
          }
          if (this.token) {
            config.headers['X-CSRFToken'] = this.token;
          }
        }
        return config;
      });

      this.isInitialized = true;
    },

    async initialize(): Promise<void> {
      this.setupInterceptor();
      await this.fetchToken();
    },
  },
});

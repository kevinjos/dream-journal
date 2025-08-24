import { defineStore, acceptHMRUpdate } from 'pinia';
import { api } from 'boot/axios';
import { authApi } from 'src/services/web';

interface User {
  pk: number;
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
}

interface LoginCredentials {
  username: string;
  password: string;
}

interface RegisterCredentials {
  username: string;
  email: string;
  password1: string;
  password2: string;
}

interface ApiError {
  response?: {
    status?: number;
    data?: Record<string, string | string[]> & { detail?: string };
  };
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    accessToken: localStorage.getItem('access_token'),
    refreshToken: localStorage.getItem('refresh_token'),
    loading: false,
    error: null as string | null,
    refreshPromise: null as Promise<boolean> | null, // Track ongoing refresh
    initialized: false, // Track if auth store has been initialized
  }),

  getters: {
    isAuthenticated: (state): boolean => state.accessToken !== null && state.user !== null,
  },

  actions: {
    setTokens(access: string, refresh: string): void {
      this.accessToken = access;
      this.refreshToken = refresh;
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      // Set default authorization header
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
    },

    formatApiError(apiError: ApiError): string {
      // Handle different error types
      if (apiError.response?.status === 404) {
        return 'Server endpoint not found. Please try again later.';
      } else if (apiError.response?.status === 500) {
        return 'Server error. Please try again later.';
      } else if (apiError.response?.data) {
        // Handle field-specific errors from the API
        const errorData = apiError.response.data;
        const errors: string[] = [];

        // Check for detail field first (common in DRF)
        if (errorData.detail) {
          errors.push(String(errorData.detail));
        } else {
          // Handle field-specific errors
          for (const [, messages] of Object.entries(errorData)) {
            if (Array.isArray(messages)) {
              errors.push(...messages);
            } else if (messages) {
              errors.push(String(messages));
            }
          }
        }

        return errors.length > 0 ? errors.join('. ') : 'Request failed';
      } else {
        return 'Unable to connect to server. Please check your connection.';
      }
    },

    clearAuth(): void {
      this.user = null;
      this.accessToken = null;
      this.refreshToken = null;
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      delete api.defaults.headers.common['Authorization'];
    },

    async login(credentials: LoginCredentials): Promise<{ success: boolean; error?: string }> {
      this.loading = true;
      this.error = null;

      try {
        const response = await authApi.login(credentials);
        const { access, refresh, user } = response.data;

        this.setTokens(access, refresh);
        this.user = user;

        return { success: true };
      } catch (err) {
        const apiError = err as ApiError;
        this.error = this.formatApiError(apiError);
        return { success: false, error: this.error };
      } finally {
        this.loading = false;
      }
    },

    async register(
      credentials: RegisterCredentials,
    ): Promise<{ success: boolean; error?: string }> {
      this.loading = true;
      this.error = null;

      try {
        const response = await authApi.register(credentials);
        const { access, refresh, user } = response.data;

        this.setTokens(access, refresh);
        this.user = user;

        return { success: true };
      } catch (err) {
        const apiError = err as ApiError;
        this.error = this.formatApiError(apiError);
        return { success: false, error: this.error };
      } finally {
        this.loading = false;
      }
    },

    async logout(): Promise<void> {
      this.loading = true;

      try {
        await authApi.logout();
      } catch {
        console.warn('Logout request failed, but clearing local auth anyway');
      } finally {
        this.clearAuth();
        this.loading = false;
      }
    },

    async fetchUser(): Promise<void> {
      if (!this.accessToken) return;

      try {
        const response = await authApi.getUser();
        this.user = response.data;
      } catch {
        // Don't clear auth here - let the axios interceptor handle token refresh
        // If the interceptor can't fix it, it will clear auth
      }
    },

    async refreshAccessToken(): Promise<boolean> {
      // If refresh is already in progress, wait for it
      if (this.refreshPromise) {
        return await this.refreshPromise;
      }

      if (!this.refreshToken) {
        this.clearAuth();
        return false;
      }

      // Create and store the refresh promise to prevent concurrent refreshes
      this.refreshPromise = this._performRefresh();
      const result = await this.refreshPromise;
      this.refreshPromise = null; // Clear the promise when done

      return result;
    },

    async _performRefresh(): Promise<boolean> {
      try {
        const response = await authApi.refreshToken(this.refreshToken!);
        const { access, refresh } = response.data;

        // Update access token
        this.accessToken = access;
        localStorage.setItem('access_token', access);
        api.defaults.headers.common['Authorization'] = `Bearer ${access}`;

        // Update refresh token if a new one was provided (token rotation)
        if (refresh) {
          this.refreshToken = refresh;
          localStorage.setItem('refresh_token', refresh);
        }

        return true;
      } catch {
        this.clearAuth();
        return false;
      }
    },

    // Initialize auth on store creation
    async init(): Promise<void> {
      if (this.initialized) {
        return;
      }

      this.initialized = true;

      if (this.accessToken) {
        api.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`;
        await this.fetchUser();
      }
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot));
}

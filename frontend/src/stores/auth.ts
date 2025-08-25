import { defineStore, acceptHMRUpdate } from 'pinia';
import { LocalStorage } from 'quasar';

interface User {
  pk: number;
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    accessToken: LocalStorage.getItem('access_token'),
    refreshToken: LocalStorage.getItem('refresh_token'),
    isInitialized: false,
    isInitializing: false,
  }),

  getters: {
    isAuthenticated: (state): boolean => !!(state.accessToken && state.user),
    currentUser: (state): User | null => state.user,
    username: (state): string => state.user?.username || '',
    email: (state): string => state.user?.email || '',
  },

  actions: {
    setUser(user: User | null): void {
      this.user = user;
    },

    setTokens(access: string, refresh: string): void {
      this.accessToken = access;
      this.refreshToken = refresh;
      LocalStorage.set('access_token', access);
      LocalStorage.set('refresh_token', refresh);
    },

    setAccessToken(access: string): void {
      this.accessToken = access;
      LocalStorage.set('access_token', access);
    },

    setRefreshToken(refresh: string): void {
      this.refreshToken = refresh;
      LocalStorage.set('refresh_token', refresh);
    },

    clearAuth(): void {
      this.user = null;
      this.accessToken = null;
      this.refreshToken = null;
      LocalStorage.remove('access_token');
      LocalStorage.remove('refresh_token');
      this.resetInitialization();
    },

    hasToken(): boolean {
      return !!this.accessToken;
    },

    async initializeAuth(): Promise<void> {
      if (this.isInitialized || this.isInitializing) {
        return;
      }

      this.isInitializing = true;

      try {
        if (this.accessToken) {
          // Set authorization header
          const { api } = await import('boot/axios');
          api.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`;

          // Fetch user data
          try {
            const { authApi } = await import('src/services/web');
            const response = await authApi.getUser();
            this.setUser(response.data);
          } catch {
            // Don't clear auth here - let the axios interceptor handle token refresh
          }
        }
      } finally {
        this.isInitialized = true;
        this.isInitializing = false;
      }
    },

    resetInitialization(): void {
      this.isInitialized = false;
      this.isInitializing = false;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot));
}

import { defineBoot } from '#q-app/wrappers';
import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios';

declare module 'vue' {
  interface ComponentCustomProperties {
    $axios: AxiosInstance;
    $api: AxiosInstance;
  }
}

// Extend Axios config to include retry flag
interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

// Be careful when using SSR for cross-request state pollution
// due to creating a Singleton instance here;
// If any client changes this (global) instance, it might be a
// good idea to move this instance creation inside of the
// "export default () => {}" function below (which runs individually
// for each client)
// Use relative URL for production, localhost for development
const baseURL = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8081/api';
const api = axios.create({ baseURL });

// Track requests being retried to prevent infinite loops
const isRetryRequest = (config: RetryableRequestConfig): boolean => {
  return !!config._retry;
};

const setRetryFlag = (config: InternalAxiosRequestConfig): RetryableRequestConfig => {
  return { ...config, _retry: true };
};

export default defineBoot(({ app }) => {
  // Set up response interceptor for automatic token refresh
  api.interceptors.response.use(
    (response) => response, // Pass successful responses through
    async (error: AxiosError) => {
      const originalRequest = error.config as RetryableRequestConfig;

      // Check if this is a 401 error and not already a retry attempt
      if (error.response?.status === 401 && originalRequest && !isRetryRequest(originalRequest)) {
        // Import auth store directly instead of composable to avoid Vue context issues
        const { useAuthStore } = await import('src/stores/auth');
        const authStore = useAuthStore();

        if (!authStore.refreshToken) {
          authStore.clearAuth();
          return Promise.reject(error);
        }

        try {
          // Perform token refresh directly using the API
          const { authApi } = await import('src/services/web');
          const response = await authApi.refreshToken(authStore.refreshToken);
          const { access, refresh } = response.data;

          // Update tokens in store
          authStore.setAccessToken(access);
          if (refresh) {
            authStore.setRefreshToken(refresh);
          }

          // Update axios default header
          api.defaults.headers.common['Authorization'] = `Bearer ${access}`;

          // Retry the original request with new token
          const retryConfig = setRetryFlag(originalRequest);
          retryConfig.headers = retryConfig.headers || {};
          retryConfig.headers['Authorization'] = `Bearer ${access}`;

          return api.request(retryConfig);
        } catch {
          // Refresh failed, clear auth and redirect
          authStore.clearAuth();
          delete api.defaults.headers.common['Authorization'];

          // Only redirect if we're in browser context
          if (typeof window !== 'undefined') {
            const { useRouter } = await import('vue-router');
            try {
              const router = useRouter();
              void router.push('/auth/login');
            } catch {
              // If router is not available, use location
              window.location.href = '/auth/login';
            }
          }
        }
      }

      // For all other errors or failed refresh, reject the promise
      return Promise.reject(error);
    },
  );

  // for use inside Vue files (Options API) through this.$axios and this.$api
  app.config.globalProperties.$axios = axios;
  // ^ ^ ^ this will allow you to use this.$axios (for Vue Options API form)
  //       so you won't necessarily have to import axios in each vue file

  app.config.globalProperties.$api = api;
  // ^ ^ ^ this will allow you to use this.$api (for Vue Options API form)
  //       so you can easily perform requests against your app's API
});

export { api };

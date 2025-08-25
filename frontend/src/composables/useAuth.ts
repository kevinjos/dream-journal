import { useAuthStore } from 'stores/auth';
import { authApi } from 'src/services/web';
import { api } from 'boot/axios';
import { formatApiError, type ApiError } from 'src/utils/errorHandling';

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

export function useAuth() {
  const authStore = useAuthStore();

  const login = async (
    credentials: LoginCredentials,
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await authApi.login(credentials);
      const { access, refresh, user } = response.data;

      authStore.setTokens(access, refresh);
      authStore.setUser(user);

      // Set default authorization header
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`;

      return { success: true };
    } catch (err) {
      const error = formatApiError(err as ApiError);
      return { success: false, error };
    }
  };

  const register = async (
    credentials: RegisterCredentials,
  ): Promise<{
    success: boolean;
    error?: string;
    requiresVerification?: boolean;
    message?: string;
  }> => {
    try {
      const response = await authApi.register(credentials);

      // Check status code and response structure
      if (response.status === 201 && response.data.detail) {
        // Email verification required - 201 with detail message
        return {
          success: true,
          requiresVerification: true,
          message: response.data.detail,
        };
      } else if (response.status === 200 && response.data.access && response.data.refresh) {
        // Normal registration with immediate login - 200 with tokens
        const { access, refresh, user } = response.data;
        authStore.setTokens(access, refresh);
        authStore.setUser(user);

        // Set default authorization header
        api.defaults.headers.common['Authorization'] = `Bearer ${access}`;

        return { success: true, requiresVerification: false };
      } else {
        // Unexpected response format - fail explicitly
        return {
          success: false,
          error: `Unexpected response format (status: ${response.status})`,
        };
      }
    } catch (err) {
      const error = formatApiError(err as ApiError);
      return { success: false, error };
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authApi.logout();
    } catch {
      console.warn('Logout request failed, but clearing local auth anyway');
    } finally {
      authStore.clearAuth();
      delete api.defaults.headers.common['Authorization'];
    }
  };

  const fetchUser = async (): Promise<void> => {
    if (!authStore.accessToken) return;

    try {
      const response = await authApi.getUser();
      authStore.setUser(response.data);
    } catch {
      // Don't clear auth here - let the axios interceptor handle token refresh
      // If the interceptor can't fix it, it will clear auth
    }
  };

  const initAuth = async (): Promise<void> => {
    // This method is mainly for component-level initialization
    // Router-level initialization is handled directly in the router guard
    if (authStore.accessToken) {
      api.defaults.headers.common['Authorization'] = `Bearer ${authStore.accessToken}`;
      await fetchUser();
    }
  };

  return {
    login,
    register,
    logout,
    fetchUser,
    initAuth,
    // Expose getters
    isAuthenticated: () => authStore.isAuthenticated,
    user: () => authStore.user,
  };
}

import { authApi } from 'src/services/web';
import { formatApiError, type ApiError } from 'src/utils/errorHandling';

interface PasswordResetConfirmCredentials {
  uid: string;
  token: string;
  new_password1: string;
  new_password2: string;
}

export function usePasswordReset() {
  const resetPassword = async (email: string): Promise<{ success: boolean; error?: string }> => {
    try {
      await authApi.resetPassword(email);
      return { success: true };
    } catch (err) {
      const error = formatApiError(err as ApiError);
      return { success: false, error };
    }
  };

  const resetPasswordConfirm = async (
    credentials: PasswordResetConfirmCredentials,
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      await authApi.resetPasswordConfirm(credentials);
      return { success: true };
    } catch (err) {
      const error = formatApiError(err as ApiError);
      return { success: false, error };
    }
  };

  return {
    resetPassword,
    resetPasswordConfirm,
  };
}

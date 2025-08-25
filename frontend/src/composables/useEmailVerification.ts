import { authApi } from 'src/services/web';
import { formatApiError, type ApiError } from 'src/utils/errorHandling';

export function useEmailVerification() {
  const verifyEmail = async (key: string): Promise<{ success: boolean; error?: string }> => {
    try {
      await authApi.verifyEmail(key);
      return { success: true };
    } catch (err) {
      const error = formatApiError(err as ApiError);
      return { success: false, error };
    }
  };

  const resendEmailVerification = async (data: {
    email?: string;
    username?: string;
  }): Promise<{ success: boolean; error?: string }> => {
    try {
      await authApi.resendEmailVerification(data);
      return { success: true };
    } catch (err) {
      const error = formatApiError(err as ApiError);
      return { success: false, error };
    }
  };

  return {
    verifyEmail,
    resendEmailVerification,
  };
}

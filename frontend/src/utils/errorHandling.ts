export interface ApiError {
  response?: {
    status?: number;
    data?: Record<string, string | string[]> & {
      detail?: string;
      email_verification_required?: boolean;
      can_resend?: boolean;
      email?: string;
    };
  };
}

export interface AuthErrorData {
  detail?: string;
  email_verification_required?: boolean;
  can_resend?: boolean;
  email?: string | string[];
  non_field_errors?: string[];
  password?: string[];
  username?: string[];
}

export interface AuthError {
  response?: {
    status?: number;
    data?: AuthErrorData;
  };
}

export function formatAuthError(authError: AuthError): {
  message: string;
  requiresEmailVerification?: boolean | undefined;
  canResend?: boolean | undefined;
  email?: string | undefined;
} {
  const data = authError.response?.data;

  // Handle authentication-specific errors
  if (data?.email_verification_required) {
    return {
      message: data.detail || 'Email verification is required before you can log in.',
      requiresEmailVerification: true,
      canResend: data.can_resend ?? false,
      email: typeof data.email === 'string' ? data.email : undefined,
    };
  }

  // Handle rate limiting for auth endpoints
  if (authError.response?.status === 429) {
    return {
      message: 'Too many attempts. Please wait a moment and try again.',
    };
  }

  // Handle validation errors for authentication
  if (authError.response?.status === 400 && data) {
    const errors: string[] = [];

    // Handle specific auth field errors with context
    if (data.email) {
      if (Array.isArray(data.email)) {
        errors.push(...data.email.map((msg) => `Email: ${msg}`));
      } else if (typeof data.email === 'string') {
        // Handle case where email is the user's email address (not an error message)
        // This is likely not an error message, so skip it
      }
    }
    if (data.password && Array.isArray(data.password)) {
      errors.push(...data.password.map((msg) => `Password: ${msg}`));
    }
    if (data.username && Array.isArray(data.username)) {
      errors.push(...data.username.map((msg) => `Username: ${msg}`));
    }
    if (data.non_field_errors && Array.isArray(data.non_field_errors)) {
      errors.push(...data.non_field_errors);
    }
    if (data.detail) {
      errors.push(data.detail);
    }

    if (errors.length > 0) {
      return { message: errors.join('. ') };
    }
  }

  // Handle unauthorized access
  if (authError.response?.status === 401) {
    return {
      message: 'Invalid credentials. Please check your email and password.',
    };
  }

  // Fall back to general API error handling
  return { message: formatApiError(authError as ApiError) };
}

export function formatApiError(apiError: ApiError): string {
  if (apiError.response?.status === 404) {
    return 'Server endpoint not found. Please try again later.';
  } else if (apiError.response?.status === 500) {
    return 'Server error. Please try again later.';
  } else if (apiError.response?.status === 503) {
    return 'Service temporarily unavailable. Please try again later.';
  } else if (apiError.response?.data) {
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
}

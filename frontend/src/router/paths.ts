/**
 * Centralized route paths for the application.
 * Use these constants instead of hardcoding paths throughout components.
 */

// Auth routes
export const AUTH_ROUTES = {
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  PASSWORD_RESET: '/auth/password-reset',
  PASSWORD_RESET_CONFIRM: (uid: string, token: string) =>
    `/auth/password-reset/confirm/${uid}/${token}`,
  EMAIL_VERIFICATION: '/auth/email-verification',
  EMAIL_VERIFICATION_CONFIRM: (key: string) => `/auth/email-verification/confirm/${key}`,
} as const;

// Main app routes
export const APP_ROUTES = {
  HOME: '/',
  DREAMS_LIST: '/dreams',
  DREAMS_CREATE: '/dreams/create',
  DREAMS_EDIT: (id: string | number) => `/dreams/${id}/edit`,
  QUALITIES: '/qualities',
} as const;

// Helper function to build route with query params
export function withQuery(
  path: string,
  query: Record<string, string | undefined>,
): { path: string; query: Record<string, string> } {
  const filteredQuery: Record<string, string> = {};
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined) {
      filteredQuery[key] = value;
    }
  }
  return { path, query: filteredQuery };
}

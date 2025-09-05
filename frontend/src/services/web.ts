import { api } from 'boot/axios';
import type { Dream, Quality } from 'src/types/models';

// Auth API calls
export const authApi = {
  login: (credentials: { username: string; password: string }) =>
    api.post('/auth/login/', credentials),

  register: (credentials: {
    username: string;
    email: string;
    password1: string;
    password2: string;
  }) => api.post('/auth/registration/', credentials),

  logout: () => api.post('/auth/logout/'),

  getUser: () => api.get('/auth/user/'),

  refreshToken: (refreshToken: string) =>
    api.post('/auth/token/refresh/', { refresh: refreshToken }),

  resetPassword: (email: string) => api.post('/auth/password/reset/', { email }),

  resetPasswordConfirm: (data: {
    uid: string;
    token: string;
    new_password1: string;
    new_password2: string;
  }) => api.post('/auth/password/reset/confirm/', data),

  verifyEmail: (key: string) => api.post('/auth/registration/verify-email/', { key }),

  resendEmailVerification: (data: { email?: string; username?: string }) =>
    api.post('/auth/registration/resend-email/', data),
};

// Dreams API calls
export const dreamsApi = {
  list: (params?: URLSearchParams) => {
    const url = `/dreams/${params?.toString() ? '?' + params.toString() : ''}`;
    return api.get(url);
  },

  get: (id: string | number) => api.get<Dream>(`/dreams/${id}/`),

  create: (dream: Partial<Dream>) => api.post('/dreams/', dream),

  update: (id: string | number, dream: Partial<Dream>) => api.patch(`/dreams/${id}/`, dream),

  delete: (id: string | number) => api.delete(`/dreams/${id}/`),

  // Image generation APIs
  generateImage: (id: string | number) => api.post(`/dreams/${id}/generate_image/`),

  alterImage: (dreamId: string | number, imageId: string | number, prompt: string) =>
    api.post(`/dreams/${dreamId}/alter_image/${imageId}/`, { prompt }),

  getImages: (id: string | number) => api.get(`/dreams/${id}/images/`),

  getImage: (dreamId: string | number, imageId: string | number) =>
    api.get(`/dreams/${dreamId}/images/${imageId}/`),

  // Astral Plane API for public dreams
  getAstralPlane: (params?: string) => {
    const url = `/dreams/astral_plane/${params ? '?' + params : ''}`;
    return api.get(url);
  },
};

// Qualities API calls
export const qualitiesApi = {
  list: () => api.get('/qualities/'),

  get: (id: string | number) => api.get<Quality>(`/qualities/${id}/`),

  create: (quality: Partial<Quality>) => api.post('/qualities/', quality),

  update: (id: string | number, quality: Partial<Quality>) => api.put(`/qualities/${id}/`, quality),

  delete: (id: string | number) => api.delete(`/qualities/${id}/`),
};

// Nested dream-quality API calls
export const dreamQualitiesApi = {
  list: (dreamId: string | number) => api.get(`/dreams/${dreamId}/qualities/`),

  update: (dreamId: string | number, qualityId: string | number, data: unknown) =>
    api.put(`/dreams/${dreamId}/qualities/${qualityId}/`, data),

  delete: (dreamId: string | number, qualityId: string | number) =>
    api.delete(`/dreams/${dreamId}/qualities/${qualityId}/`),
};

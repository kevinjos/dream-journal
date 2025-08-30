import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  // Auth routes (minimal layout)
  {
    path: '/auth',
    component: () => import('layouts/AuthLayout.vue'),
    children: [
      { path: 'login', component: () => import('pages/LoginPage.vue') },
      { path: 'register', component: () => import('pages/RegisterPage.vue') },
      { path: 'password-reset', component: () => import('pages/PasswordResetPage.vue') },
      {
        path: 'password-reset/confirm/:uid/:token',
        component: () => import('pages/PasswordResetConfirmPage.vue'),
      },
      { path: 'email-verification', component: () => import('pages/EmailVerificationPage.vue') },
      {
        path: 'email-verification/confirm/:key',
        component: () => import('pages/EmailVerificationConfirmPage.vue'),
      },
    ],
  },

  // Main app routes (with layout)
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/HomePage.vue') },
      { path: 'dreams', component: () => import('pages/DreamsListPage.vue') },
      { path: 'dreams/create', component: () => import('pages/CreateDreamPage.vue') },
      { path: 'dreams/:id/edit', component: () => import('pages/EditDreamPage.vue') },
      { path: 'qualities', component: () => import('pages/QualityMapPage.vue') },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;

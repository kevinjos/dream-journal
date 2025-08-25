import { defineRouter } from '#q-app/wrappers';
import {
  createMemoryHistory,
  createRouter,
  createWebHashHistory,
  createWebHistory,
} from 'vue-router';
import routes from './routes';

/*
 * If not building with SSR mode, you can
 * directly export the Router instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Router instance.
 */

export default defineRouter(function ({ store }) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : process.env.VUE_ROUTER_MODE === 'history'
      ? createWebHistory
      : createWebHashHistory;

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(process.env.VUE_ROUTER_BASE),
  });

  // Navigation guards
  Router.beforeEach(async (to) => {
    // Import auth store inside the guard to avoid circular imports
    const { useAuthStore } = await import('stores/auth');
    const authStore = useAuthStore(store);

    // Initialize auth on first navigation using Pinia state
    await authStore.initializeAuth();

    // Check if route requires authentication
    const isAuthRoute = to.path.startsWith('/auth');
    const isPublicAuthRoute =
      to.path.startsWith('/auth/login') ||
      to.path.startsWith('/auth/register') ||
      to.path.startsWith('/auth/password-reset') ||
      to.path.startsWith('/auth/email-verification');
    const isAuthenticated = authStore.isAuthenticated;

    if (!isAuthRoute && !isAuthenticated) {
      // Redirect to login if accessing protected route while unauthenticated
      return '/auth/login';
    } else if (isAuthRoute && isAuthenticated && isPublicAuthRoute) {
      // Redirect to home if accessing public auth routes while authenticated
      return '/';
    }
    // Allow navigation (no explicit return needed)
  });

  return Router;
});

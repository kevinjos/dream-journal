import { boot } from 'quasar/wrappers';
import { useCSRFStore } from 'src/stores/csrf';

// Boot file for CSRF initialization
export default boot(async () => {
  const csrfStore = useCSRFStore();

  // Initialize CSRF protection (sets up axios interceptor)
  await csrfStore.initialize();
});

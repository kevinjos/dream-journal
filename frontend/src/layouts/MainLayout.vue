<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />

        <q-toolbar-title></q-toolbar-title>

        <q-space />

        <q-btn
          flat
          dense
          round
          :icon="themeStore.isDark ? 'light_mode' : 'dark_mode'"
          :aria-label="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          @click="toggleTheme"
          class="q-mr-sm"
        />

        <q-btn flat dense round icon="logout" aria-label="Logout" @click="onLogout" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list>
        <q-item-label header>Navigation</q-item-label>

        <q-item clickable v-ripple @click="navigateTo('/')">
          <q-item-section avatar>
            <q-icon name="home" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Dashboard</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable v-ripple @click="navigateTo('/dreams')">
          <q-item-section avatar>
            <q-icon name="bedtime" />
          </q-item-section>
          <q-item-section>
            <q-item-label>My Dreams</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable v-ripple @click="navigateTo('/dreams/create')">
          <q-item-section avatar>
            <q-icon name="add" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Record Dream</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable v-ripple @click="navigateTo('/qualities')">
          <q-item-section avatar>
            <q-icon name="cloud" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Dream Cloud</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from 'stores/auth';
import { useThemeStore } from 'stores/theme';

const router = useRouter();
const $q = useQuasar();
const authStore = useAuthStore();
const themeStore = useThemeStore();

const leftDrawerOpen = ref<boolean>(false);

function toggleLeftDrawer(): void {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

function navigateTo(path: string): void {
  void router.push(path);
}

function toggleTheme(): void {
  themeStore.toggleTheme();
  $q.dark.set(themeStore.isDark);
}

const onLogout = async (): Promise<void> => {
  await authStore.logout();
  $q.notify({
    type: 'info',
    message: 'You have been logged out',
    position: 'top',
  });
  void router.push('/auth/login');
};

// Initialize theme on component mount
onMounted(() => {
  $q.dark.set(themeStore.isDark);
});
</script>

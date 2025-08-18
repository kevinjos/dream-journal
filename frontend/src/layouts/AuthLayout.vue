<template>
  <q-layout view="lHh Lpr lFf">
    <q-header class="bg-transparent" style="box-shadow: none;">
      <q-toolbar>
        <q-space />
        <q-btn
          flat
          dense
          round
          :icon="themeStore.isDark ? 'light_mode' : 'dark_mode'"
          :aria-label="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          @click="toggleTheme"
          class="text-grey-6"
        />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useThemeStore } from 'stores/theme'

const $q = useQuasar()
const themeStore = useThemeStore()

function toggleTheme(): void {
  themeStore.toggleTheme()
  $q.dark.set(themeStore.isDark)
}

// Initialize theme on component mount
onMounted(() => {
  $q.dark.set(themeStore.isDark)
})
</script>
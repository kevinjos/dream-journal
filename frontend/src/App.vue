<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from 'stores/auth'

const authStore = useAuthStore()

// Initialize auth store on app startup to restore session from localStorage
onMounted(async () => {
  await authStore.init()
})
</script>

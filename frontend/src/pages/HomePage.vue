<template>
  <q-page class="flex flex-center">
    <div class="column items-center q-gutter-md">
      <div class="text-h4">Welcome to Dream Journal</div>
      <div class="text-subtitle1 text-grey-6">
        Hello {{ authStore.user?.username }}!
      </div>
      
      <div class="q-mt-lg text-center text-grey-6">
        <p>Dream tracking features coming soon...</p>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useAuthStore } from 'stores/auth'

const authStore = useAuthStore()
</script>
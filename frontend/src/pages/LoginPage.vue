<template>
  <q-page class="flex flex-center">
    <q-card class="q-pa-lg" style="min-width: 400px">
      <q-card-section>
        <div class="text-h6 text-center q-mb-md">Dream Journal</div>
        <div class="text-subtitle2 text-center text-grey-6 q-mb-lg">Sign in to your account</div>

        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input
            v-model="username"
            type="text"
            label="Username"
            outlined
            lazy-rules
            :rules="[(val) => !!val || 'Username is required']"
            autocomplete="username"
          />

          <q-input
            v-model="password"
            type="password"
            label="Password"
            outlined
            lazy-rules
            :rules="[(val) => !!val || 'Password is required']"
            autocomplete="current-password"
          />

          <div v-if="authStore.error" class="text-negative q-mb-md">
            {{ authStore.error }}
          </div>

          <q-btn
            type="submit"
            color="primary"
            class="full-width"
            :loading="authStore.loading"
            :disable="authStore.loading"
          >
            Sign In
          </q-btn>
        </q-form>

        <div class="text-center q-mt-lg">
          <span class="text-grey-6">Don't have an account? </span>
          <q-btn flat dense color="primary" @click="$router.push('/auth/register')">
            Sign up
          </q-btn>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from 'stores/auth';

const router = useRouter();
const $q = useQuasar();
const authStore = useAuthStore();

const username = ref<string>('');
const password = ref<string>('');

const onSubmit = async (): Promise<void> => {
  const result = await authStore.login({
    username: username.value,
    password: password.value,
  });

  if (result.success) {
    $q.notify({
      type: 'positive',
      message: 'Welcome back!',
      position: 'top',
    });
    void router.push('/');
  }
};
</script>

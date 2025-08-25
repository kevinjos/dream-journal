<template>
  <q-page class="flex flex-center q-pa-sm q-pa-md-md">
    <q-card class="q-pa-md q-pa-lg-md col-12 col-sm-8 col-md-6 col-lg-4" style="max-width: 400px">
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

          <div v-if="error" class="text-negative q-mb-md">
            {{ error }}
          </div>

          <q-btn
            type="submit"
            color="primary"
            class="full-width"
            :loading="loading"
            :disable="loading"
          >
            Sign In
          </q-btn>
        </q-form>

        <div class="text-center q-mt-md">
          <q-btn flat dense color="primary" @click="$router.push('/auth/password-reset')">
            Forgot your password?
          </q-btn>
        </div>

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
import { useAuth } from 'src/composables/useAuth';

const router = useRouter();
const $q = useQuasar();
const { login } = useAuth();

const username = ref<string>('');
const password = ref<string>('');
const loading = ref<boolean>(false);
const error = ref<string | null>(null);

const onSubmit = async (): Promise<void> => {
  loading.value = true;
  error.value = null;

  const result = await login({
    username: username.value,
    password: password.value,
  });

  loading.value = false;

  if (result.success) {
    $q.notify({
      type: 'positive',
      message: 'Welcome back!',
      position: 'top',
    });
    void router.push('/');
  } else if (result.error) {
    error.value = result.error;
  }
};
</script>

<template>
  <q-page class="flex flex-center q-pa-sm q-pa-md-md">
    <q-card class="q-pa-md q-pa-lg-md col-12 col-sm-8 col-md-6 col-lg-4" style="max-width: 400px">
      <q-card-section>
        <div class="text-h6 text-center q-mb-md">Reset Password</div>
        <div class="text-subtitle2 text-center text-grey-6 q-mb-lg">
          Enter your email to reset your password
        </div>

        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input
            v-model="email"
            type="email"
            label="Email"
            outlined
            lazy-rules
            :rules="[(val) => !!val || 'Email is required']"
            autocomplete="email"
          />

          <div v-if="error" class="text-negative q-mb-md">
            {{ error }}
          </div>

          <div v-if="success" class="text-positive q-mb-md">
            {{ success }}
          </div>

          <q-btn
            type="submit"
            color="primary"
            class="full-width"
            :loading="loading"
            :disable="loading"
          >
            Send Reset Email
          </q-btn>
        </q-form>

        <div class="text-center q-mt-lg">
          <span class="text-grey-6">Remember your password? </span>
          <q-btn flat dense color="primary" @click="$router.push('/auth/login')"> Sign in </q-btn>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { usePasswordReset } from 'src/composables/usePasswordReset';

const { resetPassword } = usePasswordReset();

const email = ref<string>('');
const error = ref<string | null>(null);
const success = ref<string | null>(null);
const loading = ref<boolean>(false);

const onSubmit = async (): Promise<void> => {
  loading.value = true;
  error.value = null;
  success.value = null;

  const result = await resetPassword(email.value);

  if (result.success) {
    success.value = 'Password reset email sent. Check your inbox for further instructions.';
    email.value = '';
  } else {
    error.value = result.error || 'Password reset failed. Please try again.';
  }

  loading.value = false;
};
</script>

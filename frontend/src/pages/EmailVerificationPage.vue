<template>
  <q-page class="flex flex-center q-pa-sm q-pa-md-md">
    <q-card class="q-pa-md q-pa-lg-md col-12 col-sm-8 col-md-6 col-lg-4" style="max-width: 400px">
      <q-card-section>
        <div class="text-h6 text-center q-mb-md">Email Verification Required</div>
        <div class="text-subtitle2 text-center text-grey-6 q-mb-lg">
          Please check your email and click the verification link to complete your registration.
        </div>

        <div class="text-center q-mb-lg">
          <q-icon name="email" color="primary" size="64px" />
        </div>

        <div v-if="error" class="text-negative q-mb-md text-center">
          {{ error }}
        </div>

        <div v-if="success" class="text-positive q-mb-md text-center">
          {{ success }}
        </div>

        <q-btn
          color="primary"
          class="full-width q-mb-md"
          :loading="loading"
          :disable="loading"
          @click="resendVerification"
        >
          Resend Verification Email
        </q-btn>

        <div class="text-center q-mt-lg">
          <span class="text-grey-6">Already verified? </span>
          <q-btn flat dense color="primary" @click="$router.push('/auth/login')"> Sign in </q-btn>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useEmailVerification } from 'src/composables/useEmailVerification';

const { resendEmailVerification } = useEmailVerification();

const error = ref<string | null>(null);
const success = ref<string | null>(null);
const loading = ref<boolean>(false);

const resendVerification = async (): Promise<void> => {
  loading.value = true;
  error.value = null;
  success.value = null;

  const result = await resendEmailVerification();

  if (result.success) {
    success.value = 'Verification email sent! Check your inbox.';
  } else {
    error.value = result.error || 'Failed to send verification email. Please try again.';
  }

  loading.value = false;
};
</script>

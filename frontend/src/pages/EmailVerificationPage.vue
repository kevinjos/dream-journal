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
          <q-btn flat dense color="primary" @click="goToLogin"> Sign in </q-btn>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useEmailVerification } from 'src/composables/useEmailVerification';
import { AUTH_ROUTES } from 'src/router/paths';

const router = useRouter();
const route = useRoute();

const { resendEmailVerification } = useEmailVerification();

const error = ref<string | null>(null);
const success = ref<string | null>(null);
const loading = ref<boolean>(false);

const resendVerification = async (): Promise<void> => {
  loading.value = true;
  error.value = null;
  success.value = null;

  // Get email or username from route query params
  const email = route.query.email as string | undefined;
  const username = route.query.username as string | undefined;

  if (!email && !username) {
    error.value = 'No email or username provided. Please try logging in again.';
    loading.value = false;
    return;
  }

  // Build data object with only defined values
  const data: { email?: string; username?: string } = {};
  if (email) data.email = email;
  if (username) data.username = username;

  const result = await resendEmailVerification(data);

  if (result.success) {
    success.value = 'Verification email sent! Check your inbox.';
  } else {
    error.value = result.error || 'Failed to send verification email. Please try again.';
  }

  loading.value = false;
};

const goToLogin = (): void => {
  void router.push(AUTH_ROUTES.LOGIN);
};
</script>

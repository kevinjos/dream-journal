<template>
  <q-page class="flex flex-center q-pa-sm q-pa-md-md">
    <q-card class="q-pa-md q-pa-lg-md col-12 col-sm-8 col-md-6 col-lg-4" style="max-width: 400px">
      <q-card-section>
        <div v-if="verifying" class="text-center">
          <div class="text-h6 q-mb-md">Verifying Email</div>
          <div class="text-subtitle2 text-grey-6 q-mb-lg">
            Please wait while we verify your email...
          </div>
          <q-spinner-hourglass color="primary" size="48px" />
        </div>

        <div v-else-if="success" class="text-center">
          <div class="text-h6 q-mb-md">Email Verified!</div>
          <div class="text-subtitle2 text-grey-6 q-mb-lg">
            Your email has been successfully verified.
          </div>
          <q-icon name="check_circle" color="positive" size="64px" class="q-mb-md" />
          <q-btn color="primary" class="full-width" @click="$router.push('/auth/login')">
            Continue to Login
          </q-btn>
        </div>

        <div v-else class="text-center">
          <div class="text-h6 q-mb-md">Verification Failed</div>
          <div class="text-subtitle2 text-grey-6 q-mb-lg">
            {{ error || 'Invalid or expired verification link.' }}
          </div>
          <q-icon name="error" color="negative" size="64px" class="q-mb-md" />

          <q-btn
            color="primary"
            class="full-width q-mb-md"
            @click="$router.push('/auth/email-verification')"
          >
            Request New Verification Email
          </q-btn>

          <q-btn flat color="primary" class="full-width" @click="$router.push('/auth/login')">
            Back to Login
          </q-btn>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useEmailVerification } from 'src/composables/useEmailVerification';

const route = useRoute();
const { verifyEmail } = useEmailVerification();

const verifying = ref<boolean>(true);
const success = ref<boolean>(false);
const error = ref<string | null>(null);

onMounted(async () => {
  const key = route.params.key as string;

  if (!key) {
    verifying.value = false;
    error.value = 'Invalid verification link';
    return;
  }

  const result = await verifyEmail(key);

  verifying.value = false;

  if (result.success) {
    success.value = true;
  } else {
    error.value = result.error || null;
  }
});
</script>

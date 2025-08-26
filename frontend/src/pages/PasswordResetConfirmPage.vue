<template>
  <q-page class="flex flex-center q-pa-sm q-pa-md-md">
    <q-card class="q-pa-md q-pa-lg-md col-12 col-sm-8 col-md-6 col-lg-4" style="max-width: 400px">
      <q-card-section>
        <div class="text-h6 text-center q-mb-md">Set New Password</div>
        <div class="text-subtitle2 text-center text-grey-6 q-mb-lg">Enter your new password</div>

        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input
            v-model="password1"
            type="password"
            label="New Password"
            outlined
            lazy-rules
            :rules="[(val) => !!val || 'Password is required']"
            autocomplete="new-password"
          />

          <q-input
            v-model="password2"
            type="password"
            label="Confirm New Password"
            outlined
            lazy-rules
            :rules="[
              (val) => !!val || 'Please confirm your password',
              (val) => val === password1 || 'Passwords do not match',
            ]"
            autocomplete="new-password"
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
            Set Password
          </q-btn>
        </q-form>

        <div class="text-center q-mt-lg">
          <span class="text-grey-6">Remember your password? </span>
          <q-btn flat dense color="primary" @click="goToLogin"> Sign in </q-btn>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { usePasswordReset } from 'src/composables/usePasswordReset';

const route = useRoute();
const router = useRouter();
const $q = useQuasar();
const { resetPasswordConfirm } = usePasswordReset();

const password1 = ref<string>('');
const password2 = ref<string>('');
const error = ref<string | null>(null);
const success = ref<string | null>(null);
const loading = ref<boolean>(false);

const uid = ref<string>('');
const token = ref<string>('');

onMounted(() => {
  uid.value = route.params.uid as string;
  token.value = route.params.token as string;

  if (!uid.value || !token.value) {
    $q.notify({
      type: 'negative',
      message: 'Invalid password reset link',
      position: 'top',
    });
    void router.push('/auth/login');
  }
});

const onSubmit = async (): Promise<void> => {
  loading.value = true;
  error.value = null;
  success.value = null;

  const result = await resetPasswordConfirm({
    uid: uid.value,
    token: token.value,
    new_password1: password1.value,
    new_password2: password2.value,
  });

  if (result.success) {
    success.value = 'Password reset successfully! You can now log in with your new password.';
    $q.notify({
      type: 'positive',
      message: 'Password changed successfully!',
      position: 'top',
    });
    setTimeout(() => {
      void router.push('/auth/login');
    }, 2000);
  } else {
    error.value = result.error || 'Password reset failed. Please try again.';
  }

  loading.value = false;
};

const goToLogin = (): void => {
  void router.push('/auth/login');
};
</script>

<template>
  <q-page class="flex flex-center q-pa-sm q-pa-md-md">
    <q-card class="q-pa-md q-pa-lg-md col-12 col-sm-8 col-md-6 col-lg-4" style="max-width: 400px">
      <q-card-section>
        <div class="text-h6 text-center q-mb-md">Dream Journal</div>
        <div class="text-subtitle2 text-center text-grey-6 q-mb-lg">Create your account</div>

        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input
            v-model="username"
            type="text"
            label="Username"
            outlined
            lazy-rules
            :rules="[
              (val) => !!val || 'Username is required',
              (val) => val.length >= 3 || 'Username must be at least 3 characters',
            ]"
            autocomplete="username"
          />

          <q-input
            v-model="email"
            type="email"
            label="Email"
            outlined
            lazy-rules
            :rules="[
              (val) => !!val || 'Email is required',
              (val) => /.+@.+\..+/.test(val) || 'Please enter a valid email',
            ]"
            autocomplete="email"
          />

          <q-input
            v-model="password1"
            type="password"
            label="Password"
            outlined
            lazy-rules
            :rules="[
              (val) => !!val || 'Password is required',
              (val) => val.length >= 8 || 'Password must be at least 8 characters',
            ]"
            autocomplete="new-password"
            :input-attrs="{
              passwordrules: 'minlength: 8; required: upper; required: lower; required: digit;',
            }"
          />

          <q-input
            v-model="password2"
            type="password"
            label="Confirm Password"
            outlined
            lazy-rules
            :rules="[
              (val) => !!val || 'Please confirm your password',
              (val) => val === password1 || 'Passwords do not match',
            ]"
            autocomplete="new-password"
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
            Create Account
          </q-btn>
        </q-form>

        <div class="text-center q-mt-lg">
          <span class="text-grey-6">Already have an account? </span>
          <q-btn flat dense color="primary" @click="$router.push('/auth/login')"> Sign in </q-btn>
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
const email = ref<string>('');
const password1 = ref<string>('');
const password2 = ref<string>('');

const onSubmit = async (): Promise<void> => {
  const result = await authStore.register({
    username: username.value,
    email: email.value,
    password1: password1.value,
    password2: password2.value,
  });

  if (result.success) {
    $q.notify({
      type: 'positive',
      message: 'Account created successfully! Welcome to Dream Journal.',
      position: 'top',
    });
    void router.push('/');
  }
};
</script>

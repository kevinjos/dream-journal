<template>
  <q-page-sticky position="bottom" :offset="[0, 16]">
    <div class="full-width q-pa-md">
      <q-btn
        type="submit"
        color="primary"
        :label="label"
        unelevated
        :loading="loading"
        :disable="loading || disabled"
        class="full-width"
        size="lg"
        @click="$emit('click')"
      >
        <template v-slot:loading>
          <q-spinner-hourglass class="on-left" />
          {{ loadingText }}
        </template>
      </q-btn>
    </div>
  </q-page-sticky>
</template>

<script setup lang="ts">
interface Props {
  label: string;
  loadingText: string;
  loading?: boolean;
  disabled?: boolean;
}

interface Emits {
  (e: 'click'): void;
}

withDefaults(defineProps<Props>(), {
  loading: false,
  disabled: false,
});

defineEmits<Emits>();
</script>

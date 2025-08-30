<template>
  <!-- Quality Tags Input -->
  <div>
    <q-input
      v-model="qualityInput"
      outlined
      placeholder="Dream qualities"
      @keyup.enter="addQuality"
      class="full-width"
      :autofocus="autoFocus"
    >
      <template v-slot:prepend>
        <q-icon name="new_label" />
      </template>
      <template v-slot:append>
        <q-btn flat round icon="add" @click="addQuality" :disabled="!qualityInput.trim()" />
      </template>
    </q-input>

    <!-- Quality Chips -->
    <div v-if="qualityNames?.length" class="q-mt-sm">
      <q-chip
        v-for="(quality, index) in qualityNames"
        :key="index"
        removable
        @remove="removeQuality(index)"
        color="primary"
        text-color="white"
        class="q-mr-xs q-mb-xs"
      >
        {{ quality }}
      </q-chip>
    </div>
  </div>

  <!-- Description Input -->
  <div>
    <q-input
      v-model="description"
      outlined
      type="textarea"
      rows="8"
      class="full-width"
      placeholder="First person, present tense description"
    >
      <template v-slot:prepend>
        <q-icon name="description" />
      </template>
    </q-input>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  qualityInput: string;
  qualityNames?: string[];
  description: string;
  autoFocus?: boolean;
}

interface Emits {
  (e: 'update:qualityInput', value: string): void;
  (e: 'update:description', value: string): void;
  (e: 'addQuality'): void;
  (e: 'removeQuality', index: number): void;
}

const props = withDefaults(defineProps<Props>(), {
  autoFocus: false,
  qualityNames: () => [],
});

const emit = defineEmits<Emits>();

const qualityInput = computed({
  get: () => props.qualityInput,
  set: (value: string) => emit('update:qualityInput', value),
});

const description = computed({
  get: () => props.description,
  set: (value: string) => emit('update:description', value),
});

const addQuality = (): void => {
  emit('addQuality');
};

const removeQuality = (index: number): void => {
  emit('removeQuality', index);
};
</script>

<template>
  <q-page class="q-pa-md">
    <div class="create-dream-container">
      <!-- Header -->
      <div class="row items-center q-mb-md">
        <q-btn flat round icon="arrow_back" @click="router.push('/')" class="q-mr-sm" />
        <div class="text-h6 text-weight-medium">{{ isEditMode ? 'Edit Dream' : 'New Dream' }}</div>
      </div>

      <!-- Dream Form -->
      <q-form @submit="onSubmit" class="column q-gutter-md">
        <!-- Quality Tags Input -->
        <div>
          <q-input
            v-model="qualityInput"
            outlined
            placeholder="Add qualities (e.g., vivid, scary, flying...)"
            @keyup.enter="addQuality"
            class="full-width"
            autofocus
          >
            <template v-slot:append>
              <q-btn flat round icon="add" @click="addQuality" :disabled="!qualityInput.trim()" />
            </template>
          </q-input>

          <!-- Quality Chips -->
          <div v-if="dreamForm.quality_names?.length" class="q-mt-sm">
            <q-chip
              v-for="(quality, index) in dreamForm.quality_names"
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

        <!-- Content Input -->
        <div>
          <q-input
            v-model="dreamForm.description"
            outlined
            type="textarea"
            rows="8"
            class="full-width"
            placeholder="What happened in your dream? Include as much detail as you remember..."
          >
            <template v-slot:prepend>
              <q-icon name="description" />
            </template>
          </q-input>
        </div>

        <!-- Submit Button -->
        <div>
          <q-btn
            type="submit"
            color="primary"
            label="Save Dream"
            unelevated
            :loading="loading"
            :disable="loading"
            class="full-width q-mt-lg"
            size="lg"
          >
            <template v-slot:loading>
              <q-spinner-hourglass class="on-left" />
              Saving...
            </template>
          </q-btn>
        </div>
      </q-form>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useQuasar } from 'quasar';
import { dreamsApi } from 'src/services/web';
import type { DreamCreate } from 'components/models';

const router = useRouter();
const route = useRoute();
const $q = useQuasar();
const loading = ref(false);
const qualityInput = ref('');

const dreamId = computed(() => route.params.id as string | undefined);
const isEditMode = computed(() => !!dreamId.value);

const dreamForm = reactive<DreamCreate>({
  description: '',
  quality_names: [],
});

const addQuality = (): void => {
  const quality = qualityInput.value.trim().toLowerCase();
  if (quality && !dreamForm.quality_names?.includes(quality)) {
    if (!dreamForm.quality_names) {
      dreamForm.quality_names = [];
    }
    dreamForm.quality_names.push(quality);
    qualityInput.value = '';
  }
};

const removeQuality = (index: number): void => {
  if (dreamForm.quality_names) {
    dreamForm.quality_names.splice(index, 1);
  }
};

const fetchDream = async (): Promise<void> => {
  if (!isEditMode.value || !dreamId.value) return;

  try {
    const response = await dreamsApi.get(dreamId.value);
    const dream = response.data;

    dreamForm.description = dream.description;
    dreamForm.quality_names = dream.qualities?.map((q) => q.name) || [];
  } catch (error) {
    console.error('Error fetching dream:', error);
    $q.notify({
      type: 'negative',
      message: 'Failed to load dream data.',
      position: 'top',
    });
    void router.push('/');
  }
};

const onSubmit = async (): Promise<void> => {
  loading.value = true;

  try {
    if (isEditMode.value) {
      if (dreamId.value) {
        await dreamsApi.update(dreamId.value, dreamForm);
      }
    } else {
      await dreamsApi.create(dreamForm);
    }

    $q.notify({
      type: 'positive',
      message: 'Dream saved successfully!',
      position: 'top',
    });

    void router.push('/');
  } catch (error) {
    console.error('Error saving dream:', error);
    $q.notify({
      type: 'negative',
      message: 'Failed to save dream. Please try again.',
      position: 'top',
    });
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  void fetchDream();
});
</script>

<style scoped>
.create-dream-container {
  max-width: 600px;
  margin: 0 auto;
}

/* Mobile-first responsive design */
@media (max-width: 600px) {
  .create-dream-container {
    max-width: 100%;
  }
}
</style>

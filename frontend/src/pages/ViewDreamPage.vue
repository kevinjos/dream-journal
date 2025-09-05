<template>
  <q-page class="q-pa-sm">
    <div class="page-container">
      <!-- Header -->
      <div class="row items-center justify-between q-mb-md">
        <div class="row items-center">
          <q-btn flat round icon="arrow_back" @click="goBack" class="q-mr-sm" />
          <div class="text-h6 text-weight-medium">
            {{ isOwner ? 'Dreamscape' : 'Astral Plane' }}
          </div>
        </div>
        <q-chip v-if="dream?.is_public" color="blue-2" text-color="primary" icon="visibility">
          Public Dream
        </q-chip>
      </div>

      <!-- Dream Content (Read-only) -->
      <div v-if="dream" class="column q-gutter-md">
        <!-- Description -->
        <q-input
          v-model="dream.description"
          type="textarea"
          outlined
          readonly
          autogrow
          label="Dream Description"
          :input-style="{ minHeight: '100px' }"
        />

        <!-- Qualities -->
        <div>
          <div class="text-subtitle2 q-mb-sm">Qualities</div>
          <div class="row q-gutter-sm">
            <q-chip
              v-for="quality in dream.qualities"
              :key="quality.id"
              color="primary"
              text-color="white"
            >
              {{ quality.name }}
            </q-chip>
            <div v-if="!dream.qualities?.length" class="text-grey-6">No qualities added</div>
          </div>
        </div>
      </div>

      <!-- Generated Images Display -->
      <div v-if="latestCompletedImage" class="q-mt-md">
        <DreamImage :image="latestCompletedImage" />
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useQuasar } from 'quasar';
import { dreamsApi } from 'src/services/web';
import { useDreamImages } from 'src/composables/useDreamImages';
import DreamImage from 'components/DreamImage.vue';
import type { Dream } from 'src/types/models';

const router = useRouter();
const route = useRoute();
const $q = useQuasar();

const dream = ref<Dream | null>(null);

// Use the dream images composable
const { latestCompletedImage, fetchImages } = useDreamImages();

const dreamId = computed(() => route.params.id as string);
const isOwner = computed(() => dream.value?.is_owner || false);

const fetchDream = async (): Promise<void> => {
  if (!dreamId.value) return;

  try {
    const response = await dreamsApi.get(dreamId.value);
    dream.value = response.data;

    // Fetch images
    await fetchImages(dreamId.value);
  } catch (error) {
    console.error('Error fetching dream:', error);
    $q.notify({
      type: 'negative',
      message: 'Failed to load dream.',
      position: 'top',
    });
    void router.push('/dreams');
  }
};

const goBack = (): void => {
  void router.push('/dreams');
};

onMounted(() => {
  void fetchDream();
});
</script>

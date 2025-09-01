<template>
  <q-page class="q-pa-sm">
    <div class="edit-dream-container">
      <!-- Header -->
      <div class="row items-center justify-between q-mb-md">
        <div class="row items-center">
          <q-btn flat round icon="arrow_back" @click="goBack" class="q-mr-sm" />
          <div class="text-h6 text-weight-medium">Dreamscape</div>
        </div>
        <SyncStatusIndicator :status="syncStatus" :error="syncError" />
      </div>

      <!-- Dream Form -->
      <div class="column q-gutter-md">
        <DreamFormFields
          v-model:quality-input="qualityInput"
          v-model:description="dreamForm.description"
          :quality-names="dreamForm.quality_names"
          :auto-focus="true"
          @add-quality="addQuality"
          @remove-quality="removeQuality"
        />

        <!-- Generate Image Button -->
        <transition
          enter-active-class="fade-enter-active"
          leave-active-class="fade-leave-active"
          enter-from-class="fade-enter-from"
          leave-to-class="fade-leave-to"
        >
          <div v-if="imagesLoaded && !latestCompletedImage">
            <q-btn
              color="secondary"
              outline
              label="Generate Image"
              icon="auto_awesome"
              :loading="generatingImage"
              :disable="generatingImage || !dreamForm.description.trim()"
              class="full-width"
              @click="generateImage"
            >
              <template v-slot:loading>
                <q-spinner-hourglass class="on-left" />
                Generating...
              </template>
            </q-btn>
          </div>
        </transition>
      </div>

      <!-- Generated Images Display -->
      <div v-if="latestCompletedImage" class="q-mt-md q-mb-xl">
        <q-card class="q-mb-md">
          <div class="q-pa-sm">
            <!-- Show completed image -->
            <q-img
              v-if="latestCompletedImage.image_url"
              :src="latestCompletedImage.image_url"
              :alt="latestCompletedImage.generation_prompt"
              ratio="1"
              fit="cover"
              class="rounded-borders image-border"
            >
              <template v-slot:error>
                <div class="absolute-full flex flex-center bg-grey-3 text-grey-7">
                  <div class="text-center">
                    <q-icon name="broken_image" size="24px" />
                    <div class="text-caption">Failed to load</div>
                  </div>
                </div>
              </template>
            </q-img>
          </div>

          <!-- Request Changes Section -->
          <div class="q-pa-sm q-pt-none">
            <div class="row q-gutter-sm items-start">
              <q-input
                v-model="imageChangePrompt"
                type="textarea"
                autogrow
                outlined
                dense
                placeholder="Alter image"
                class="col"
                :input-style="{ minHeight: '38px', resize: 'none' }"
                @keyup.enter.stop="regenerateImage"
              >
                <template v-slot:append>
                  <q-icon
                    v-if="imageChangePrompt"
                    name="close"
                    class="cursor-pointer"
                    @click="imageChangePrompt = ''"
                  />
                </template>
              </q-input>
              <q-btn
                round
                color="secondary"
                outline
                icon="auto_fix_high"
                size="sm"
                :loading="generatingImage"
                :disable="generatingImage || !imageChangePrompt.trim()"
                @click="regenerateImage"
                style="flex-shrink: 0"
              >
                <template v-slot:loading>
                  <q-spinner-hourglass />
                </template>
              </q-btn>
            </div>
          </div>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useQuasar } from 'quasar';
import { dreamsApi } from 'src/services/web';
import { useDreamForm } from 'src/composables/useDreamForm';
import DreamFormFields from 'components/DreamFormFields.vue';
import SyncStatusIndicator from 'components/SyncStatusIndicator.vue';
import type { SyncStatus } from 'components/SyncStatusIndicator.vue';
import type { Image } from 'src/types/models';
import { ImageGenerationStatus } from 'src/types/models';

const router = useRouter();
const route = useRoute();
const $q = useQuasar();
const generatingImage = ref(false);
const generatedImages = ref<Image[]>([]);
const imagesLoaded = ref(false); // Track if we've loaded images from API
let pollingInterval: NodeJS.Timeout | null = null;
const imageChangePrompt = ref('');

// Auto-save state management
const syncStatus = ref<SyncStatus>('synced');
const syncError = ref<string>('');
let saveDebounceTimer: NodeJS.Timeout | null = null;
const isInitialLoad = ref(true);

const dreamId = computed(() => route.params.id as string);

// Computed property to show only the latest completed image
const latestCompletedImage = computed(() => {
  const completed = generatedImages.value
    .filter((img) => img.generation_status === ImageGenerationStatus.COMPLETED)
    .sort((a, b) => new Date(b.created).getTime() - new Date(a.created).getTime());
  return completed.length > 0 ? completed[0] : null;
});

// Use the dream form composable
const { qualityInput, dreamForm, addQuality, removeQuality, populateForm } = useDreamForm();

// Auto-save function with field-specific updates
const autoSave = async (fields: Partial<typeof dreamForm>, immediate = false): Promise<void> => {
  if (isInitialLoad.value || !dreamId.value) return;

  // Clear any existing debounce timer for immediate saves
  if (immediate && saveDebounceTimer) {
    clearTimeout(saveDebounceTimer);
    saveDebounceTimer = null;
  }

  const performSave = async (): Promise<void> => {
    syncStatus.value = 'saving';
    syncError.value = '';

    try {
      // Only send the fields that changed
      await dreamsApi.update(dreamId.value, fields);
      syncStatus.value = 'synced';
    } catch (error) {
      console.error('Error auto-saving dream:', error);
      syncStatus.value = 'error';
      syncError.value = 'Failed to save';

      $q.notify({
        type: 'negative',
        message: 'Failed to save changes. Retrying...',
        position: 'top',
      });

      // Retry after 3 seconds with the same fields
      setTimeout(() => {
        void autoSave(fields, true);
      }, 3000);
    }
  };

  if (immediate) {
    await performSave();
  } else {
    // Debounce for description changes
    syncStatus.value = 'modified';

    if (saveDebounceTimer) {
      clearTimeout(saveDebounceTimer);
    }

    saveDebounceTimer = setTimeout(() => {
      void performSave();
    }, 4000); // 4 second debounce
  }
};

// Watch for description changes
watch(
  () => dreamForm.description,
  () => {
    // Only send description field
    void autoSave({ description: dreamForm.description }, false); // Debounced save
  },
);

// Watch for quality changes
watch(
  () => dreamForm.quality_names,
  () => {
    // Only send quality_names field
    void autoSave({ quality_names: dreamForm.quality_names }, true); // Immediate save
  },
  { deep: true },
);

const fetchDream = async (): Promise<void> => {
  if (!dreamId.value) return;

  try {
    // Fetch dream data
    const response = await dreamsApi.get(dreamId.value);
    const dream = response.data;

    populateForm({
      description: dream.description,
      quality_names: dream.qualities?.map((q) => q.name) || [],
    });

    // Fetch existing images for this dream
    await fetchImages();

    // Mark initial load as complete
    setTimeout(() => {
      isInitialLoad.value = false;
    }, 100);
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

const fetchImages = async (): Promise<void> => {
  if (!dreamId.value) return;

  try {
    const response = await dreamsApi.getImages(dreamId.value);
    generatedImages.value = response.data as Image[];

    // Check if the most recent image is generating/pending and start polling
    if (generatedImages.value.length > 0) {
      // Sort images by creation date to find the most recent
      const sortedImages = [...generatedImages.value].sort(
        (a, b) => new Date(b.created).getTime() - new Date(a.created).getTime(),
      );
      const mostRecentImage = sortedImages[0];

      // Only poll if the most recent image exists and is generating or pending
      if (
        mostRecentImage &&
        (mostRecentImage.generation_status === ImageGenerationStatus.GENERATING ||
          mostRecentImage.generation_status === ImageGenerationStatus.PENDING)
      ) {
        pollImageStatus(mostRecentImage.id);
      }
    }
  } catch (error) {
    console.error('Error fetching images:', error);
    // Don't show notification for image loading errors
  } finally {
    // Always set images as loaded, regardless of success/failure
    imagesLoaded.value = true;
  }
};

const generateImage = async (): Promise<void> => {
  if (!dreamForm.description.trim() || !dreamId.value) return;

  generatingImage.value = true;

  try {
    // Call the image generation API
    const response = await dreamsApi.generateImage(dreamId.value);

    $q.notify({
      type: 'positive',
      message: "Image generation started! You'll be notified when complete.",
      position: 'top',
    });

    // Start polling for completion
    pollImageStatus(response.data.id);
  } catch (error) {
    console.error('Error generating image:', error);
    $q.notify({
      type: 'negative',
      message: 'Failed to start image generation. Please try again.',
      position: 'top',
    });
  } finally {
    generatingImage.value = false;
  }
};

const regenerateImage = async (): Promise<void> => {
  if (!imageChangePrompt.value.trim() || !dreamId.value || !latestCompletedImage.value) return;

  generatingImage.value = true;

  try {
    // Call the alter_image API with the custom prompt
    const response = await dreamsApi.alterImage(
      dreamId.value,
      latestCompletedImage.value.id,
      imageChangePrompt.value,
    );

    $q.notify({
      type: 'positive',
      message: 'Image alteration started with your changes!',
      position: 'top',
    });

    // Clear the prompt input
    imageChangePrompt.value = '';

    // Start polling for completion
    pollImageStatus(response.data.id);
  } catch (error) {
    console.error('Error altering image:', error);
    $q.notify({
      type: 'negative',
      message: 'Failed to alter image. Please try again.',
      position: 'top',
    });
  } finally {
    generatingImage.value = false;
  }
};

const pollImageStatus = (imageId: number): void => {
  // Clear any existing polling
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }

  // Create async function for checking status
  const checkStatus = async (): Promise<void> => {
    try {
      if (!dreamId.value) return;

      const response = await dreamsApi.getImage(dreamId.value, imageId);
      const image = response.data as Image;

      // Update the image in our local state
      const existingIndex = generatedImages.value.findIndex((img) => img.id === imageId);
      if (existingIndex >= 0) {
        generatedImages.value[existingIndex] = image;
      } else {
        generatedImages.value.push(image);
      }

      // Stop polling if completed or failed
      if (
        image.generation_status === ImageGenerationStatus.COMPLETED ||
        image.generation_status === ImageGenerationStatus.FAILED
      ) {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
        }

        if (image.generation_status === ImageGenerationStatus.COMPLETED) {
          $q.notify({
            type: 'positive',
            message: 'Image generation completed!',
            position: 'top',
          });
        } else {
          $q.notify({
            type: 'negative',
            message: 'Image generation failed.',
            position: 'top',
          });
        }
      }
    } catch (error) {
      console.error('Error checking image status:', error);
      // Don't show notification for polling errors
    }
  };

  // Use void operator to indicate we're intentionally not awaiting
  pollingInterval = setInterval(() => {
    void checkStatus();
  }, 8000); // Poll every 8 seconds

  // Stop polling after 128 seconds
  setTimeout(() => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  }, 128 * 1000); // 128 seconds
};

const goBack = (): void => {
  void router.push('/dreams');
};

onMounted(() => {
  void fetchDream();
});

onUnmounted(() => {
  // Clean up polling when component unmounts
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }

  // Clean up debounce timer
  if (saveDebounceTimer) {
    clearTimeout(saveDebounceTimer);
    saveDebounceTimer = null;
  }
});
</script>

<style scoped>
.edit-dream-container {
  max-width: 600px;
}

/* Custom fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.8s ease-in-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

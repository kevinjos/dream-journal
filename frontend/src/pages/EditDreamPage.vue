<template>
  <q-page class="q-pa-sm q-pa-md-md">
    <div class="edit-dream-container">
      <!-- Header -->
      <div class="row items-center q-mb-md">
        <q-btn flat round icon="arrow_back" @click="goBack" class="q-mr-sm" />
        <div class="text-h6 text-weight-medium">Edit Dream</div>
      </div>

      <!-- Dream Form -->
      <q-form @submit="onSubmit" class="column q-gutter-md">
        <DreamFormFields
          v-model:quality-input="qualityInput"
          v-model:description="dreamForm.description"
          :quality-names="dreamForm.quality_names"
          :auto-focus="true"
          @add-quality="addQuality"
          @remove-quality="removeQuality"
        />

        <!-- Generate Image Button -->
        <div>
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
      </q-form>
    </div>

    <StickySubmitButton
      label="Save Changes"
      loading-text="Saving..."
      :loading="loading"
      @click="onSubmit"
    />
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useQuasar } from 'quasar';
import { dreamsApi } from 'src/services/web';
import { useDreamForm } from 'src/composables/useDreamForm';
import DreamFormFields from 'components/DreamFormFields.vue';
import StickySubmitButton from 'components/StickySubmitButton.vue';

const router = useRouter();
const route = useRoute();
const $q = useQuasar();
const loading = ref(false);
const generatingImage = ref(false);

const dreamId = computed(() => route.params.id as string);

// Use the dream form composable
const { qualityInput, dreamForm, addQuality, removeQuality, populateForm } = useDreamForm();

const fetchDream = async (): Promise<void> => {
  if (!dreamId.value) return;

  try {
    const response = await dreamsApi.get(dreamId.value);
    const dream = response.data;

    populateForm({
      description: dream.description,
      quality_names: dream.qualities?.map((q) => q.name) || [],
    });
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

const generateImage = async (): Promise<void> => {
  if (!dreamForm.description.trim()) return;

  generatingImage.value = true;

  try {
    // TODO: Implement image generation API call
    // This is a placeholder for the actual image generation functionality
    await new Promise((resolve) => setTimeout(resolve, 2000)); // Simulate API call

    $q.notify({
      type: 'positive',
      message: 'Image generation feature coming soon!',
      position: 'top',
    });
  } catch (error) {
    console.error('Error generating image:', error);
    $q.notify({
      type: 'negative',
      message: 'Failed to generate image. Please try again.',
      position: 'top',
    });
  } finally {
    generatingImage.value = false;
  }
};

const onSubmit = async (): Promise<void> => {
  loading.value = true;

  try {
    await dreamsApi.update(dreamId.value, dreamForm);

    $q.notify({
      type: 'positive',
      message: 'Dream updated successfully!',
      position: 'top',
    });
  } catch (error) {
    console.error('Error updating dream:', error);
    $q.notify({
      type: 'negative',
      message: 'Failed to update dream. Please try again.',
      position: 'top',
    });
  } finally {
    loading.value = false;
  }
};

const goBack = (): void => {
  void router.push('/dreams');
};

onMounted(() => {
  void fetchDream();
});
</script>

<style scoped>
.edit-dream-container {
  max-width: 600px;
  margin: 0 auto;
}
</style>

<template>
  <q-page class="q-pa-sm q-pa-md-md">
    <div class="page-container">
      <!-- Header -->
      <div class="row items-center q-mb-md">
        <q-btn flat round icon="arrow_back" @click="goBack" class="q-mr-sm" />
        <div class="text-h6 text-weight-medium">New Dream</div>
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
      </q-form>
    </div>

    <StickySubmitButton
      label="Save Dream"
      loading-text="Saving..."
      :loading="loading"
      @click="onSubmit"
    />
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { dreamsApi } from 'src/services/web';
import { useDreamForm } from 'src/composables/useDreamForm';
import DreamFormFields from 'components/DreamFormFields.vue';
import StickySubmitButton from 'components/StickySubmitButton.vue';

const router = useRouter();
const $q = useQuasar();
const loading = ref(false);

// Use the dream form composable
const { qualityInput, dreamForm, addQuality, removeQuality } = useDreamForm();

// No need to fetch dream data since this page only creates new dreams

const onSubmit = async (): Promise<void> => {
  loading.value = true;

  try {
    const response = await dreamsApi.create(dreamForm);
    const savedDreamId = response.data.id.toString();

    $q.notify({
      type: 'positive',
      message: 'Dream saved successfully!',
      position: 'top',
    });

    void router.push(`/dreams/${savedDreamId}/edit`);
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

const goBack = (): void => {
  void router.push('/');
};

// No onMounted needed since we don't fetch data for new dreams
</script>

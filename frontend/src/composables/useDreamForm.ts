import { ref, reactive } from 'vue';
import type { DreamCreate } from 'src/types/models';

export function useDreamForm() {
  const qualityInput = ref('');

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

  const resetForm = (): void => {
    dreamForm.description = '';
    dreamForm.quality_names = [];
    qualityInput.value = '';
  };

  const populateForm = (data: { description: string; quality_names?: string[] }): void => {
    dreamForm.description = data.description;
    dreamForm.quality_names = data.quality_names || [];
  };

  return {
    qualityInput,
    dreamForm,
    addQuality,
    removeQuality,
    resetForm,
    populateForm,
  };
}

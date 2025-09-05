import { ref, computed } from 'vue';
import { dreamsApi } from 'src/services/web';
import type { Image } from 'src/types/models';
import { ImageGenerationStatus } from 'src/types/models';

export function useDreamImages() {
  const generatedImages = ref<Image[]>([]);
  const imagesLoaded = ref(false);

  // Computed property to show only the latest completed image
  const latestCompletedImage = computed(() => {
    const completed = generatedImages.value
      .filter((img) => img.generation_status === ImageGenerationStatus.COMPLETED)
      .sort((a, b) => new Date(b.created).getTime() - new Date(a.created).getTime());
    return completed.length > 0 ? completed[0] : null;
  });

  const fetchImages = async (dreamId: string): Promise<void> => {
    try {
      const response = await dreamsApi.getImages(dreamId);
      generatedImages.value = response.data as Image[];
    } catch (error) {
      console.error('Error fetching images:', error);
      // Don't show notification for image loading errors
    } finally {
      // Always set images as loaded, regardless of success/failure
      imagesLoaded.value = true;
    }
  };

  const updateImage = (image: Image): void => {
    const existingIndex = generatedImages.value.findIndex((img) => img.id === image.id);
    if (existingIndex >= 0) {
      generatedImages.value[existingIndex] = image;
    } else {
      generatedImages.value.push(image);
    }
  };

  return {
    generatedImages,
    imagesLoaded,
    latestCompletedImage,
    fetchImages,
    updateImage,
  };
}

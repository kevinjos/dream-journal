<template>
  <q-card v-if="image" class="dream-image-card">
    <div class="q-pa-sm">
      <q-img
        v-if="image.image_url"
        :src="image.image_url"
        :alt="image.generation_prompt"
        ratio="1"
        fit="cover"
        class="rounded-borders"
        :class="{ 'image-border': showBorder }"
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

    <!-- Slot for additional content (like the alter image controls in EditDreamPage) -->
    <slot name="controls"></slot>
  </q-card>
</template>

<script setup lang="ts">
import type { Image } from 'src/types/models';

interface Props {
  image: Image | null;
  showBorder?: boolean;
}

withDefaults(defineProps<Props>(), {
  showBorder: false,
});
</script>

<style scoped>
.dream-image-card {
  /* Component styles inherit from parent */
}

.image-border {
  border: 2px solid var(--q-primary);
}
</style>

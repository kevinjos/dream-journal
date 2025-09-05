<template>
  <q-card
    flat
    bordered
    class="q-mb-md q-pa-md cursor-pointer dream-card"
    :class="cardClass"
    @click="$emit('click', dream)"
  >
    <!-- Dream header with status and date -->
    <div class="row items-center q-mb-sm">
      <div class="row items-center">
        <q-chip
          v-if="showOwnership && dream.is_owner !== undefined"
          size="sm"
          :color="dream.is_public ? 'blue-2' : 'grey-3'"
          :text-color="dream.is_public ? 'primary' : 'grey-7'"
          :icon="dream.is_public ? 'visibility' : 'lock'"
        >
          {{ dream.is_public ? 'Public' : 'Private' }}
        </q-chip>
        <q-chip
          v-else-if="showAnonymous"
          size="sm"
          color="blue-2"
          text-color="primary"
          icon="visibility_off"
        >
          Anonymous
        </q-chip>
      </div>
      <q-space />
      <div class="text-caption text-grey-6">
        {{ formatDate(dream.created) }}
      </div>
    </div>

    <!-- Dream description -->
    <div class="text-body1 q-mb-sm">
      {{ truncatedDescription }}
    </div>

    <!-- Quality Tags -->
    <div v-if="dream.qualities?.length" class="q-mt-sm">
      <q-chip
        v-for="quality in dream.qualities"
        :key="quality.id"
        :label="quality.name"
        color="primary"
        outline
        size="sm"
        class="q-mr-xs q-mb-xs"
      />
    </div>

    <!-- Image preview if available -->
    <div v-if="dream.images?.length" class="q-mt-sm">
      <div class="text-caption text-grey-6 q-mb-xs">
        {{ dream.images.length }} generated image{{ dream.images.length > 1 ? 's' : '' }}
      </div>
    </div>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Dream } from 'src/types/models';

interface Props {
  dream: Dream;
  showOwnership?: boolean; // Show Public/Private status for owned dreams
  showAnonymous?: boolean; // Show Anonymous indicator for public dreams
  cardClass?: string; // Additional CSS classes for card styling
  maxDescriptionLength?: number;
}

const props = withDefaults(defineProps<Props>(), {
  showOwnership: false,
  showAnonymous: false,
  cardClass: '',
  maxDescriptionLength: 200,
});

defineEmits<{
  click: [dream: Dream];
}>();

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

const truncatedDescription = computed(() => {
  if (!props.dream.description) return '';

  if (props.dream.description.length <= props.maxDescriptionLength) {
    return props.dream.description;
  }

  return props.dream.description.substring(0, props.maxDescriptionLength) + '...';
});
</script>

<style scoped>
.dream-card {
  border-left: 4px solid #f5f5f5;
}

.dream-card:hover {
  border-left: 4px solid #1976d2;
  transition: border-left-color 0.3s ease;
}

.dream-card.astral-style {
  border-left: 4px solid #e3f2fd;
}

.dream-card.astral-style:hover {
  border-left: 4px solid #2196f3;
}
</style>

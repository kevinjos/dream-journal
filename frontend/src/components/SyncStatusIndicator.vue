<template>
  <div class="sync-status-indicator">
    <q-icon :name="statusIcon" :color="statusColor" size="16px" class="q-mr-xs" />
    <span class="text-caption">{{ statusText }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

export type SyncStatus = 'synced' | 'saving' | 'error' | 'modified';

interface Props {
  status: SyncStatus;
  error?: string;
}

const props = withDefaults(defineProps<Props>(), {
  status: 'synced',
});

const statusIcon = computed(() => {
  switch (props.status) {
    case 'synced':
      return 'check_circle';
    case 'saving':
      return 'sync';
    case 'error':
      return 'error';
    case 'modified':
      return 'edit';
    default:
      return 'help';
  }
});

const statusColor = computed(() => {
  switch (props.status) {
    case 'synced':
      return 'positive';
    case 'saving':
      return 'warning';
    case 'error':
      return 'negative';
    case 'modified':
      return 'info';
    default:
      return 'grey';
  }
});

const statusText = computed(() => {
  switch (props.status) {
    case 'synced':
      return 'Saved';
    case 'saving':
      return 'Saving...';
    case 'error':
      return props.error || 'Error';
    case 'modified':
      return 'Modified';
    default:
      return '';
  }
});
</script>

<style scoped>
.sync-status-indicator {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

/* Add spinning animation for saving state */
:deep(.q-icon) {
  transition: color 0.3s ease;
}

.sync-status-indicator .q-icon[name='sync'] {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>

<template>
  <div v-if="totalPages > 1" class="row justify-center q-mt-md">
    <q-pagination
      v-model="currentPageModel"
      :max="totalPages"
      :max-pages="6"
      boundary-numbers
      direction-links
      outline
      color="primary"
      :disable="loading"
      @update:model-value="onPageChange"
    />
    
    <!-- Results info -->
    <div class="full-width text-center q-mt-sm">
      <div class="text-caption text-grey-6">
        Showing {{ startItem }}-{{ endItem }} of {{ totalItems }} results
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  currentPage: number
  totalPages: number
  totalItems: number
  pageSize?: number
  loading?: boolean
}

interface Emits {
  (e: 'page-change', page: number): void
}

const props = withDefaults(defineProps<Props>(), {
  pageSize: 20,
  loading: false
})

const emit = defineEmits<Emits>()

const currentPageModel = computed({
  get: () => props.currentPage,
  set: (value: number) => {
    // This setter is needed for v-model but actual changes come through onPageChange
  }
})

const startItem = computed(() => {
  if (props.totalItems === 0) return 0
  return (props.currentPage - 1) * props.pageSize + 1
})

const endItem = computed(() => {
  const calculated = props.currentPage * props.pageSize
  return Math.min(calculated, props.totalItems)
})

const onPageChange = (page: number): void => {
  if (page !== props.currentPage && !props.loading) {
    emit('page-change', page)
  }
}
</script>

<style scoped>
/* Pagination styles inherit from Quasar theme */
</style>
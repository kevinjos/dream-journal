<template>
  <q-page class="q-pa-sm q-pa-md-md">
    <div class="page-container">
      <!-- Header -->
      <div class="row items-center q-mb-md">
        <q-btn flat round icon="arrow_back" @click="router.push('/')" class="q-mr-sm" />
        <div class="text-h6 text-weight-medium">
          {{ filterQuality ? `Dreams with "${filterQuality.name}"` : 'All Dreams' }}
        </div>
      </div>

      <!-- Search and Filter Section -->
      <div class="q-mb-md">
        <!-- Search Input -->
        <q-input
          v-model="searchQuery"
          outlined
          placeholder="Search dreams..."
          clearable
          class="q-mb-sm"
          @update:model-value="onSearchInput"
        >
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
        </q-input>

        <!-- Quality Filter Chip -->
        <div v-if="filterQuality">
          <q-chip
            :label="filterQuality.name"
            :style="{ color: qualityColor, backgroundColor: `${qualityColor}20` }"
            removable
            @remove="clearFilter"
            icon="local_offer"
          />
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="text-center q-pa-lg">
        <q-spinner-dots size="40px" color="primary" />
        <div class="text-subtitle2 q-mt-md">Loading dreams...</div>
      </div>

      <!-- Dreams List -->
      <div v-else-if="dreams.length > 0" class="dreams-list">
        <DreamCard
          v-for="dream in dreams"
          :key="dream.id"
          :dream="dream"
          :show-ownership="true"
          @click="openDream"
        />
      </div>

      <!-- Empty state -->
      <q-card v-else flat bordered class="text-center q-pa-lg">
        <q-icon name="bedtime" size="48px" color="grey-5" class="q-mb-md" />
        <div class="text-subtitle1 text-grey-6 q-mb-sm">
          {{ filterQuality ? `No dreams with "${filterQuality.name}"` : 'No dreams yet' }}
        </div>
        <div class="text-body2 text-grey-5">
          {{
            filterQuality
              ? 'Try a different quality or create more dreams'
              : 'Start capturing your dreams'
          }}
        </div>
      </q-card>

      <!-- Pagination -->
      <PaginationComponent
        v-if="!loading"
        :current-page="pagination.currentPage"
        :total-pages="pagination.totalPages"
        :total-items="pagination.count"
        :page-size="5"
        :loading="loading"
        @page-change="onPageChange"
      />
    </div>

    <!-- Floating Action Button -->
    <q-page-sticky position="bottom-right" :offset="[18, 18]">
      <q-btn
        fab
        icon="add"
        color="primary"
        @click="router.push('/dreams/create')"
        aria-label="Create new dream"
      />
    </q-page-sticky>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { dreamsApi, qualitiesApi } from 'src/services/web';
import type { Dream, Quality } from 'src/types/models';
import { useDreamsList } from 'src/composables/useDreamsList';
import PaginationComponent from 'components/PaginationComponent.vue';
import DreamCard from 'components/DreamCard.vue';

const router = useRouter();
const route = useRoute();
const filterQuality = ref<Quality | null>(null);

// Use shared dreams list logic
const dreamsFetcher = async (page = 1, search?: string) => {
  // Build API URL with query parameters
  const params = new URLSearchParams();
  const qualityId = route.query.quality as string;

  // Add pagination parameter
  if (page > 1) {
    params.append('page', page.toString());
  }

  // Only use quality filter if it's in the URL
  if (qualityId && !filterQuality.value) {
    // Quality in URL but not loaded yet, fetch it
    try {
      const qualityResponse = await qualitiesApi.get(qualityId);
      filterQuality.value = qualityResponse.data;
      params.append('quality', qualityId);
    } catch (error) {
      console.warn('Could not fetch quality details:', error);
    }
  } else if (qualityId && filterQuality.value) {
    // Quality already loaded
    params.append('quality', qualityId);
  }

  // Add search query parameter
  if (search) {
    params.append('search', search);
  }

  return dreamsApi.list(params);
};

const { loading, dreams, searchQuery, pagination, onSearchInput, onPageChange, fetchDreams } =
  useDreamsList({
    fetchFunction: dreamsFetcher,
    initialSearchQuery: (route.query.search as string) || '',
  });

// Get a themed color for the quality filter chip
const qualityColor = computed(() => {
  if (!filterQuality.value) return '#1976d2';

  // Use the same color selection logic as the word cloud
  const computedStyle = getComputedStyle(document.documentElement);
  const colors = [
    computedStyle.getPropertyValue('--q-positive').trim(),
    computedStyle.getPropertyValue('--q-warning').trim(),
    computedStyle.getPropertyValue('--q-negative').trim(),
    computedStyle.getPropertyValue('--q-info').trim(),
    computedStyle.getPropertyValue('--q-accent').trim(),
    computedStyle.getPropertyValue('--q-secondary').trim(),
  ].filter((color) => color);

  // Use quality ID to pick consistent color
  return colors[filterQuality.value.id % colors.length] || '#1976d2';
});

const clearFilter = async (): Promise<void> => {
  // Clear the quality filter immediately
  filterQuality.value = null;

  // Update the route without quality param
  await router.replace({
    path: '/dreams',
    query: searchQuery.value.trim() ? { search: searchQuery.value.trim() } : {},
  });

  // Now fetch dreams without the quality filter
  await fetchDreams();
};

const openDream = (dream: Dream): void => {
  // If owner, go to edit page, otherwise view page
  if (dream.is_owner) {
    void router.push(`/dreams/${dream.id}/edit`);
  } else {
    void router.push(`/dreams/${dream.id}`);
  }
};
</script>

<style scoped>
.dreams-list {
  min-height: 400px;
}
</style>

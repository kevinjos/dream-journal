<template>
  <q-page class="q-pa-sm q-pa-md-md">
    <div class="dreams-list-container">
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
        <q-card
          v-for="dream in dreams"
          :key="dream.id"
          flat
          bordered
          class="q-mb-md q-pa-md cursor-pointer"
          @click="router.push(`/dreams/${dream.id}/edit`)"
        >
          <div class="text-body1 q-mb-sm">
            {{ dream.description?.substring(0, 200)
            }}{{ dream.description && dream.description.length > 200 ? '...' : '' }}
          </div>
          <div class="text-caption text-grey-6">
            {{ formatDate(dream.created) }} • {{ dream.qualities?.length || 0 }} qualities
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
        </q-card>
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
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { dreamsApi, qualitiesApi } from 'src/services/web';
import type { Dream, Quality } from 'src/types/models';
import PaginationComponent from 'components/PaginationComponent.vue';

const router = useRouter();
const route = useRoute();
const loading = ref(true);
const dreams = ref<Dream[]>([]);
const filterQuality = ref<Quality | null>(null);
const searchQuery = ref('');
const pagination = ref({
  count: 0,
  currentPage: 1,
  totalPages: 1,
});
let searchTimeout: NodeJS.Timeout;

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

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

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

const onSearchInput = (): void => {
  // Debounce search to avoid too many API calls
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }

  searchTimeout = setTimeout(() => {
    // Reset to page 1 when searching
    pagination.value.currentPage = 1;
    void fetchDreams(1);
  }, 300); // Wait 300ms after user stops typing
};

const onPageChange = (page: number): void => {
  pagination.value.currentPage = page;
  void fetchDreams(page);
};

const fetchDreams = async (page: number = 1): Promise<void> => {
  try {
    loading.value = true;

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
    // If filterQuality.value is null but qualityId exists, we're clearing it - don't add to params

    // Add search query parameter
    if (searchQuery.value.trim()) {
      params.append('search', searchQuery.value.trim());
    }

    // Build final URL

    // Fetch dreams
    const response = await dreamsApi.list(params);
    const data = response.data;

    // Handle paginated response
    if (data.results !== undefined) {
      // Paginated response
      dreams.value = data.results;
      pagination.value = {
        count: data.count || 0,
        currentPage: page,
        totalPages: Math.ceil((data.count || 0) / 20), // PAGE_SIZE is 20 from backend settings
      };
    } else {
      // Non-paginated response (fallback)
      dreams.value = data || [];
      pagination.value = {
        count: dreams.value.length,
        currentPage: 1,
        totalPages: 1,
      };
    }
  } catch (error) {
    console.error('Error fetching dreams:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  // Restore search query from URL if present
  const searchParam = route.query.search as string;
  if (searchParam) {
    searchQuery.value = searchParam;
  }

  void fetchDreams();
});
</script>

<style scoped>
.dreams-list-container {
  max-width: 800px;
  margin: 0 auto;
}

.dreams-list {
  min-height: 400px;
}
</style>

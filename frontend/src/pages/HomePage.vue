<template>
  <q-page class="q-pa-sm q-pa-md-md">
    <div class="home-container">
      <!-- Header -->
      <div class="text-center q-mb-xl">
        <div class="text-h4 text-weight-light">Dream Journal</div>
        <div class="text-subtitle1 text-grey-6">Hello {{ authStore.user?.username }}!</div>
      </div>

      <!-- Recent Dreams Section -->
      <div class="q-mb-lg">
        <div class="text-h6 q-mb-md">Recent Dreams</div>

        <!-- Loading state -->
        <div v-if="loading" class="text-center q-pa-md">
          <q-spinner-dots size="40px" color="primary" />
        </div>

        <!-- Dreams list -->
        <div v-else-if="dreams.length > 0">
          <q-card
            v-for="dream in dreams"
            :key="dream.id"
            flat
            bordered
            class="q-mb-sm q-pa-md cursor-pointer"
            @click="router.push(`/dreams/${dream.id}/edit`)"
          >
            <div class="text-body1">
              {{ dream.description?.substring(0, 100)
              }}{{ dream.description && dream.description.length > 100 ? '...' : '' }}
            </div>
            <div class="text-caption text-grey-6 q-mt-xs">
              {{ formatDate(dream.created) }} • {{ dream.qualities?.length || 0 }} qualities
            </div>
          </q-card>
        </div>

        <!-- Empty state -->
        <q-card v-else flat bordered class="text-center q-pa-lg">
          <q-icon name="bedtime" size="48px" color="grey-5" class="q-mb-md" />
          <div class="text-subtitle1 text-grey-6 q-mb-sm">No dreams yet</div>
          <div class="text-body2 text-grey-5">Start capturing your dreams</div>
        </q-card>

        <!-- Pagination for dreams -->
        <PaginationComponent
          v-if="!loading && dreams.length > 0"
          :current-page="pagination.currentPage"
          :total-pages="pagination.totalPages"
          :total-items="pagination.count"
          :loading="loading"
          @page-change="onPageChange"
        />
      </div>

      <!-- Quick Stats -->
      <div class="row q-gutter-md">
        <div class="col">
          <q-card
            flat
            bordered
            class="text-center q-pa-md cursor-pointer"
            @click="router.push('/dreams')"
          >
            <div class="text-h4 text-primary">{{ stats.dreamCount }}</div>
            <div class="text-caption text-grey-6">Dreams</div>
          </q-card>
        </div>
        <div class="col">
          <q-card
            flat
            bordered
            class="text-center q-pa-md cursor-pointer"
            @click="router.push('/qualities')"
          >
            <div class="text-h4 text-secondary">{{ stats.qualityCount }}</div>
            <div class="text-caption text-grey-6">Qualities</div>
          </q-card>
        </div>
      </div>
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
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from 'stores/auth';
import { dreamsApi, qualitiesApi } from 'src/services/web';
import type { Dream } from 'components/models';
import PaginationComponent from 'components/PaginationComponent.vue';

const router = useRouter();
const authStore = useAuthStore();

const loading = ref(true);
const dreams = ref<Dream[]>([]);
const pagination = ref({
  count: 0,
  currentPage: 1,
  totalPages: 1,
});
const stats = ref({
  dreamCount: 0,
  qualityCount: 0,
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

const onPageChange = (page: number): void => {
  pagination.value.currentPage = page;
  void fetchData(page);
};

const fetchData = async (page: number = 1): Promise<void> => {
  try {
    loading.value = true;

    // Build API URL with pagination
    const params = new URLSearchParams();
    if (page > 1) {
      params.append('page', page.toString());
    }

    // Fetch recent dreams
    const dreamsResponse = await dreamsApi.list(params);
    const dreamsData = dreamsResponse.data;

    // Handle paginated response
    if (dreamsData.results !== undefined) {
      // Paginated response
      dreams.value = dreamsData.results;
      pagination.value = {
        count: dreamsData.count || 0,
        currentPage: page,
        totalPages: Math.ceil((dreamsData.count || 0) / 20), // PAGE_SIZE is 20
      };
    } else {
      // Non-paginated response (fallback)
      dreams.value = dreamsData || [];
      pagination.value = {
        count: dreams.value.length,
        currentPage: 1,
        totalPages: 1,
      };
    }

    // Fetch qualities for stats
    const qualitiesResponse = await qualitiesApi.list();
    const qualities = qualitiesResponse.data.results || qualitiesResponse.data || [];

    // Update stats with total counts from API
    stats.value = {
      dreamCount: pagination.value.count,
      qualityCount: qualities.length,
    };
  } catch (error) {
    console.error('Error fetching data:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  void fetchData();
});
</script>

<style scoped>
.home-container {
  max-width: 600px;
  margin: 0 auto;
}
</style>

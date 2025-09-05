import { ref, onMounted } from 'vue';
import type { Dream } from 'src/types/models';

interface UseDreamsListOptions {
  fetchFunction: (
    page?: number,
    searchQuery?: string,
  ) => Promise<{
    data:
      | {
          results?: Dream[];
          count?: number;
        }
      | Dream[];
  }>;
  initialSearchQuery?: string;
}

interface PaginationState {
  count: number;
  currentPage: number;
  totalPages: number;
}

export function useDreamsList(options: UseDreamsListOptions) {
  const { fetchFunction, initialSearchQuery = '' } = options;

  const loading = ref(true);
  const dreams = ref<Dream[]>([]);
  const searchQuery = ref(initialSearchQuery);
  const pagination = ref<PaginationState>({
    count: 0,
    currentPage: 1,
    totalPages: 1,
  });

  let searchTimeout: NodeJS.Timeout;

  const onSearchInput = (): void => {
    // Debounce search to avoid too many API calls
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    searchTimeout = setTimeout(() => {
      // Reset to page 1 when searching
      pagination.value.currentPage = 1;
      void fetchDreams(1);
    }, 2000); // Wait 2 seconds after user stops typing
  };

  const onPageChange = (page: number): void => {
    pagination.value.currentPage = page;
    void fetchDreams(page);
  };

  const fetchDreams = async (page: number = 1): Promise<void> => {
    try {
      loading.value = true;

      const response = await fetchFunction(page, searchQuery.value.trim() || undefined);

      const data = response.data;

      // Handle paginated response
      if (data && typeof data === 'object' && 'results' in data) {
        // Paginated response
        dreams.value = data.results || [];
        pagination.value = {
          count: data.count || 0,
          currentPage: page,
          totalPages: Math.ceil((data.count || 0) / 5), // PAGE_SIZE is 5 from backend settings
        };
      } else {
        // Non-paginated response (fallback)
        dreams.value = (data as Dream[]) || [];
        pagination.value = {
          count: dreams.value.length,
          currentPage: 1,
          totalPages: 1,
        };
      }
    } catch (error) {
      console.error('Error fetching dreams:', error);
      dreams.value = [];
    } finally {
      loading.value = false;
    }
  };

  // Initialize on mount
  onMounted(() => {
    void fetchDreams();
  });

  return {
    // State
    loading,
    dreams,
    searchQuery,
    pagination,

    // Methods
    onSearchInput,
    onPageChange,
    fetchDreams,
  };
}

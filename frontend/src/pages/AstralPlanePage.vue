<template>
  <q-page class="q-pa-sm q-pa-md-md">
    <div class="page-container">
      <!-- Header -->
      <div class="row items-center q-mb-md">
        <q-btn flat round icon="arrow_back" @click="router.push('/dreams')" class="q-mr-sm" />
        <div class="text-h6 text-weight-medium">The Astral Plane</div>
      </div>

      <!-- Search Section -->
      <div class="q-mb-md">
        <q-input
          v-model="searchQuery"
          outlined
          placeholder="Search public dreams..."
          clearable
          class="q-mb-sm"
          @update:model-value="onSearchInput"
        >
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
        </q-input>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="text-center q-pa-lg">
        <q-spinner-dots size="40px" color="primary" />
        <div class="text-subtitle2 q-mt-md">Loading dreams from The Astral Plane...</div>
      </div>

      <!-- Dreams List -->
      <div v-else-if="dreams.length > 0" class="dreams-list">
        <DreamCard
          v-for="dream in dreams"
          :key="dream.id"
          :dream="dream"
          :show-anonymous="true"
          card-class="astral-style"
          @click="openDream"
        />
      </div>

      <!-- Empty state -->
      <q-card v-else flat bordered class="text-center q-pa-lg">
        <q-icon name="visibility" size="48px" color="grey-5" class="q-mb-md" />
        <div class="text-subtitle1 text-grey-6 q-mb-sm">
          {{ searchQuery ? `No dreams found for "${searchQuery}"` : 'No public dreams yet' }}
        </div>
        <div class="text-body2 text-grey-5">
          {{
            searchQuery
              ? 'Try a different search term'
              : 'Be the first to share a dream in The Astral Plane!'
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
  </q-page>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { dreamsApi } from 'src/services/web';
import type { Dream } from 'src/types/models';
import { useDreamsList } from 'src/composables/useDreamsList';
import PaginationComponent from 'components/PaginationComponent.vue';
import DreamCard from 'components/DreamCard.vue';

const router = useRouter();

// Astral Plane dreams fetcher
const astralFetcher = (page = 1, search?: string) => {
  const params = new URLSearchParams();

  if (page > 1) {
    params.append('page', page.toString());
  }

  if (search) {
    params.append('search', search);
  }

  return dreamsApi.getAstralPlane(params.toString());
};

// Use shared dreams list logic
const { loading, dreams, searchQuery, pagination, onSearchInput, onPageChange } = useDreamsList({
  fetchFunction: astralFetcher,
});

const openDream = (dream: Dream): void => {
  // Public dreams are always viewed in read-only mode
  void router.push(`/dreams/${dream.id}`);
};
</script>

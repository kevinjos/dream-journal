<template>
  <q-page class="q-pa-md">
    <div class="quality-cloud-container">
      <!-- Header -->
      <div class="row items-center q-mb-md">
        <q-btn flat round icon="arrow_back" @click="router.push('/')" class="q-mr-sm" />
        <div class="text-h6 text-weight-medium">Dream Cloud</div>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="text-center q-pa-lg">
        <q-spinner-dots size="40px" color="primary" />
        <div class="text-subtitle2 q-mt-md">Loading qualities...</div>
      </div>

      <!-- D3 Word Cloud -->
      <div v-else-if="qualities.length > 0">
        <div ref="wordCloudContainer" class="word-cloud-svg"></div>
      </div>

      <!-- Empty state -->
      <q-card v-else flat bordered class="text-center q-pa-lg">
        <q-icon name="cloud" size="48px" color="grey-5" class="q-mb-md" />
        <div class="text-subtitle1 text-grey-6 q-mb-sm">No qualities yet</div>
        <div class="text-body2 text-grey-5">
          Create dreams with qualities to see your word cloud
        </div>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { qualitiesApi } from 'src/services/web';
import * as d3 from 'd3';
import type { Quality } from 'components/models';

interface QualityNode extends Quality, d3.SimulationNodeDatum {
  x?: number;
  y?: number;
}

const router = useRouter();
const $q = useQuasar();
const loading = ref(true);
const qualities = ref<Quality[]>([]);
const wordCloudContainer = ref<HTMLDivElement>();

const createWordCloud = async (): Promise<void> => {
  if (!wordCloudContainer.value || qualities.value.length === 0) return;

  // Clear previous content
  d3.select(wordCloudContainer.value).selectAll('*').remove();

  const container = wordCloudContainer.value;
  // Let CSS handle both width and height - SVG will inherit from container

  // Create SVG with zoom container - let it inherit width and height from CSS
  const svg = d3.select(container).append('svg').style('width', '100%').style('height', '100%');

  // Create a group for zoom/pan transformations
  const zoomGroup = svg.append('g');

  // Set up zoom behavior
  const zoom = d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.5, 3]) // Allow zoom from 50% to 300%
    .on('zoom', (event) => {
      zoomGroup.attr('transform', event.transform);
    });

  // Apply zoom behavior to SVG
  svg.call(zoom);

  // Create scales
  const maxFrequency = Math.max(...qualities.value.map((q) => q.frequency));
  const minFrequency = Math.min(...qualities.value.map((q) => q.frequency));

  const fontScale = d3.scaleLinear().domain([minFrequency, maxFrequency]).range([16, 48]);

  // Use Quasar's named color variables from the existing scheme
  const computedStyle = getComputedStyle(document.documentElement);
  const primaryColor = computedStyle.getPropertyValue('--q-primary').trim();
  const secondaryColor = computedStyle.getPropertyValue('--q-secondary').trim();

  // Get theme colors for random text selection colors
  const textColors = [
    computedStyle.getPropertyValue('--q-positive').trim(), // success/green
    computedStyle.getPropertyValue('--q-warning').trim(), // warning/orange
    computedStyle.getPropertyValue('--q-negative').trim(), // error/red
    computedStyle.getPropertyValue('--q-info').trim(), // info/blue
    computedStyle.getPropertyValue('--q-accent').trim(), // accent color
    secondaryColor, // include secondary as an option
  ].filter((color) => color); // Remove any empty values

  // Pick a random text color from theme
  const getRandomTextColor = () =>
    textColors[Math.floor(Math.random() * textColors.length)] || secondaryColor;

  // Convert qualities to simulation nodes
  const nodes: QualityNode[] = qualities.value.map((q) => ({ ...q }));

  // Simple spiral placement algorithm
  // Wait for SVG to render with CSS dimensions
  await new Promise((resolve) => setTimeout(resolve, 10));

  // Get actual SVG dimensions after CSS styling
  const svgRect = svg.node()!.getBoundingClientRect();
  const actualWidth = svgRect.width;
  const actualHeight = svgRect.height;

  // Set viewBox to match actual dimensions
  svg
    .attr('viewBox', `0 0 ${actualWidth} ${actualHeight}`)
    .attr('preserveAspectRatio', 'xMidYMid meet');

  const centerX = actualWidth / 2;
  const centerY = actualHeight / 2;
  const spiral = d3.range(nodes.length).map((_, i) => {
    const angle = i * 0.5;
    const radius = Math.sqrt(i) * 20;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });

  // Set initial positions
  nodes.forEach((node, i) => {
    const pos = spiral[i];
    if (pos) {
      node.x = pos.x;
      node.y = pos.y;
    }
  });

  // Create text elements in the zoom group
  const textElements = zoomGroup
    .selectAll('text')
    .data(nodes)
    .enter()
    .append('text')
    .text((d) => d.name)
    .attr('x', 0)
    .attr('y', 0)
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .attr('transform', (d) => `translate(${d.x || centerX}, ${d.y || centerY}) scale(1)`)
    .style('font-size', (d) => `${fontScale(d.frequency)}px`)
    .style('font-weight', 'bold')
    .style('fill', primaryColor)
    .style('cursor', 'pointer')
    .style('user-select', 'none');

  // Add hover, touch, and click interactions
  textElements
    .on('mouseover', function (_, d) {
      d3.select(this)
        .style('fill', secondaryColor)
        .attr('transform', `translate(${d.x || centerX}, ${d.y || centerY}) scale(1.1)`);
    })
    .on('mouseout', function (_, d) {
      d3.select(this)
        .style('fill', primaryColor)
        .attr('transform', `translate(${d.x || centerX}, ${d.y || centerY}) scale(1)`);
    })
    // Add touch support for mobile
    .on('touchstart', function (event) {
      event.preventDefault();
    })
    .on('click touchend', function (event, d) {
      event.preventDefault();

      // Reset all text elements to normal state
      textElements.each(function (nodeData) {
        const node = nodeData;
        d3.select(this)
          .style('fill', primaryColor)
          .style('stroke', 'none')
          .attr('transform', `translate(${node.x || centerX}, ${node.y || centerY}) scale(1)`)
          .attr('x', 0)
          .attr('y', 0);
      });

      // Apply persistent selection styling
      const randomColor = getRandomTextColor();
      d3.select(this)
        .style('fill', randomColor)
        .attr('transform', `translate(${d.x || centerX}, ${d.y || centerY}) scale(1.2)`);

      // Show notification with quality info and matching color
      $q.notify({
        message: `<strong style="color: ${randomColor}">${d.name}</strong> appears in ${d.frequency} dream${d.frequency === 1 ? '' : 's'}`,
        color: 'primary',
        position: 'bottom',
        timeout: 4000,
        html: true,
        actions: [
          {
            label: 'View Dreams',
            color: 'white',
            handler: () => {
              void viewDreamsWithQuality(d);
            },
          },
          { label: 'Dismiss', color: 'white' },
        ],
      });
    });

  // Collision detection and repositioning
  const simulation = d3
    .forceSimulation(nodes)
    .force(
      'collision',
      d3.forceCollide<QualityNode>().radius((d) => fontScale(d.frequency) / 2 + 8),
    )
    .force('center', d3.forceCenter(centerX, centerY))
    .force('charge', d3.forceManyBody().strength(-30))
    .on('tick', () => {
      textElements.attr('transform', (d) => {
        const safeX = Math.max(60, Math.min(actualWidth - 60, d.x || centerX));
        const safeY = Math.max(30, Math.min(actualHeight - 60, d.y || centerY));
        // Update the node position data
        d.x = safeX;
        d.y = safeY;
        return `translate(${safeX}, ${safeY}) scale(1)`;
      });
    });

  // Run simulation for positioning, then stop completely
  for (let i = 0; i < 150; ++i) simulation.tick();

  // Final positioning with safe margins
  textElements.attr('transform', (d) => {
    const safeX = Math.max(60, Math.min(actualWidth - 60, d.x || centerX));
    const safeY = Math.max(30, Math.min(actualHeight - 60, d.y || centerY));
    d.x = safeX;
    d.y = safeY;
    return `translate(${safeX}, ${safeY}) scale(1)`;
  });

  // Stop and remove simulation to prevent further movement
  simulation.stop();
  simulation.nodes([]);
};

const viewDreamsWithQuality = (quality: Quality): void => {
  // Navigate to dreams page with quality filter
  void router.push({
    path: '/dreams',
    query: { quality: quality.id.toString() },
  });
};

const fetchQualities = async (): Promise<void> => {
  try {
    loading.value = true;
    const response = await qualitiesApi.list();
    qualities.value = response.data.results || response.data || [];

    // Wait for DOM to be fully rendered
    await nextTick();

    // Small delay to ensure container has dimensions
    setTimeout(() => {
      void createWordCloud();
    }, 50);
  } catch (error) {
    console.error('Error fetching qualities:', error);
  } finally {
    loading.value = false;
  }
};

// Watch for when loading finishes and container is available
watch([loading, wordCloudContainer], ([isLoading, container]) => {
  if (!isLoading && container && qualities.value.length > 0) {
    setTimeout(() => {
      void createWordCloud();
    }, 100);
  }
});

onMounted(() => {
  void fetchQualities();
});
</script>

<style scoped>
.quality-cloud-container {
  max-width: 1000px;
  margin: 0 auto;
}

.word-cloud-svg {
  width: 100%;
  height: calc(100vh - 160px); /* Back to original approach */
  min-height: 350px;
  border: 1px solid var(--q-separator-color);
  border-radius: 8px;
  background: var(--q-page-background);
}

/* Mobile-first responsive design */
@media (max-width: 600px) {
  .quality-cloud-container {
    max-width: 100%;
  }

  .word-cloud-svg {
    height: calc(100vh - 160px); /* Same as desktop for now */
    min-height: 300px;
  }
}
</style>

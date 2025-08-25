<template>
  <q-page class="q-pa-sm q-pa-md-md column">
    <!-- Header -->
    <div class="row items-center q-mb-md">
      <q-btn flat round icon="arrow_back" @click="router.push('/')" class="q-mr-sm" />
      <div class="text-h6 text-weight-medium">Dream Cloud</div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-center q-pa-lg col-grow">
      <q-spinner-dots size="40px" color="primary" />
      <div class="text-subtitle2 q-mt-md">Loading qualities...</div>
    </div>

    <!-- D3 Word Cloud -->
    <div v-else-if="qualities.length > 0" class="col-grow column">
      <div ref="wordCloudContainer" class="word-cloud-svg full-width col-grow"></div>
    </div>

    <!-- Empty state -->
    <q-card v-else flat bordered class="text-center q-pa-lg">
      <q-icon name="cloud" size="48px" color="grey-5" class="q-mb-md" />
      <div class="text-subtitle1 text-grey-6 q-mb-sm">No qualities yet</div>
      <div class="text-body2 text-grey-5">Create dreams with qualities to see your word cloud</div>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { qualitiesApi } from 'src/services/web';
import * as d3 from 'd3';
import type { Quality } from 'src/types/models';

interface QualityNode extends d3.SimulationNodeDatum, Quality {
  fontSize: number;
  rotate: number;
  width: number;
  height: number;
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

  // Reduce font size range to allow more words to fit
  const fontScale = d3.scaleLinear().domain([minFrequency, maxFrequency]).range([14, 32]);

  // Use Quasar's themed colors
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

  // Helper function to calculate text dimensions
  const getTextDimensions = (
    text: string,
    fontSize: number,
    rotate: number,
  ): { width: number; height: number } => {
    // Create temporary text element to measure dimensions
    const tempText = svg
      .append('text')
      .text(text)
      .style('font-size', `${fontSize}px`)
      .style('font-weight', 'bold')
      .style('visibility', 'hidden');

    const bbox = tempText.node()!.getBBox();
    tempText.remove();

    // For rotated text, swap width and height
    if (rotate === 90) {
      return { width: bbox.height, height: bbox.width };
    }
    return { width: bbox.width, height: bbox.height };
  };

  // Check if two nodes overlap (with padding)
  const nodesOverlap = (a: QualityNode, b: QualityNode, padding: number = 5): boolean => {
    if (!a.x || !a.y || !b.x || !b.y || !a.width || !a.height || !b.width || !b.height)
      return false;

    const aLeft = a.x - a.width / 2 - padding;
    const aRight = a.x + a.width / 2 + padding;
    const aTop = a.y - a.height / 2 - padding;
    const aBottom = a.y + a.height / 2 + padding;

    const bLeft = b.x - b.width / 2 - padding;
    const bRight = b.x + b.width / 2 + padding;
    const bTop = b.y - b.height / 2 - padding;
    const bBottom = b.y + b.height / 2 + padding;

    return !(aRight < bLeft || aLeft > bRight || aBottom < bTop || aTop > bBottom);
  };

  // Create word cloud nodes with rotation assignment
  const nodes: QualityNode[] = qualities.value.map((q) => {
    const fontSize = fontScale(q.frequency);
    // 15% chance for vertical text (90° rotation)
    const rotate = Math.random() < 0.15 ? 90 : 0;
    const dimensions = getTextDimensions(q.name, fontSize, rotate);

    return {
      ...q,
      fontSize,
      rotate,
      width: dimensions.width,
      height: dimensions.height,
      x: centerX + (Math.random() - 0.5) * 100, // Start near center
      y: centerY + (Math.random() - 0.5) * 100,
    };
  });

  // Custom collision detection and positioning
  const positionNodes = (): void => {
    const maxAttempts = 1000;
    const padding = 8;

    // Sort by frequency (larger words placed first)
    nodes.sort((a, b) => b.frequency - a.frequency);

    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i]!;
      let placed = false;

      if (i === 0) {
        // Place first (largest) node at center
        node.x = centerX;
        node.y = centerY;
        placed = true;
      } else {
        // Try to place subsequent nodes using spiral pattern
        for (let attempt = 0; attempt < maxAttempts && !placed; attempt++) {
          const angle = attempt * 0.3;
          const radius = attempt * 2;

          node.x = centerX + Math.cos(angle) * radius;
          node.y = centerY + Math.sin(angle) * radius;

          // Check bounds
          if (
            node.x - node.width / 2 < 0 ||
            node.x + node.width / 2 > actualWidth ||
            node.y - node.height / 2 < 0 ||
            node.y + node.height / 2 > actualHeight
          ) {
            continue;
          }

          // Check collisions with already placed nodes
          let hasCollision = false;
          for (let j = 0; j < i; j++) {
            if (nodesOverlap(node, nodes[j]!, padding)) {
              hasCollision = true;
              break;
            }
          }

          if (!hasCollision) {
            placed = true;
          }
        }
      }

      // If we couldn't place the node, skip it
      if (!placed) {
        nodes.splice(i, 1);
        i--;
      }
    }
  };

  // Position all nodes
  positionNodes();

  // Create text elements
  const textElements = zoomGroup
    .selectAll('text')
    .data(nodes)
    .enter()
    .append('text')
    .text((d) => d.name)
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .attr('transform', (d) => `translate(${d.x}, ${d.y}) rotate(${d.rotate})`)
    .style('font-size', (d) => `${d.fontSize}px`)
    .style('font-weight', 'bold')
    .style('fill', primaryColor)
    .style('cursor', 'pointer')
    .style('user-select', 'none');

  // Add hover, touch, and click interactions
  textElements
    .on('mouseover', function (_, d: QualityNode) {
      d3.select(this)
        .style('fill', secondaryColor)
        .attr('transform', `translate(${d.x}, ${d.y}) rotate(${d.rotate}) scale(1.1)`);
    })
    .on('mouseout', function (_, d: QualityNode) {
      d3.select(this)
        .style('fill', primaryColor)
        .attr('transform', `translate(${d.x}, ${d.y}) rotate(${d.rotate}) scale(1)`);
    })
    // Add touch support for mobile
    .on('touchstart', function (event) {
      event.preventDefault();
    })
    .on('click touchend', function (event, d: QualityNode) {
      event.preventDefault();

      // Reset all text elements to normal state
      textElements.each(function (nodeData: QualityNode) {
        d3.select(this)
          .style('fill', primaryColor)
          .style('stroke', 'none')
          .attr(
            'transform',
            `translate(${nodeData.x}, ${nodeData.y}) rotate(${nodeData.rotate}) scale(1)`,
          );
      });

      // Apply persistent selection styling
      const randomColor = getRandomTextColor();
      d3.select(this)
        .style('fill', randomColor)
        .attr('transform', `translate(${d.x}, ${d.y}) rotate(${d.rotate}) scale(1.2)`);

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
.word-cloud-svg {
  height: calc(100vh - 160px);
  min-height: 350px;
  border: 1px solid var(--q-separator-color);
  border-radius: 8px;
  background: var(--q-page-background);
  overflow: hidden;
}
</style>

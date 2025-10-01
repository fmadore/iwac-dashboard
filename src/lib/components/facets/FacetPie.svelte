<script lang="ts">
  import * as Card from '$lib/components/ui/card/index.js';
  import EChartsPieChart from '$lib/components/charts/EChartsPieChart.svelte';

  interface PieItem { label: string; value: number; color?: string }

  let { title = 'Facet', data = [] }: { title?: string; data?: PieItem[] } = $props();
</script>

<Card.Root>
  <Card.Header>
    <Card.Title>{title}</Card.Title>
  </Card.Header>
  <Card.Content>
    <div class="mx-auto aspect-square max-h-[400px] flex items-center justify-center">
      {#if data.length > 0}
        <EChartsPieChart
          data={data}
          innerRadius="40%"
          outerRadius="75%"
          showLabels={true}
          showValues={false}
          animationDuration={800}
          minSlicePercent={0.5}
        />
      {:else}
        <div class="flex items-center justify-center h-[200px] text-muted-foreground">No data</div>
      {/if}
    </div>
  </Card.Content>
</Card.Root>

<script lang="ts">
  import * as Card from '$lib/components/ui/card/index.js';
  import PieChart from '$lib/components/charts/PieChart.svelte';

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
        <PieChart
          data={data}
          innerRadius={60}
          outerRadius={160}
          showLabels={true}
          showValues={false}
          animationDuration={800}
          padAngle={0.01}
          cornerRadius={4}
        />
      {:else}
        <div class="flex items-center justify-center h-[200px] text-muted-foreground">No data</div>
      {/if}
    </div>
  </Card.Content>
</Card.Root>

<script lang="ts">
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import { Card } from '$lib/components/ui/card/index.js';
  import EntitiesTable from '$lib/components/entities-table.svelte';
  import BarChart from '$lib/components/charts/BarChart.svelte';
  import { t } from '$lib/stores/translationStore.js';

  type ApiChartData = { labels?: string[]; values?: number[] };
  type ChartDataItem = { category: string; documents: number };

  let chartData = $state<ChartDataItem[]>([]);
  let isLoading = $state(true);
  let fetchError = $state<string | null>(null);

  async function loadChartData() {
    try {
      const response = await fetch(`${base}/data/index-types.json`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const payload = (await response.json()) as ApiChartData;
      const labels = payload.labels ?? [];
      const values = payload.values ?? [];

      chartData = labels.map((category, index) => ({
        category,
        documents: values[index] ?? 0
      }));
      fetchError = null;
    } catch (error) {
      console.error('Failed to load index-types.json', error);
      fetchError = $t('common.error');
      chartData = [];
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadChartData();
  });
</script>

<div class="space-y-6">
  <div>
    <h2 class="text-3xl font-bold tracking-tight">{$t('nav.index')}</h2>
    <p class="text-muted-foreground">Top entity types by count</p>
  </div>

  <Card class="p-4">
    {#if isLoading}
      <div class="grid h-96 place-items-center text-sm text-muted-foreground">
        {$t('common.loading')}
      </div>
    {:else if fetchError}
      <div class="grid h-96 place-items-center text-sm text-destructive">
        {fetchError}
      </div>
    {:else if !chartData.length}
      <div class="grid h-96 place-items-center text-sm text-muted-foreground">
        {$t('chart.no_data')}
      </div>
    {:else}
      <div class="w-full h-96">
        <BarChart 
          data={chartData}
          barColor="var(--chart-1)"
          hoverColor="var(--chart-2)"
          maxLabelLength={10}
          animationDuration={750}
        />
      </div>
    {/if}
  </Card>

  <EntitiesTable />
</div>

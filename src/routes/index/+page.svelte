<script lang="ts">
  import { onMount } from 'svelte';
  // Avoid direct type import from 'echarts' to prevent TS 2497; use any-typed dynamic modules instead.
  import { Card } from '$lib/components/ui/card/index.js';
  import { t } from '$lib/stores/translationStore.js';
  import { base } from '$app/paths';
  import EntitiesTable from '$lib/components/entities-table.svelte';

  let chartEl = $state<HTMLDivElement | null>(null);
  let chart = $state<any>(null);
  let echarts = $state<any>(null);

  type ChartData = { labels: string[]; values: number[] };

  async function ensureChart() {
    if (!echarts) {
      const coreMod: any = await import('echarts/core');
      const chartsMod: any = await import('echarts/charts');
      const compsMod: any = await import('echarts/components');
      const renderersMod: any = await import('echarts/renderers');
      echarts = coreMod;
      coreMod.use([
        chartsMod.BarChart,
        compsMod.GridComponent,
        compsMod.TooltipComponent,
        compsMod.TitleComponent,
        compsMod.LegendComponent,
        renderersMod.CanvasRenderer
      ]);
    }
    if (echarts && chartEl && !chart) {
      chart = echarts.init(chartEl);
    }
  }

  async function renderChart(data: ChartData) {
    if (!chartEl) return;
    await ensureChart();
    if (!chart || !echarts) return;
    const { labels, values } = data;
    const option = {
      title: { text: $t('nav.index') },
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 40, bottom: 40 },
      xAxis: { type: 'category', data: labels, axisLabel: { interval: 0, rotate: 30 } },
      yAxis: { type: 'value', name: $t('chart.documents') },
      series: [
        {
          type: 'bar',
          name: $t('chart.documents'),
          data: values,
          showBackground: true,
          itemStyle: { color: '#4f46e5' },
          emphasis: { focus: 'series' }
        }
      ]
    };
    chart.setOption(option);
    chart.resize();
  }

  onMount(() => {
    const url = `${base}/data/index-types.json`;
    fetch(url)
      .then((r) => r.json())
      .then((json: ChartData) => {
        renderChart({ labels: json.labels ?? [], values: json.values ?? [] });
      })
      .catch((err) => {
        console.error('Failed to load index-types.json', err);
      });
    
    // Handle window resize for chart responsiveness
    const handleResize = () => {
      if (chart) {
        chart.resize();
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      chart?.dispose();
      chart = null;
    };
  });

  // Use effect to resize chart when it becomes available
  $effect(() => {
    if (chart && chartEl) {
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        chart.resize();
      }, 100);
    }
  });
</script>

<div class="w-full max-w-none space-y-6 overflow-x-hidden">
  <div>
    <h2 class="text-3xl font-bold tracking-tight">{$t('nav.index')}</h2>
    <p class="text-muted-foreground">Top entity types by count</p>
  </div>

  <!-- Vertical layout: chart on top, table below -->
  <div class="space-y-6 w-full">
    <!-- Chart Section -->
    <div class="w-full">
      <Card class="p-4 w-full">
        <div bind:this={chartEl} class="w-full h-[400px]"></div>
      </Card>
    </div>

    <!-- Table Section -->
    <div class="w-full">
      <EntitiesTable />
    </div>
  </div>
</div>

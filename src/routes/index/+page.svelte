<script lang="ts">
  import { onMount } from 'svelte';
  // Avoid direct type import from 'echarts' to prevent TS 2497; use any-typed dynamic modules instead.
  import { Card } from '$lib/components/ui/card/index.js';
  import { t } from '$lib/stores/translationStore.js';
  import { base } from '$app/paths';

  let chartEl: HTMLDivElement | null = null;
  let chart: any = null;
  let echarts: any = null;
  let unsubscribe: () => void;

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
    return () => {
      chart?.dispose();
      chart = null;
    };
  });
</script>

<div class="space-y-6">
  <div>
    <h2 class="text-3xl font-bold tracking-tight">{$t('nav.index')}</h2>
    <p class="text-muted-foreground">Top entity types by count</p>
  </div>

  <Card class="p-6">
    <div bind:this={chartEl} class="h-[420px] w-full"></div>
  </Card>
</div>

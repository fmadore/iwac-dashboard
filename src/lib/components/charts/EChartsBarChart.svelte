<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { t, languageStore } from '$lib/stores/translationStore.js';

  interface ChartDataItem {
    category: string;
    documents: number;
    originalKey?: string;
  }

  interface Props {
    data?: ChartDataItem[];
    height?: number;
    animationDuration?: number;
    useMultipleColors?: boolean;
  }

  let {
    data = [],
    height = 400,
    animationDuration = 750,
    useMultipleColors = false
  }: Props = $props();

  let chartContainer: HTMLDivElement;
  let chartInstance: any = $state(null);
  let echarts: any = $state(null);
  let themeClass = $state(''); // Track theme changes for reactivity

  // Get computed CSS variable value
  function getCSSVariable(variable: string): string {
    if (!browser) return '#000000';
    const root = document.documentElement;
    const value = getComputedStyle(root).getPropertyValue(variable).trim();
    
    // If it's an oklch color, we need to convert it or use a fallback
    if (value.startsWith('oklch')) {
      // For simplicity, return a mapped color based on the variable name
      const colorMap: Record<string, string> = {
        '--chart-1': '#e8590c',
        '--chart-2': '#2563eb',
        '--chart-3': '#16a34a',
        '--chart-4': '#f59e0b',
        '--chart-5': '#dc2626',
        '--foreground': '#09090b',
        '--muted-foreground': '#71717a',
        '--background': '#ffffff',
        '--popover': '#ffffff',
        '--popover-foreground': '#09090b',
        '--border': '#e4e4e7'
      };
      return colorMap[variable] || '#666666';
    }
    return value || '#666666';
  }

  // Color mapping based on original English keys (language-independent)
  const categoryColorMap: Record<string, string> = {
    'Events': '--chart-1',
    'Locations': '--chart-2',
    'Organizations': '--chart-3',
    'Persons': '--chart-4',
    'Topics': '--chart-5'
  };

  // Get color for each category based on originalKey
  function getColorForCategory(item: ChartDataItem, index: number): string {
    if (!useMultipleColors) {
      return getCSSVariable('--chart-1');
    }

    // Use originalKey if available, otherwise fall back to category
    const key = item.originalKey || item.category;
    const colorVar = categoryColorMap[key];
    if (colorVar) {
      return getCSSVariable(colorVar);
    }

    // Fallback to cycling through chart colors
    const chartColors = ['--chart-1', '--chart-2', '--chart-3', '--chart-4', '--chart-5'];
    return getCSSVariable(chartColors[index % chartColors.length]);
  }

  onMount(() => {
    if (!browser) return;

    let resizeObserver: ResizeObserver | undefined;

    // Dynamically import and initialize ECharts
    import('echarts').then((echartsModule) => {
      echarts = echartsModule.default || echartsModule;

      // Initialize chart
      if (chartContainer) {
        chartInstance = echarts.init(chartContainer);
        updateChart();

        // Handle window resize
        resizeObserver = new ResizeObserver(() => {
          chartInstance?.resize();
        });
        resizeObserver.observe(chartContainer);
      }
    });

    return () => {
      resizeObserver?.disconnect();
      chartInstance?.dispose();
    };
  });

  // Update chart when data or language changes
  $effect(() => {
    if (chartInstance && echarts && data.length > 0) {
      // Access $languageStore to make this effect reactive to language changes
      // We need to actually USE the value, not just declare it
      const currentLang = $languageStore;
      // Also trigger on data changes by accessing it
      const currentData = data;
      // Force update on any of these changes
      updateChart();
    }
  });

  function updateChart() {
    if (!chartInstance || !data.length) return;

    const categories = data.map(d => d.category);
    const values = data.map(d => d.documents);

    // Get fresh CSS variables on each update (important for theme changes)
    const foregroundColor = getCSSVariable('--foreground');
    const borderColor = getCSSVariable('--border');
    const popoverBg = getCSSVariable('--popover');
    const popoverFg = getCSSVariable('--popover-foreground');

    const option = {
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLabel: {
          rotate: 45,
          color: foregroundColor,
          fontSize: 12,
          formatter: (value: string) => {
            return value.length > 10 ? value.substring(0, 10) + '...' : value;
          }
        },
        axisLine: {
          lineStyle: {
            color: borderColor,
            opacity: 1
          }
        },
        axisTick: {
          lineStyle: {
            color: borderColor,
            opacity: 1
          }
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: foregroundColor,
          fontSize: 12
        },
        axisLine: {
          lineStyle: {
            color: borderColor,
            opacity: 1
          }
        },
        axisTick: {
          lineStyle: {
            color: borderColor,
            opacity: 1
          }
        },
        splitLine: {
          lineStyle: {
            color: borderColor,
            opacity: 0.3
          }
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        backgroundColor: popoverBg,
        borderColor: borderColor,
        textStyle: {
          color: popoverFg
        },
        formatter: (params: any) => {
          const param = params[0];
          return `${param.name}<br/><strong>${param.value}</strong> ${$t('chart.documents').toLowerCase()}`;
        }
      },
      series: [
        {
          type: 'bar',
          data: data.map((d, index) => ({
            value: d.documents,
            itemStyle: {
              color: getColorForCategory(d, index),
              borderRadius: [4, 4, 0, 0]
            }
          })),
          emphasis: {
            itemStyle: {
              opacity: 0.8
            }
          },
          animationDuration: animationDuration,
          animationEasing: 'cubicOut'
        }
      ]
    };

    chartInstance.setOption(option);
  }

  // Watch for theme changes (light/dark mode) via MutationObserver
  onMount(() => {
    if (browser) {
      // Initialize theme class
      themeClass = document.documentElement.className;
      
      const observer = new MutationObserver(() => {
        themeClass = document.documentElement.className;
      });
      
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class']
      });

      return () => observer.disconnect();
    }
  });

  // Update chart when theme changes
  $effect(() => {
    if (chartInstance && themeClass !== undefined) {
      // This will trigger whenever themeClass changes
      updateChart();
    }
  });
</script>

<div 
  bind:this={chartContainer}
  class="w-full bg-card text-card-foreground"
  style="height: {height}px;"
  role="img"
  aria-label="Bar chart showing document counts by category"
></div>

<style>
  div {
    min-height: 300px;
  }
</style>

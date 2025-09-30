<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { t, languageStore } from '$lib/stores/translationStore.js';
  import type { Language } from '$lib/stores/translationStore.js';

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
  let resizeObserver: ResizeObserver | undefined;
  let previousThemeClass: string | null = null;
  let lastLanguage: Language | null = null;
  let lastCategoriesSignature: string | null = null;

  const colorParsingCanvas = browser ? document.createElement('canvas') : null;
  const colorParsingContext = colorParsingCanvas?.getContext('2d', { willReadFrequently: false });

  // Get computed CSS variable value
  function parseColor(value: string): string | null {
    if (!colorParsingContext) return null;
    try {
      // Reset fillStyle to avoid retaining invalid values
      colorParsingContext.fillStyle = '#000000';
      colorParsingContext.fillStyle = value;
      return colorParsingContext.fillStyle || null;
    } catch (error) {
      return null;
    }
  }

  function getCSSVariable(variable: string): string {
    if (!browser) return '#000000';
    const root = document.documentElement;
    const value = getComputedStyle(root).getPropertyValue(variable).trim();

    if (value) {
      const parsed = parseColor(value);
      if (parsed) {
        return parsed;
      }
    }

    const fallbackMap: Record<string, string> = {
      '--chart-1': '#e8590c',
      '--chart-2': '#2563eb',
      '--chart-3': '#16a34a',
      '--chart-4': '#f59e0b',
      '--chart-5': '#dc2626',
      '--chart-6': '#ec4899',
      '--chart-7': '#06b6d4',
      '--chart-8': '#f472b6',
      '--chart-9': '#84cc16',
      '--chart-10': '#10b981',
      '--foreground': '#09090b',
      '--muted-foreground': '#71717a',
      '--background': '#ffffff',
      '--popover': '#ffffff',
      '--popover-foreground': '#09090b',
      '--border': '#e4e4e7'
    };

    return fallbackMap[variable] || value || '#666666';
  }

  // Color mapping based on original English keys (language-independent)
  const categoryColorMap: Record<string, string> = {
    'Persons': '--chart-1',
    'Locations': '--chart-2',
    'Organizations': '--chart-3',
    'Authority Files': '--chart-4',
    'Events': '--chart-5',
    'Topics': '--chart-6'
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
    const chartColors = ['--chart-1', '--chart-2', '--chart-3', '--chart-4', '--chart-5', '--chart-6', '--chart-7', '--chart-8', '--chart-9', '--chart-10'];
    return getCSSVariable(chartColors[index % chartColors.length]);
  }

  function attachResizeObserver() {
    if (!chartContainer || resizeObserver) return;
    resizeObserver = new ResizeObserver(() => {
      chartInstance?.resize();
    });
    resizeObserver.observe(chartContainer);
  }

  function detachResizeObserver() {
    resizeObserver?.disconnect();
    resizeObserver = undefined;
  }

  async function ensureECharts() {
    if (echarts) return echarts;
    const echartsModule = await import('echarts');
    echarts = echartsModule.default || echartsModule;
    return echarts;
  }

  async function initializeChart() {
    if (!browser || !chartContainer) return;
    await ensureECharts();
    if (!echarts) return;

    chartInstance = echarts.init(chartContainer);
    attachResizeObserver();
    updateChart();
  }

  function destroyChart() {
    detachResizeObserver();
    chartInstance?.dispose();
    chartInstance = null;
  }

  async function reinitializeChart() {
    destroyChart();
    await initializeChart();
  }

  onMount(() => {
    if (!browser) return;

    initializeChart();

    return () => {
      destroyChart();
    };
  });

  // Update chart when data or language changes
  $effect(() => {
    const currentLang = $languageStore;
    const currentData = data;
    const categoriesSignature = currentData
      .map((item) => `${item.category}::${item.documents}`)
      .join('|');

    console.log('🔄 ECharts Effect Triggered', {
      currentLang,
      lastLanguage,
      languageChanged: currentLang !== lastLanguage,
      dataLength: currentData.length,
      categories: currentData.map(d => d.category),
      categoriesSignature,
      lastCategoriesSignature,
      hasEcharts: !!echarts,
      hasChartInstance: !!chartInstance
    });

    if (!browser || !currentData.length) {
      console.log('⚠️ Skipping: browser or no data');
      lastLanguage = currentLang;
      lastCategoriesSignature = categoriesSignature;
      return;
    }

    const languageChanged = currentLang !== lastLanguage;
    const categoriesChanged = categoriesSignature !== lastCategoriesSignature;

    console.log('📊 Change Detection', {
      languageChanged,
      categoriesChanged,
      willReinitialize: languageChanged || categoriesChanged
    });

    lastLanguage = currentLang;
    lastCategoriesSignature = categoriesSignature;

    const syncChart = async () => {
      if (!echarts || !chartInstance) {
        console.log('🔧 Initializing chart (no instance)');
        await initializeChart();
        return;
      }

      if (languageChanged || categoriesChanged) {
        console.log('🔄 Reinitializing chart due to changes');
        await reinitializeChart();
        return;
      }

      console.log('📈 Updating chart (no changes)');
      updateChart();
    };

    void syncChart();
  });

  function updateChart() {
    if (!chartInstance || !data.length) return;

    const categories = data.map(d => d.category);
    const values = data.map(d => d.documents);

    console.log('📈 UpdateChart Called', {
      categories,
      values,
      dataLength: data.length
    });

    // Get fresh CSS variables on each update (important for theme changes)
    const foregroundColor = getCSSVariable('--foreground');
    const borderColor = getCSSVariable('--border');
    const popoverBg = getCSSVariable('--popover');
    const popoverFg = getCSSVariable('--popover-foreground');

    const option = {
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLabel: {
          interval: 0,
          rotate: 45,
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
            disabled: true
          },
          animationDuration: animationDuration,
          animationEasing: 'cubicOut'
        }
      ]
    };

    console.log('📊 Setting ECharts Option', {
      xAxisData: option.xAxis.data,
      seriesDataLength: option.series[0].data.length
    });

    chartInstance.clear();
    chartInstance.setOption(option, true);
    
    console.log('✅ Chart Updated');
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
    if (!browser) {
      return;
    }

    const currentTheme = themeClass;
    if (currentTheme === previousThemeClass) {
      return;
    }

    previousThemeClass = currentTheme;

    if (!echarts) {
      return;
    }

    if (!chartInstance) {
      initializeChart();
      return;
    }

    reinitializeChart();
  });
</script>

<div 
  bind:this={chartContainer}
  class="w-full bg-card text-card-foreground"
  style="height: {height}px;"
  role="img"
  aria-label={$t('chart.documents_by_category_aria')}
></div>

<style>
  div {
    min-height: 300px;
  }
</style>

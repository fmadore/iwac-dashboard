<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  // @ts-expect-error - ECharts module resolution issue
  import * as echarts from 'echarts';

  interface PieDataItem {
    label: string;
    value: number;
    color?: string;
    percentage?: string;
  }

  interface Props {
    data?: PieDataItem[];
    innerRadius?: number | string;
    outerRadius?: number | string;
    showLabels?: boolean;
    showValues?: boolean;
    animationDuration?: number;
    minSlicePercent?: number;
  }

  let {
    data = [],
    innerRadius = '0%',
    outerRadius = '75%',
    showLabels = true,
    showValues = true,
    animationDuration = 1000,
    minSlicePercent = 0.5
  }: Props = $props();

  let chartContainer: HTMLDivElement;
  let chartInstance: any = null;
  let themeClass = $state('');
  let resizeObserver: ResizeObserver | undefined;
  let previousThemeClass: string | null = null;

  const colorParsingCanvas = browser ? document.createElement('canvas') : null;
  const colorParsingContext = colorParsingCanvas?.getContext('2d', { willReadFrequently: false });

  // Get computed CSS variable value - simplified approach matching EChartsBarChart
  function parseColor(value: string): string | null {
    if (!colorParsingContext) return null;
    try {
      // Reset fillStyle to avoid retaining invalid values
      colorParsingContext.fillStyle = '#000000';
      colorParsingContext.fillStyle = value;
      const result = colorParsingContext.fillStyle;
      // Only return if it's not the reset value (meaning parsing succeeded)
      return result !== '#000000' ? result : null;
    } catch (error) {
      return null;
    }
  }

  function getCSSVariable(variable: string): string {
    if (!browser) return '#000000';
    
    // Handle var(--variable-name) format by extracting the variable name
    let varName = variable.trim();
    if (varName.startsWith('var(') && varName.endsWith(')')) {
      varName = varName.slice(4, -1).split(',')[0].trim();
    }
    
    const root = document.documentElement;
    const value = getComputedStyle(root).getPropertyValue(varName).trim();

    if (value) {
      const parsed = parseColor(value);
      if (parsed) {
        return parsed;
      }
      // If parsing failed but we have a value, it might be OKLCH
      // Try to use it directly and let the browser handle it via a temporary div
      if (value.startsWith('oklch(') || value.startsWith('rgb(') || value.startsWith('hsl(')) {
        const tempDiv = document.createElement('div');
        tempDiv.style.color = value;
        document.body.appendChild(tempDiv);
        const computed = getComputedStyle(tempDiv).color;
        document.body.removeChild(tempDiv);
        if (computed && computed !== 'rgba(0, 0, 0, 0)' && computed !== 'rgb(0, 0, 0)') {
          return computed;
        }
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
      '--chart-11': '#6366f1',
      '--chart-12': '#f97316',
      '--chart-13': '#22c55e',
      '--chart-14': '#a855f7',
      '--chart-15': '#ef4444',
      '--chart-16': '#0ea5e9',
      '--foreground': '#09090b',
      '--muted-foreground': '#71717a',
      '--background': '#ffffff',
      '--popover': '#ffffff',
      '--popover-foreground': '#09090b',
      '--border': '#e4e4e7'
    };

    return fallbackMap[varName] || '#666666';
  }

  // Keep track of grouped "Others" data for tooltip
  let othersGroupDetails = $state<PieDataItem[]>([]);

  // Process data to group small slices
  const processedData = $derived(() => {
    if (!data || data.length === 0) return [];
    
    const total = data.reduce((sum, item) => sum + item.value, 0);
    const sortedData = [...data].sort((a, b) => b.value - a.value);
    
    // For heavily skewed data (top slice >90%), show top 5 + others
    const topSlicePercent = (sortedData[0]?.value / total) * 100;
    
    if (topSlicePercent > 90) {
      const mainSlices = sortedData.slice(0, 5);
      const smallSlices = sortedData.slice(5);
      
      if (smallSlices.length > 0) {
        othersGroupDetails = smallSlices; // Store for tooltip
        const othersValue = smallSlices.reduce((sum, item) => sum + item.value, 0);
        return [
          ...mainSlices,
          {
            label: `Others (${smallSlices.length} languages)`,
            value: othersValue,
            color: '--muted-foreground'
          }
        ];
      }
      othersGroupDetails = [];
      return mainSlices;
    }
    
    // For balanced data, use percentage threshold
    const threshold = (minSlicePercent / 100) * total;
    const mainSlices: PieDataItem[] = [];
    const smallSlices: PieDataItem[] = [];
    
    sortedData.forEach((item, index) => {
      if (index < 8 && item.value >= threshold) {
        mainSlices.push(item);
      } else if (item.value < threshold) {
        smallSlices.push(item);
      } else {
        mainSlices.push(item);
      }
    });
    
    if (smallSlices.length > 2) {
      othersGroupDetails = smallSlices; // Store for tooltip
      const othersValue = smallSlices.reduce((sum, item) => sum + item.value, 0);
      return [
        ...mainSlices,
        {
          label: `Others (${smallSlices.length} languages)`,
          value: othersValue,
          color: '--muted-foreground'
        }
      ];
    }
    
    othersGroupDetails = [];
    return [...mainSlices, ...smallSlices];
  });



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

  async function initChart() {
    if (!browser || !chartContainer) return;

    if (chartInstance) {
      chartInstance.dispose();
    }

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
    await initChart();
  }

  function updateChart() {
    if (!chartInstance || processedData().length === 0) return;

    // Get fresh CSS variables on each update
    const foreground = getCSSVariable('--foreground');
    const background = getCSSVariable('--background');
    const popover = getCSSVariable('--popover');
    const popoverForeground = getCSSVariable('--popover-foreground');
    const border = getCSSVariable('--border');

    // Convert data to ECharts format with resolved colors
    const chartData = processedData().map((item, index) => {
      const colorVar = item.color || `--chart-${(index % 16) + 1}`;
      const resolvedColor = getCSSVariable(colorVar);
      return {
        name: item.label,
        value: item.value,
        itemStyle: {
          color: resolvedColor
        }
      };
    });

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const name = params.name;
          const value = params.value;
          const percent = params.percent;
          
          // Check if this is the "Others" category
          if (name.startsWith('Others (') && othersGroupDetails.length > 0) {
            // Build detailed breakdown for Others
            const total = processedData().reduce((sum, item) => sum + item.value, 0);
            const header = `<strong>${name}</strong><br/>${value} (${percent.toFixed(1)}%)<br/><br/>`;
            const details = othersGroupDetails
              .map(item => {
                const itemPercent = ((item.value / total) * 100).toFixed(1);
                return `${item.label}: ${item.value} (${itemPercent}%)`;
              })
              .join('<br/>');
            return header + details;
          }
          
          // Default formatter for regular items
          return `<strong>${name}</strong><br/>${value} (${percent.toFixed(1)}%)`;
        },
        backgroundColor: popover,
        borderColor: border,
        borderWidth: 1,
        textStyle: {
          color: popoverForeground,
          fontSize: 12
        },
        padding: [8, 12],
        extraCssText: 'border-radius: 6px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); max-width: 300px;'
      },
      series: [
        {
          type: 'pie',
          radius: [innerRadius, outerRadius],
          center: ['50%', '50%'],
          data: chartData,
          label: {
            show: showLabels,
            position: 'outside',
            color: foreground,
            fontSize: 12,
            fontWeight: 500,
            formatter: '{b}',
            minMargin: 8,
            lineHeight: 16,
            alignTo: 'none',
            bleedMargin: 10
          },
          labelLine: {
            show: showLabels,
            length: 25,
            length2: 40,
            smooth: 0.2,
            lineStyle: {
              color: foreground,
              opacity: 0.5,
              width: 1
            }
          },
          itemStyle: {
            borderRadius: 4,
            borderColor: background,
            borderWidth: 2
          },
          emphasis: {
            disabled: true
          },
          animationType: 'scale',
          animationEasing: 'elasticOut',
          animationDuration: animationDuration
        }
      ]
    };

    chartInstance.setOption(option, true);
  }

  // Initialize chart on mount
  onMount(() => {
    if (!browser) return;

    initChart();

    return () => {
      destroyChart();
    };
  });

  // Watch for theme changes via MutationObserver
  onMount(() => {
    if (browser) {
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
    if (!browser) return;

    const currentTheme = themeClass;
    if (currentTheme === previousThemeClass) return;

    previousThemeClass = currentTheme;

    if (!chartInstance) return;

    reinitializeChart();
  });

  // Update chart when data changes
  $effect(() => {
    if (chartInstance && processedData().length > 0) {
      updateChart();
    }
  });
</script>

<div 
  bind:this={chartContainer}
  class="w-full h-full min-h-[400px]"
  role="img"
  aria-label="Pie chart showing data distribution"
></div>

<style>
  div {
    container-type: inline-size;
  }
</style>

<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	// @ts-ignore - echarts uses UMD exports
	import * as echarts from 'echarts';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';

	let {
		months = [],
		monthlyAdditions = [],
		cumulativeTotal = []
	} = $props<{
		months: string[];
		monthlyAdditions: number[];
		cumulativeTotal: number[];
	}>();

	// Filter data to start from April 2024 (2024-04)
	const startMonth = '2024-04';
	const filteredData = $derived.by(() => {
		const startIndex = months.findIndex((m) => m >= startMonth);
		if (startIndex === -1) return { months, monthlyAdditions, cumulativeTotal };

		return {
			months: months.slice(startIndex),
			monthlyAdditions: monthlyAdditions.slice(startIndex),
			cumulativeTotal: cumulativeTotal.slice(startIndex)
		};
	});

	let chartContainer: HTMLDivElement;
	let chartInstance: any = null;
	let themeClass = $state('');
	let resizeObserver: ResizeObserver | undefined;

	// Get computed CSS variable value (same as EChartsBarChart)
	function getCSSVariable(variable: string): string {
		if (!browser) return '#000000';
		const root = document.documentElement;
		const value = getComputedStyle(root).getPropertyValue(variable).trim();

		if (value) {
			return value;
		}

		const fallbackMap: Record<string, string> = {
			'--chart-1': '#e8590c',
			'--chart-2': '#2563eb',
			'--foreground': '#09090b',
			'--muted-foreground': '#71717a',
			'--background': '#ffffff',
			'--popover': '#ffffff',
			'--popover-foreground': '#09090b',
			'--border': '#e4e4e7'
		};

		return fallbackMap[variable] || value || '#666666';
	}

	function initChart() {
		if (!chartContainer || !browser) return;

		// Dispose existing instance
		if (chartInstance) {
			chartInstance.dispose();
		}

		chartInstance = echarts.init(chartContainer);

		const filtered = filteredData;

		// Get fresh CSS variables on each update (important for theme changes)
		const foregroundColor = getCSSVariable('--foreground');
		const borderColor = getCSSVariable('--border');
		const popoverBg = getCSSVariable('--popover');
		const popoverFg = getCSSVariable('--popover-foreground');
		const chart1Color = getCSSVariable('--chart-1');
		const chart2Color = getCSSVariable('--chart-2');

		const option: echarts.EChartsOption = {
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'cross',
					crossStyle: {
						color: borderColor
					}
				},
				backgroundColor: popoverBg,
				borderColor: borderColor,
				textStyle: {
					color: popoverFg
				}
			},
			legend: {
				data: [t('timeline.monthly_additions'), t('timeline.cumulative_total')],
				textStyle: {
					color: foregroundColor
				},
				top: 0
			},
			grid: {
				left: '3%',
				right: '4%',
				bottom: '10%',
				top: '15%',
				containLabel: true
			},
			xAxis: [
				{
					type: 'category',
					data: filtered.months,
					axisPointer: {
						type: 'shadow'
					},
					axisLabel: {
						color: foregroundColor,
						rotate: 45,
						formatter: (value: string) => {
							// Format YYYY-MM to shorter form for readability
							const [year, month] = value.split('-');
							return `${month}/${year.slice(2)}`;
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
				}
			],
			yAxis: [
				{
					type: 'value',
					name: t('timeline.monthly_additions'),
					nameTextStyle: {
						color: foregroundColor
					},
					axisLabel: {
						color: foregroundColor
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
				{
					type: 'value',
					name: t('timeline.cumulative_total'),
					nameTextStyle: {
						color: foregroundColor
					},
					axisLabel: {
						color: foregroundColor
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
						show: false
					}
				}
			],
			series: [
				{
					name: t('timeline.monthly_additions'),
					type: 'bar',
					data: filtered.monthlyAdditions,
					itemStyle: {
						color: chart1Color,
						borderRadius: [4, 4, 0, 0]
					},
					emphasis: {
						disabled: true
					}
				},
				{
					name: t('timeline.cumulative_total'),
					type: 'line',
					yAxisIndex: 1,
					data: filtered.cumulativeTotal,
					itemStyle: {
						color: chart2Color
					},
					lineStyle: {
						width: 3,
						color: chart2Color
					},
					smooth: true,
					emphasis: {
						disabled: true
					}
				}
			]
		};

		chartInstance.clear();
		chartInstance.setOption(option, true);
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

	// Re-render chart when language, theme, or data changes
	$effect(() => {
		if (!browser || !chartContainer || months.length === 0) return;

		// Track all dependencies that should trigger re-render
		const _ = languageStore.current;
		const _months = months;
		const _additions = monthlyAdditions;
		const _cumulative = cumulativeTotal;

		initChart();
	});

	// Initialize chart and watch for theme changes
	onMount(() => {
		if (!browser) return;

		// Initialize theme class
		themeClass = document.documentElement.className;

		// Initialize chart
		initChart();
		attachResizeObserver();

		// Watch for theme changes via MutationObserver
		const themeObserver = new MutationObserver(() => {
			const newTheme = document.documentElement.className;
			if (newTheme !== themeClass) {
				themeClass = newTheme;
				if (chartInstance && months.length > 0) {
					initChart(); // Reinitialize with new theme colors
				}
			}
		});

		themeObserver.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['class']
		});

		return () => {
			themeObserver.disconnect();
			detachResizeObserver();
			if (chartInstance) {
				chartInstance.dispose();
				chartInstance = null;
			}
		};
	});
</script>

<div bind:this={chartContainer} class="h-[500px] w-full"></div>

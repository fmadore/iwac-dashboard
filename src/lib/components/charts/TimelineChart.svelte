<script lang="ts">
	import { onMount } from 'svelte';
	// @ts-ignore - echarts uses UMD exports
	import * as echarts from 'echarts';
	import { t, languageStore } from '$lib/stores/translationStore.js';

	let { months = [], monthlyAdditions = [], cumulativeTotal = [] } = $props<{
		months: string[];
		monthlyAdditions: number[];
		cumulativeTotal: number[];
	}>();

	// Filter data to start from April 2024 (2024-04)
	const startMonth = '2024-04';
	const filteredData = $derived(() => {
		const startIndex = months.findIndex(m => m >= startMonth);
		if (startIndex === -1) return { months, monthlyAdditions, cumulativeTotal };
		
		return {
			months: months.slice(startIndex),
			monthlyAdditions: monthlyAdditions.slice(startIndex),
			cumulativeTotal: cumulativeTotal.slice(startIndex)
		};
	});

	let chartContainer: HTMLDivElement;
	let chartInstance: echarts.ECharts | null = null;

	function getThemeColors() {
		const style = getComputedStyle(document.documentElement);
		return {
			foreground: style.getPropertyValue('--foreground').trim(),
			muted: style.getPropertyValue('--muted-foreground').trim(),
			border: style.getPropertyValue('--border').trim(),
			chart1: style.getPropertyValue('--chart-1').trim(),
			chart2: style.getPropertyValue('--chart-2').trim(),
			popover: style.getPropertyValue('--popover').trim(),
			popoverForeground: style.getPropertyValue('--popover-foreground').trim()
		};
	}

	function initChart() {
		if (!chartContainer) return;

		// Dispose existing instance
		if (chartInstance) {
			chartInstance.dispose();
		}

		chartInstance = echarts.init(chartContainer);

		const colors = getThemeColors();
		const filtered = filteredData();

		const option: echarts.EChartsOption = {
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'cross',
					crossStyle: {
						color: colors.muted
					}
				},
				backgroundColor: `hsl(${colors.popover})`,
				borderColor: `hsl(${colors.border})`,
				textStyle: {
					color: `hsl(${colors.popoverForeground})`
				}
			},
			legend: {
				data: [$t('timeline.monthly_additions'), $t('timeline.cumulative_total')],
				textStyle: {
					color: `hsl(${colors.foreground})`
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
						color: `hsl(${colors.foreground})`,
						rotate: 45,
						formatter: (value: string) => {
							// Format YYYY-MM to shorter form for readability
							const [year, month] = value.split('-');
							return `${month}/${year.slice(2)}`;
						}
					},
					axisLine: {
						lineStyle: {
							color: `hsl(${colors.border})`
						}
					}
				}
			],
			yAxis: [
				{
					type: 'value',
					name: $t('timeline.monthly_additions'),
					nameTextStyle: {
						color: `hsl(${colors.foreground})`
					},
					axisLabel: {
						color: `hsl(${colors.foreground})`
					},
					axisLine: {
						lineStyle: {
							color: `hsl(${colors.border})`
						}
					},
					splitLine: {
						lineStyle: {
							color: `hsl(${colors.border})`,
							opacity: 0.3
						}
					}
				},
				{
					type: 'value',
					name: $t('timeline.cumulative_total'),
					nameTextStyle: {
						color: `hsl(${colors.foreground})`
					},
					axisLabel: {
						color: `hsl(${colors.foreground})`
					},
					axisLine: {
						lineStyle: {
							color: `hsl(${colors.border})`
						}
					},
					splitLine: {
						show: false
					}
				}
			],
			series: [
				{
					name: $t('timeline.monthly_additions'),
					type: 'bar',
					data: filtered.monthlyAdditions,
					itemStyle: {
						color: `hsl(${colors.chart1})`
					},
					emphasis: {
						focus: 'series'
					}
				},
				{
					name: $t('timeline.cumulative_total'),
					type: 'line',
					yAxisIndex: 1,
					data: filtered.cumulativeTotal,
					itemStyle: {
						color: `hsl(${colors.chart2})`
					},
					lineStyle: {
						width: 3
					},
					smooth: true,
					emphasis: {
						focus: 'series'
					}
				}
			]
		};

		chartInstance.setOption(option);

		// Handle window resize
		const resizeObserver = new ResizeObserver(() => {
			chartInstance?.resize();
		});
		resizeObserver.observe(chartContainer);

		return () => {
			resizeObserver.disconnect();
		};
	}

	// Re-render chart when language changes or data changes
	$effect(() => {
		if (chartContainer && months.length > 0) {
			// Track language changes
			const _ = $languageStore;
			initChart();
		}
	});

	// Listen for theme changes
	onMount(() => {
		const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
		const handleThemeChange = () => {
			if (chartInstance && months.length > 0) {
				initChart();
			}
		};

		mediaQuery.addEventListener('change', handleThemeChange);

		// Also listen for manual theme changes via data-theme attribute
		const observer = new MutationObserver(handleThemeChange);
		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['data-theme', 'class']
		});

		return () => {
			mediaQuery.removeEventListener('change', handleThemeChange);
			observer.disconnect();
			if (chartInstance) {
				chartInstance.dispose();
			}
		};
	});
</script>

<div bind:this={chartContainer} class="h-[500px] w-full"></div>

<script lang="ts">
	import { onMount } from 'svelte';
	import * as echarts from 'echarts';
	import { languageStore } from '$lib/stores/translationStore.js';

	interface SeriesData {
		name: string;
		data: number[];
	}

	interface Props {
		title?: string;
		years: number[];
		series: SeriesData[];
		height?: string;
		colors?: Record<string, string>;
	}

	let {
		title = '',
		years = [],
		series = [],
		height = '600px',
		colors = {}
	}: Props = $props();

	let chartContainer: HTMLDivElement;
	let chartInstance: echarts.ECharts | null = null;

	// Default colors for document types
	const defaultColors: Record<string, string> = {
		'Press Article': 'var(--chart-1)',
		'Islamic Periodical': 'var(--chart-2)',
		'Document': 'var(--chart-3)',
		'Audiovisuel': 'var(--chart-4)',
		'Reference': 'var(--chart-5)'
	};

	const typeColors = $derived({ ...defaultColors, ...colors });

	function initChart() {
		if (!chartContainer) return;

		if (chartInstance) {
			chartInstance.dispose();
		}

		chartInstance = echarts.init(chartContainer);
		updateChart();
	}

	function updateChart() {
		if (!chartInstance || series.length === 0) return;

		const _ = $languageStore; // Track language changes

		// Get current theme colors
		const textColor = getComputedStyle(document.documentElement)
			.getPropertyValue('--foreground')
			.trim();
		const borderColor = getComputedStyle(document.documentElement)
			.getPropertyValue('--border')
			.trim();

		const option = {
			title: title
				? {
						text: title,
						left: 'center',
						textStyle: {
							color: `oklch(${textColor})`
						}
					}
				: undefined,
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'shadow'
				},
				backgroundColor: `oklch(${getComputedStyle(document.documentElement)
					.getPropertyValue('--popover')
					.trim()})`,
				borderColor: `oklch(${borderColor})`,
				textStyle: {
					color: `oklch(${textColor})`
				}
			},
			legend: {
				data: series.map((s) => s.name),
				top: title ? 40 : 10,
				textStyle: {
					color: `oklch(${textColor})`
				}
			},
			grid: {
				left: '3%',
				right: '4%',
				bottom: '3%',
				top: title ? 100 : 70,
				containLabel: true
			},
			xAxis: {
				type: 'category',
				data: years,
				axisLabel: {
					color: `oklch(${textColor})`,
					rotate: 45
				},
				axisLine: {
					lineStyle: {
						color: `oklch(${borderColor})`
					}
				}
			},
			yAxis: {
				type: 'value',
				axisLabel: {
					color: `oklch(${textColor})`
				},
				axisLine: {
					lineStyle: {
						color: `oklch(${borderColor})`
					}
				},
				splitLine: {
					lineStyle: {
						color: `oklch(${borderColor})`,
						opacity: 0.3
					}
				}
			},
			series: series.map((s) => ({
				name: s.name,
				type: 'bar',
				stack: 'total',
				data: s.data,
				itemStyle: {
					color: typeColors[s.name] || 'var(--chart-1)'
				},
				emphasis: {
					focus: 'series'
				}
			}))
		};

		chartInstance.setOption(option);
	}

	function handleResize() {
		if (chartInstance) {
			chartInstance.resize();
		}
	}

	onMount(() => {
		initChart();

		window.addEventListener('resize', handleResize);

		return () => {
			window.removeEventListener('resize', handleResize);
			if (chartInstance) {
				chartInstance.dispose();
			}
		};
	});

	// Re-render chart when language or data changes
	$effect(() => {
		const _ = $languageStore;
		if (chartInstance && series.length > 0) {
			updateChart();
		}
	});

	$effect(() => {
		// Watch for data changes
		if (chartInstance && years.length > 0 && series.length > 0) {
			updateChart();
		}
	});
</script>

<div bind:this={chartContainer} class="w-full" style="height: {height};"></div>

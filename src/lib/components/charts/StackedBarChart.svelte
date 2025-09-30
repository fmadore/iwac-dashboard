<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	// @ts-ignore - echarts uses UMD exports
	import * as echarts from 'echarts';
	import { languageStore, t } from '$lib/stores/translationStore.svelte.js';

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
	let chartInstance: any = null;
	let themeClass = $state(''); // Track theme changes for reactivity
	let resizeObserver: ResizeObserver | undefined;
	let previousThemeClass: string | null = null;

	// Canvas for parsing CSS colors
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
			'--foreground': '#09090b',
			'--muted-foreground': '#71717a',
			'--background': '#ffffff',
			'--popover': '#ffffff',
			'--popover-foreground': '#09090b',
			'--border': '#e4e4e7'
		};

		return fallbackMap[variable] || value || '#666666';
	}

	// Default colors for document types (CSS variable names)
	const defaultColorVars: Record<string, string> = {
		'Press Article': '--chart-1',
		'Islamic Periodical': '--chart-2',
		'Document': '--chart-3',
		'Audiovisuel': '--chart-4',
		'Reference': '--chart-5'
	};

	const typeColors = $derived({ ...defaultColorVars, ...colors });

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
		if (!chartContainer) return;

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
		if (!chartInstance || series.length === 0) return;

		const _ = languageStore.current; // Track language changes

		// Translate series names
		const translatedSeriesNames = series.map((s) => {
			const translationKey = `type.${s.name}`;
			return t(translationKey) !== translationKey ? t(translationKey) : s.name;
		});

		// Get current theme colors - resolve CSS variables properly
		const textColor = getCSSVariable('--foreground');
		const borderColor = getCSSVariable('--border');
		const popoverBg = getCSSVariable('--popover');
		const popoverFg = getCSSVariable('--popover-foreground');

		const option = {
			title: title
				? {
						text: title,
						left: 'center',
						textStyle: {
							color: textColor
						}
					}
				: undefined,
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'shadow'
				},
				backgroundColor: popoverBg,
				borderColor: borderColor,
				textStyle: {
					color: popoverFg
				}
			},
			legend: {
				data: translatedSeriesNames,
				top: title ? 40 : 10,
				textStyle: {
					color: textColor
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
					color: textColor,
					rotate: 45
				},
				axisLine: {
					lineStyle: {
						color: borderColor
					}
				}
			},
			yAxis: {
				type: 'value',
				axisLabel: {
					color: textColor
				},
				axisLine: {
					lineStyle: {
						color: borderColor
					}
				},
				splitLine: {
					lineStyle: {
						color: borderColor,
						opacity: 0.3
					}
				}
			},
			series: series.map((s, index) => ({
				name: translatedSeriesNames[index],
				type: 'bar',
				stack: 'total',
				data: s.data,
				itemStyle: {
					color: getCSSVariable(typeColors[s.name] || '--chart-1')
				},
				emphasis: {
					focus: 'series'
				}
			}))
		};

		chartInstance.setOption(option);
	}

	onMount(() => {
		if (!browser) return;

		initChart();

		return () => {
			destroyChart();
		};
	});

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

		if (!chartInstance) {
			return;
		}

		reinitializeChart();
	});

	// Re-render chart when language or data changes
	$effect(() => {
		const _ = languageStore.current;
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

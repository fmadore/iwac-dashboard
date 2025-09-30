<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';

	interface BarChartRaceProps {
		/**
		 * Data structure: { [key: string]: { data: [string, number][], year?: number, ... } }
		 * Each key represents a time period or category
		 */
		data: Record<string, { data: [string, number][]; year?: number; [key: string]: any }>;
		
		/**
		 * Array of time period keys in order (e.g., years)
		 */
		periods: (string | number)[];
		
		/**
		 * Chart title template. Use {0} for dynamic period value
		 * @default 'Chart - {0}'
		 */
		title?: string;
		
		/**
		 * Maximum number of bars to show
		 * @default 10
		 */
		maxBars?: number;
		
		/**
		 * Auto-play on mount
		 * @default false
		 */
		autoPlay?: boolean;
		
		/**
		 * Animation interval in milliseconds
		 * @default 1000
		 */
		interval?: number;
		
		/**
		 * Animation duration for transitions
		 * @default 500
		 */
		animationDuration?: number;
		
		/**
		 * Chart height in pixels
		 * @default 600
		 */
		height?: number;
		
		/**
		 * Primary bar color (CSS variable or color string)
		 * @default 'var(--chart-1)'
		 */
		barColor?: string;
		
		/**
		 * Enable/disable value labels on bars
		 * @default true
		 */
		showLabels?: boolean;
		
		/**
		 * Make data cumulative over time
		 * @default false
		 */
		cumulative?: boolean;
		
		/**
		 * Current period index (for external control)
		 */
		currentIndex?: number;
		
		/**
		 * Callback when period changes
		 */
		onPeriodChange?: (index: number, period: string | number) => void;
		
		/**
		 * Callback when animation completes
		 */
		onComplete?: () => void;
	}

	let {
		data,
		periods,
		title = 'Chart - {0}',
		maxBars = 10,
		autoPlay = false,
		interval = 1000,
		animationDuration = 500,
		height = 600,
		barColor = 'var(--chart-1)',
		showLabels = true,
		cumulative = false,
		currentIndex = $bindable(0),
		onPeriodChange,
		onComplete
	}: BarChartRaceProps = $props();

	// Component state
	let chartContainer: HTMLDivElement;
	let chartInstance: any = null;
	let isPlaying = $state(false);
	let playInterval: number | null = null;
	let themeClass = $state('');
	let resizeObserver: ResizeObserver | undefined;
	let previousThemeClass: string | null = null;

	// Canvas for parsing CSS colors
	const colorParsingCanvas = browser ? document.createElement('canvas') : null;
	const colorParsingContext = colorParsingCanvas?.getContext('2d', { willReadFrequently: false });

	// Derived current period
	const currentPeriod = $derived(periods[currentIndex]);

	// Get computed CSS variable value
	function parseColor(value: string): string | null {
		if (!colorParsingContext) return null;
		try {
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

	// Compute cumulative data if needed
	function getCumulativeData(): Record<string, { data: [string, number][]; year?: number; [key: string]: any }> {
		if (!cumulative) return data;

		const cumulativeData: Record<string, { data: [string, number][]; year?: number; [key: string]: any }> = {};
		const termTotals: Map<string, number> = new Map();

		for (let i = 0; i <= currentIndex; i++) {
			const period = periods[i];
			const periodData = data[String(period)];
			
			if (periodData && periodData.data) {
				// Accumulate counts for each term
				for (const [term, count] of periodData.data) {
					const current = termTotals.get(term) || 0;
					termTotals.set(term, current + count);
				}
			}
		}

		// Sort by total count and return top items
		const sortedTerms = Array.from(termTotals.entries())
			.sort((a, b) => b[1] - a[1]);

		cumulativeData[String(currentPeriod)] = {
			data: sortedTerms,
			year: data[String(currentPeriod)]?.year
		};

		return cumulativeData;
	}

	/**
	 * Initialize ECharts instance
	 */
	async function initChart() {
		if (!browser || !chartContainer) return;

		try {
			// Dynamically import ECharts
			const echarts = await import('echarts');

			// Dispose existing chart if any
			if (chartInstance) {
				chartInstance.dispose();
			}

			// Initialize new chart instance
			chartInstance = echarts.init(chartContainer);

			// Attach resize observer
			attachResizeObserver();

			// Render initial chart
			renderChart();
		} catch (err) {
			console.error('Error initializing chart:', err);
		}
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

	function destroyChart() {
		detachResizeObserver();
		chartInstance?.dispose();
		chartInstance = null;
	}

	async function reinitializeChart() {
		destroyChart();
		await initChart();
	}

	/**
	 * Render chart for current period
	 */
	function renderChart() {
		if (!chartInstance || !currentPeriod) return;

		// Get data (cumulative or regular)
		const displayData = cumulative ? getCumulativeData() : data;
		const periodData = displayData[String(currentPeriod)];
		
		if (!periodData || !periodData.data || periodData.data.length === 0) {
			return;
		}

		// Get top N items
		const topItems = periodData.data.slice(0, maxBars);
		const labels = topItems.map(([label]) => label);
		const values = topItems.map(([, value]) => value);

		// Format title with current period
		const formattedTitle = title.replace('{0}', String(currentPeriod));

		// Resolve CSS variables to actual colors
		const foregroundColor = getCSSVariable('--foreground');
		const borderColor = getCSSVariable('--border');
		const popoverBg = getCSSVariable('--popover');
		const popoverFg = getCSSVariable('--popover-foreground');
		const resolvedBarColor = barColor.startsWith('var(--') 
			? getCSSVariable(barColor.slice(4, -1)) 
			: barColor;

		const option = {
			title: {
				text: formattedTitle,
				left: 'center',
				textStyle: {
					color: foregroundColor
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
				}
			},
			grid: {
				left: '15%',
				right: '10%',
				bottom: '10%',
				top: '15%',
				containLabel: true
			},
			xAxis: {
				type: 'value',
				axisLine: {
					lineStyle: {
						color: borderColor,
						opacity: 1
					}
				},
				axisLabel: {
					color: foregroundColor
				},
				splitLine: {
					lineStyle: {
						color: borderColor,
						opacity: 0.3
					}
				}
			},
			yAxis: {
				type: 'category',
				data: labels,
				inverse: true,
				axisLine: {
					lineStyle: {
						color: borderColor,
						opacity: 1
					}
				},
				axisLabel: {
					color: foregroundColor
				}
			},
			series: [
				{
					type: 'bar',
					data: values,
					itemStyle: {
						color: resolvedBarColor,
						borderRadius: [0, 4, 4, 0]
					},
					label: {
						show: showLabels,
						position: 'right',
						color: foregroundColor,
						formatter: '{c}'
					},
					emphasis: {
						itemStyle: {
							color: resolvedBarColor,
							opacity: 0.8
						}
					},
					animationDuration: animationDuration,
					animationEasing: 'cubicOut'
				}
			]
		};

		chartInstance.setOption(option, true);

		// Trigger callback
		if (onPeriodChange) {
			onPeriodChange(currentIndex, currentPeriod);
		}
	}

	/**
	 * Start auto-play animation
	 */
	export function play() {
		if (isPlaying) return;

		isPlaying = true;
		playInterval = window.setInterval(() => {
			if (currentIndex < periods.length - 1) {
				currentIndex++;
				renderChart();
			} else {
				pause();
				if (onComplete) {
					onComplete();
				}
			}
		}, interval);
	}

	/**
	 * Pause auto-play animation
	 */
	export function pause() {
		isPlaying = false;
		if (playInterval !== null) {
			clearInterval(playInterval);
			playInterval = null;
		}
	}

	/**
	 * Reset to first period
	 */
	export function reset() {
		pause();
		currentIndex = 0;
		renderChart();
	}

	/**
	 * Go to specific period index
	 */
	export function goToIndex(index: number) {
		if (index >= 0 && index < periods.length) {
			pause();
			currentIndex = index;
			renderChart();
		}
	}

	/**
	 * Go to next period
	 */
	export function next() {
		if (currentIndex < periods.length - 1) {
			currentIndex++;
			renderChart();
		}
	}

	/**
	 * Go to previous period
	 */
	export function previous() {
		if (currentIndex > 0) {
			currentIndex--;
			renderChart();
		}
	}

	// Initialize chart on mount
	$effect(() => {
		if (browser && chartContainer) {
			initChart();
		}
	});

	// Re-render when data or current index changes
	$effect(() => {
		const _ = currentIndex;
		const _data = data;
		const _period = currentPeriod;
		const _cumulative = cumulative;

		if (chartInstance) {
			renderChart();
		}
	});

	// Watch for theme changes
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

	// Reinitialize chart when theme changes
	$effect(() => {
		if (!browser) return;

		const currentTheme = themeClass;
		if (currentTheme === previousThemeClass) return;

		previousThemeClass = currentTheme;

		if (chartInstance) {
			reinitializeChart();
		}
	});

	// Auto-play on mount if enabled
	$effect(() => {
		if (autoPlay && chartInstance && !isPlaying) {
			play();
		}
	});

	// Cleanup on unmount
	onMount(() => {
		return () => {
			pause();
			destroyChart();
		};
	});

	// Export playing state as getters
	export function getPlaying() {
		return isPlaying;
	}

	export function getProgress() {
		return (currentIndex / (periods.length - 1)) * 100;
	}
</script>

<div class="bar-chart-race">
	<div
		bind:this={chartContainer}
		class="chart-container"
		style="height: {height}px;"
	></div>
</div>

<style>
	.bar-chart-race {
		position: relative;
		width: 100%;
	}

	.chart-container {
		width: 100%;
	}
</style>

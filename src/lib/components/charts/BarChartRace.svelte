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
		currentIndex = $bindable(0),
		onPeriodChange,
		onComplete
	}: BarChartRaceProps = $props();

	// Component state
	let chartContainer: HTMLDivElement;
	let chartInstance: any = null;
	let isPlaying = $state(false);
	let playInterval: number | null = null;

	// Derived current period
	const currentPeriod = $derived(periods[currentIndex]);

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

			// Render initial chart
			renderChart();

			// Handle window resize
			const handleResize = () => {
				if (chartInstance) {
					chartInstance.resize();
				}
			};
			window.addEventListener('resize', handleResize);

			// Return cleanup function
			return () => {
				window.removeEventListener('resize', handleResize);
				if (chartInstance) {
					chartInstance.dispose();
					chartInstance = null;
				}
			};
		} catch (err) {
			console.error('Error initializing chart:', err);
		}
	}

	/**
	 * Render chart for current period
	 */
	function renderChart() {
		if (!chartInstance || !currentPeriod) return;

		const periodData = data[String(currentPeriod)];
		if (!periodData || !periodData.data || periodData.data.length === 0) {
			return;
		}

		// Get top N items
		const topItems = periodData.data.slice(0, maxBars);
		const labels = topItems.map(([label]) => label);
		const values = topItems.map(([, value]) => value);

		// Format title with current period
		const formattedTitle = title.replace('{0}', String(currentPeriod));

		const option = {
			title: {
				text: formattedTitle,
				left: 'center',
				textStyle: {
					color: 'var(--foreground)'
				}
			},
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'shadow'
				},
				backgroundColor: 'var(--popover)',
				borderColor: 'var(--border)',
				textStyle: {
					color: 'var(--popover-foreground)'
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
						color: 'var(--border)'
					}
				},
				axisLabel: {
					color: 'var(--foreground)'
				}
			},
			yAxis: {
				type: 'category',
				data: labels,
				inverse: true,
				axisLine: {
					lineStyle: {
						color: 'var(--border)'
					}
				},
				axisLabel: {
					color: 'var(--foreground)'
				}
			},
			series: [
				{
					type: 'bar',
					data: values,
					itemStyle: {
						color: barColor
					},
					label: {
						show: showLabels,
						position: 'right',
						color: 'var(--foreground)'
					},
					animationDuration: animationDuration,
					animationEasing: 'linear'
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
			initChart().then((cleanup) => {
				if (cleanup) {
					return cleanup;
				}
			});
		}
	});

	// Re-render when data or current index changes
	$effect(() => {
		const _ = currentIndex;
		const _data = data;
		const _period = currentPeriod;

		if (chartInstance) {
			renderChart();
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
			if (chartInstance) {
				chartInstance.dispose();
			}
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

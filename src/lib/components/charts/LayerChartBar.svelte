<script lang="ts">
	import { BarChart, Tooltip as TooltipPrimitive } from 'layerchart';
	import { scaleBand } from 'd3-scale';
	import { cubicInOut } from 'svelte/easing';
	import { ChartContainer, type ChartConfig } from '$lib/components/ui/chart/index.js';
	import LayerChartTooltip, { type TooltipItem } from './LayerChartTooltip.svelte';
	import { t } from '$lib/stores/translationStore.svelte.js';

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
		orientation?: 'vertical' | 'horizontal';
		xAxisLabelRotate?: number;
		yAxisLabelWidth?: number;
		xAxisLabelInterval?: number | 'auto';
	}

	let {
		data = [],
		height = 400,
		animationDuration = 500,
		useMultipleColors = false,
		orientation = 'vertical',
		xAxisLabelRotate = 0,
		yAxisLabelWidth = 100,
		xAxisLabelInterval = 'auto'
	}: Props = $props();

	let containerEl = $state<HTMLElement | null>(null);
	let containerWidth = $state(0);

	$effect(() => {
		if (!containerEl) return;

		const update = () => {
			containerWidth = containerEl?.clientWidth ?? 0;
		};

		update();
		const ro = new ResizeObserver(update);
		ro.observe(containerEl);
		return () => ro.disconnect();
	});

	// Color mapping based on original English keys (language-independent)
	const categoryColorMap: Record<string, string> = {
		Persons: 'var(--chart-1)',
		Locations: 'var(--chart-2)',
		Organizations: 'var(--chart-3)',
		'Authority Files': 'var(--chart-4)',
		Events: 'var(--chart-5)',
		Topics: 'var(--chart-6)'
	};

	// Chart colors for cycling
	const chartColors = [
		'var(--chart-1)',
		'var(--chart-2)',
		'var(--chart-3)',
		'var(--chart-4)',
		'var(--chart-5)',
		'var(--chart-6)',
		'var(--chart-7)',
		'var(--chart-8)',
		'var(--chart-9)',
		'var(--chart-10)'
	];

	// Get color for each category based on originalKey
	function getColorForCategory(item: ChartDataItem, index: number): string {
		if (!useMultipleColors) {
			return 'var(--chart-1)';
		}

		// Use originalKey if available, otherwise fall back to category
		const key = item.originalKey || item.category;
		const colorVar = categoryColorMap[key];
		if (colorVar) {
			return colorVar;
		}

		// Fallback to cycling through chart colors
		return chartColors[index % chartColors.length];
	}

	// Prepare chart data with colors and name for tooltip
	const chartData = $derived(
		data.map((item, index) => ({
			...item,
			color: getColorForCategory(item, index),
			name: item.category, // For tooltip display
			value: item.documents // For tooltip display
		}))
	);

	// Build chart config dynamically for tooltip
	const chartConfig = $derived.by(() => {
		const config: ChartConfig = {};
		return config;
	});

	const chartWidth = $derived(containerWidth);
	const perItemWidth = $derived.by(() => {
		const count = Math.max(1, data.length);
		return chartWidth > 0 ? chartWidth / count : 0;
	});

	// Auto-skip x-axis labels when there isn't enough horizontal space.
	// For band scales, `ticks` as a number means "show every Nth label".
	const xAxisTicks = $derived.by(() => {
		if (orientation !== 'vertical') return undefined;
		if (data.length <= 1) return 1;
		if (xAxisLabelInterval !== 'auto') return Math.max(1, xAxisLabelInterval);

		// Sidebar + content transitions can leave charts in a mid-width state where
		// labels overlap. Be a bit more aggressive about skipping.
		if (!perItemWidth) return 1;
		const minLabelSpace = effectiveXAxisLabelRotate >= 45 ? 50 : 90;
		return Math.max(1, Math.ceil(minLabelSpace / perItemWidth));
	});

	const effectiveXAxisLabelRotate = $derived.by(() => {
		if (orientation !== 'vertical') return 0;
		if (xAxisLabelRotate > 0) return xAxisLabelRotate;
		// If labels are cramped (common when the sidebar is open), rotate by default.
		if (perItemWidth <= 0) return 0;
		if (perItemWidth < 55) return 90;
		if (perItemWidth < 90) return 45;
		return 0;
	});

	// Determine if we need to truncate labels based on available space
	const formatLabel = $derived.by(() => {
		const itemCount = data.length;

		if (orientation === 'horizontal' && yAxisLabelWidth) {
			const maxChars = Math.max(4, Math.floor(yAxisLabelWidth / 7));
			return (d: string) => (d.length > maxChars ? d.slice(0, maxChars - 1) + '…' : d);
		}
		if (orientation === 'vertical') {
			const fallbackMaxChars = itemCount > 10 ? 8 : itemCount > 6 ? 12 : 20;
			const maxChars = perItemWidth > 0 ? Math.max(4, Math.floor(perItemWidth / 7)) : fallbackMaxChars;
			return (d: string) => (d.length > maxChars ? d.slice(0, maxChars - 1) + '…' : d);
		}
		return (d: string) => d;
	});

	// Calculate optimal padding based on label rotation and data
	const bottomPadding = $derived.by(() => {
		if (orientation !== 'vertical') return 8;
		if (effectiveXAxisLabelRotate >= 90) return 110;
		if (effectiveXAxisLabelRotate > 0) return 80;
		return data.length > 10 ? 60 : 40;
	});

	function tooltipLabelFromPayload(payload: any[]): string {
		const first = payload?.[0];
		return (
			first?.payload?.category ??
			first?.payload?.name ??
			first?.label ??
			first?.name ??
			''
		);
	}

	function tooltipItemsFromPayload(payload: any[]): TooltipItem[] {
		return (payload ?? [])
			.map((item: any) => {
				const key = item?.key ?? item?.name;
				const name = key === 'documents' ? t('chart.documents') : (item?.name ?? item?.key ?? '');
				const value = item?.value;
				const color = item?.payload?.color ?? item?.color;
				return { key, name, value, color } satisfies TooltipItem;
			})
			.filter((i) => i.name && i.value !== undefined);
	}
</script>

<div
	bind:this={containerEl}
	class="h-full w-full"
	style="height: {height}px;"
	role="img"
	aria-label={t('chart.documents_by_category_aria')}
>
	{#if chartData.length > 0}
		<ChartContainer config={chartConfig} class="h-full w-full min-w-0 aspect-auto justify-start">
			{#if orientation === 'horizontal'}
				<BarChart
					data={chartData}
					orientation="horizontal"
					yScale={scaleBand().padding(0.2)}
					y="category"
					x="documents"
					c={(d) => d.color}
					cRange={chartData.map((c) => c.color)}
					padding={{ left: yAxisLabelWidth + 16, right: 24, top: 8, bottom: 8 }}
					grid={false}
					rule={false}
					axis
					props={{
						bars: {
							stroke: 'none',
							radius: 4,
							rounded: 'right',
							initialWidth: 0,
							initialX: 0,
							motion: {
								x: { type: 'tween', duration: animationDuration, easing: cubicInOut },
								width: { type: 'tween', duration: animationDuration, easing: cubicInOut }
							}
						},
						highlight: { area: { fill: 'none' } },
						yAxis: {
							format: formatLabel,
							tickLabelProps: {
								svgProps: {
									x: -8
								}
							}
						}
					}}
				>
					{#snippet tooltip({ context })}
						<TooltipPrimitive.Root context={context} variant="none">
							{#snippet children()}
								<LayerChartTooltip
									label={tooltipLabelFromPayload(context.tooltip?.payload ?? [])}
									items={tooltipItemsFromPayload(context.tooltip?.payload ?? [])}
								/>
							{/snippet}
						</TooltipPrimitive.Root>
					{/snippet}
				</BarChart>
			{:else}
				<BarChart
					data={chartData}
					xScale={scaleBand().padding(0.2)}
					x="category"
					y="documents"
					c={(d) => d.color}
					cRange={chartData.map((c) => c.color)}
					padding={{ left: 48, right: 16, top: 8, bottom: bottomPadding }}
					grid={false}
					rule={false}
					axis
					props={{
						bars: {
							stroke: 'none',
							radius: 4,
							rounded: 'top',
							initialHeight: 0,
							motion: {
								y: { type: 'tween', duration: animationDuration, easing: cubicInOut },
								height: { type: 'tween', duration: animationDuration, easing: cubicInOut }
							}
						},
						highlight: { area: { fill: 'none' } },
						xAxis: {
							ticks: xAxisTicks,
							format: formatLabel,
							tickLabelProps: {
								rotate: effectiveXAxisLabelRotate > 0 ? effectiveXAxisLabelRotate : undefined,
								textAnchor: effectiveXAxisLabelRotate > 0 ? 'start' : 'middle',
								dy: effectiveXAxisLabelRotate > 0 ? '0.5em' : undefined,
								dx: effectiveXAxisLabelRotate > 0 ? 2 : undefined
							}
						}
					}}
				>
					{#snippet tooltip({ context })}
						<TooltipPrimitive.Root context={context} variant="none">
							{#snippet children()}
								<LayerChartTooltip
									label={tooltipLabelFromPayload(context.tooltip?.payload ?? [])}
									items={tooltipItemsFromPayload(context.tooltip?.payload ?? [])}
								/>
							{/snippet}
						</TooltipPrimitive.Root>
					{/snippet}
				</BarChart>
			{/if}
		</ChartContainer>
	{/if}
</div>

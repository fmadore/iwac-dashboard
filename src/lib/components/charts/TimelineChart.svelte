<script lang="ts">
	import { Axis, BarChart, Spline, Tooltip as TooltipPrimitive } from 'layerchart';
	import { scaleBand } from 'd3-scale';
	import { cubicInOut } from 'svelte/easing';
	import { ChartContainer, type ChartConfig } from '$lib/components/ui/chart/index.js';
	import LayerChartTooltip, { type TooltipItem } from './LayerChartTooltip.svelte';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';

	interface Props {
		months?: string[];
		monthlyAdditions?: number[];
		cumulativeTotal?: number[];
		height?: number;
	}

	let { months = [], monthlyAdditions = [], cumulativeTotal = [], height = 500 }: Props = $props();

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

	// Force re-render on language change
	const chartKey = $derived(`timeline-chart-${languageStore.current}`);

	// Transform data for LayerChart
	const chartData = $derived.by(() => {
		return filteredData.months.map((month, index) => {
			const [year, m] = month.split('-');
			return {
				month,
				monthLabel: `${m}/${year.slice(2)}`,
				additions: filteredData.monthlyAdditions[index] ?? 0,
				cumulative: filteredData.cumulativeTotal[index] ?? 0,
				// For tooltip - add name and value fields
				name: `${m}/${year.slice(2)}`,
				value: filteredData.monthlyAdditions[index] ?? 0,
				color: 'var(--chart-1)'
			};
		});
	});

	// Calculate domain extents
	const maxAdditions = $derived(Math.max(1, ...chartData.map((d) => d.additions)));
	const maxCumulative = $derived(Math.max(1, ...chartData.map((d) => d.cumulative)));

	// Normalize cumulative data to fit on same scale as additions for overlay
	const normalizedChartData = $derived.by(() => {
		const ratio = maxAdditions / maxCumulative;
		return chartData.map((d) => ({
			...d,
			normalizedCumulative: d.cumulative * ratio
		}));
	});

	// Convert normalized cumulative values back to cumulative totals for the right axis
	const cumulativeInverseRatio = $derived.by(() => {
		const safeMaxAdditions = Math.max(1, maxAdditions);
		return maxCumulative / safeMaxAdditions;
	});

	function formatCumulativeTick(value: unknown): string {
		if (typeof value !== 'number' || !Number.isFinite(value)) return '';
		return Math.round(value * cumulativeInverseRatio).toLocaleString();
	}

	// Chart container and width tracking
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

	// Calculate x-axis tick interval based on available space
	const perItemWidth = $derived.by(() => {
		const count = Math.max(1, chartData.length);
		return containerWidth > 0 ? containerWidth / count : 0;
	});

	const xAxisTicks = $derived.by(() => {
		if (chartData.length <= 1) return 1;
		if (!perItemWidth) return 1;
		const minLabelSpace = 50;
		return Math.max(1, Math.ceil(minLabelSpace / perItemWidth));
	});

	// Chart config for ChartContainer context
	const chartConfig: ChartConfig = $derived({
		additions: {
			label: t('timeline.monthly_additions'),
			color: 'var(--chart-1)'
		},
		cumulative: {
			label: t('timeline.cumulative_total'),
			color: 'var(--chart-2)'
		}
	});

	// Format label
	const formatLabel = $derived.by(() => {
		return (d: string) => d;
	});

	// Calculate bottom padding for rotated labels
	const bottomPadding = $derived.by(() => {
		if (chartData.length > 12) return 80;
		return 60;
	});

	// Build tooltip items from data point
	function buildTooltipItems(data: (typeof normalizedChartData)[number]): TooltipItem[] {
		return [
			{
				name: t('timeline.monthly_additions'),
				value: data.additions,
				color: 'var(--chart-1)'
			},
			{
				name: t('timeline.cumulative_total'),
				value: data.cumulative,
				color: 'var(--chart-2)'
			}
		];
	}
</script>

{#key chartKey}
	<div
		bind:this={containerEl}
		class="h-full w-full"
		style="height: {height}px;"
		role="img"
		aria-label={t('timeline.chart_aria')}
	>
		{#if chartData.length > 0}
			{#snippet timelineAboveMarks()}
				<!-- Overlay: Line for cumulative (normalized to same scale) -->
				<Spline
					data={normalizedChartData}
					x={(d) => d.monthLabel}
					y={(d) => d.normalizedCumulative}
					stroke="var(--chart-2)"
					strokeWidth={3}
				/>

				<!-- Secondary (right) y-axis showing cumulative totals -->
				<Axis
					placement="right"
					label={t('timeline.cumulative_total')}
					labelProps={{ class: 'fill-foreground text-xs' }}
					grid={false}
					rule={false}
					format={formatCumulativeTick}
				/>
			{/snippet}

			{#snippet timelineTooltip({ context })}
				<TooltipPrimitive.Root context={context} variant="none">
					{#snippet children({ data })}
						<LayerChartTooltip
							label={data?.monthLabel ?? ''}
							items={data ? buildTooltipItems(data) : []}
							indicator="dot"
						/>
					{/snippet}
				</TooltipPrimitive.Root>
			{/snippet}

			<ChartContainer
				config={chartConfig}
				class="aspect-auto h-full w-full min-w-0 justify-start flex-col items-stretch"
			>

				<BarChart
					data={normalizedChartData}
					xScale={scaleBand().padding(0.2)}
					x="monthLabel"
					y="additions"
					yDomain={[0, maxAdditions]}
					yNice
					c={() => 'var(--chart-1)'}
					cRange={['var(--chart-1)']}
					padding={{ left: 60, right: 60, top: 20, bottom: bottomPadding }}
					grid={false}
					rule={false}
					axis
					aboveMarks={timelineAboveMarks}
					tooltip={timelineTooltip}
					props={{
						bars: {
							stroke: 'none',
							radius: 4,
							rounded: 'top',
							initialHeight: 0,
							motion: {
								y: { type: 'tween', duration: 500, easing: cubicInOut },
								height: { type: 'tween', duration: 500, easing: cubicInOut }
							}
						},
						highlight: { area: { fill: 'none' } },
						xAxis: {
							ticks: xAxisTicks,
							format: formatLabel,
							label: '',
							tickLabelProps: {
								rotate: chartData.length > 12 ? 45 : 0,
								textAnchor: chartData.length > 12 ? 'start' : 'middle',
								dy: chartData.length > 12 ? '0.5em' : undefined,
								dx: chartData.length > 12 ? 2 : undefined
							}
						},
						yAxis: {
							label: t('timeline.monthly_additions'),
							labelProps: { class: 'fill-foreground text-xs' }
						}
					}}
				/>

				<!-- Legend -->
				<div class="mt-4 flex justify-center gap-6 text-sm">
					<div class="flex items-center gap-2">
						<div class="h-3 w-3 rounded" style="background-color: var(--chart-1);"></div>
						<span class="text-muted-foreground">{t('timeline.monthly_additions')}</span>
					</div>
					<div class="flex items-center gap-2">
						<div class="h-0.5 w-4 rounded" style="background-color: var(--chart-2);"></div>
						<span class="text-muted-foreground">{t('timeline.cumulative_total')}</span>
					</div>
				</div>
			</ChartContainer>
		{:else}
			<div class="flex h-full items-center justify-center">
				<p class="text-muted-foreground">{t('chart.no_data')}</p>
			</div>
		{/if}
	</div>
{/key}

<script lang="ts">
	import { Chart, Svg, Spline, Axis, Highlight, Tooltip as TooltipPrimitive } from 'layerchart';
	import { scaleLinear, scalePoint } from 'd3-scale';
	import Tooltip, { type TooltipItem } from './Tooltip.svelte';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';

	interface KeywordSeries {
		keyword: string;
		years: number[];
		counts: number[];
		color: string;
	}

	interface Props {
		series?: KeywordSeries[];
		height?: number;
	}

	let { series = [], height = 400 }: Props = $props();

	// Force re-render on language change
	const chartKey = $derived(`keywords-chart-${languageStore.current}`);

	// Transform data for LayerChart - one data point per year with all keywords
	const chartData = $derived.by(() => {
		if (series.length === 0) return [];

		// Get all unique years across all series
		const allYears = new Set<number>();
		series.forEach((s) => s.years.forEach((y) => allYears.add(y)));
		const sortedYears = Array.from(allYears).sort((a, b) => a - b);

		// Create data points for each year
		return sortedYears.map((year) => {
			const point: Record<string, number | string> = { year: String(year) };
			series.forEach((s) => {
				const idx = s.years.indexOf(year);
				point[s.keyword] = idx >= 0 ? s.counts[idx] : 0;
			});
			return point;
		});
	});

	// Calculate domain extents
	const years = $derived(chartData.map((d) => d.year as string));
	const maxCount = $derived.by(() => {
		if (series.length === 0) return 10;
		let max = 0;
		series.forEach((s) => {
			const seriesMax = Math.max(...s.counts);
			if (seriesMax > max) max = seriesMax;
		});
		return Math.max(max, 10);
	});

	// Scales
	const xScale = $derived(scalePoint<string>().domain(years).padding(0.1));
	const yScale = $derived(scaleLinear().domain([0, maxCount]).nice());

	// Chart colors (up to 10 distinct colors)
	const chartColors = [
		'var(--chart-1)',
		'var(--chart-2)',
		'var(--chart-3)',
		'var(--chart-4)',
		'var(--chart-5)',
		'hsl(280 60% 50%)',
		'hsl(160 60% 40%)',
		'hsl(30 80% 50%)',
		'hsl(340 70% 50%)',
		'hsl(200 70% 50%)'
	];

	// Build tooltip items from data point
	function buildTooltipItems(data: Record<string, number | string>): TooltipItem[] {
		return series.map((s, idx) => ({
			name: s.keyword,
			value: (data[s.keyword] as number) || 0,
			color: chartColors[idx % chartColors.length]
		}));
	}

	// Calculate x-axis tick interval based on data length
	const xAxisTicks = $derived.by(() => {
		if (chartData.length <= 10) return 1;
		if (chartData.length <= 20) return 2;
		if (chartData.length <= 40) return 5;
		return 10;
	});

	// Get tick values for the x-axis
	const xTickValues = $derived.by(() => {
		return years.filter((_, i) => i % xAxisTicks === 0);
	});
</script>

{#key chartKey}
	<div class="flex h-full w-full flex-col" style="height: {height}px;" role="img" aria-label={t('keywords.chart_aria')}>
		{#if chartData.length > 0 && series.length > 0}
			<div class="flex-1 min-h-0">
				<Chart
					data={chartData}
					x="year"
					xScale={xScale}
					yScale={yScale}
					yDomain={[0, maxCount]}
					yNice
					padding={{ left: 50, right: 20, top: 10, bottom: 50 }}
					tooltip={{ mode: 'bisect-x' }}
				>
					<Svg>
						<Axis
							placement="left"
							grid={{ class: 'stroke-muted/50' }}
							rule={false}
							tickLabelProps={{ class: 'fill-muted-foreground text-xs' }}
						/>
						<Axis
							placement="bottom"
							rule={false}
							ticks={xTickValues}
							tickLabelProps={{
								class: 'fill-muted-foreground text-xs',
								rotate: chartData.length > 30 ? 45 : 0,
								textAnchor: chartData.length > 30 ? 'start' : 'middle',
								dy: chartData.length > 30 ? '0.5em' : '0.25em'
							}}
						/>

						{#each series as s, idx (s.keyword)}
							<Spline
								data={chartData}
								x="year"
								y={s.keyword}
								stroke={chartColors[idx % chartColors.length]}
								strokeWidth={2}
							/>
						{/each}

						<Highlight points={{ r: 5, class: 'fill-primary stroke-background stroke-2' }} lines={{ class: 'stroke-muted-foreground/50' }} />
					</Svg>

					<TooltipPrimitive.Root variant="none">
						{#snippet children({ data })}
							{#if data}
								<Tooltip
									label={String(data.year)}
									items={buildTooltipItems(data)}
									indicator="dot"
								/>
							{/if}
						{/snippet}
					</TooltipPrimitive.Root>
				</Chart>
			</div>

			<!-- Legend -->
			<div class="mt-2 flex flex-wrap justify-center gap-x-4 gap-y-1 px-4 text-xs">
				{#each series as s, idx (s.keyword)}
					<div class="flex items-center gap-1.5">
						<div
							class="h-0.5 w-3 rounded"
							style="background-color: {chartColors[idx % chartColors.length]};"
						></div>
						<span class="text-muted-foreground">{s.keyword}</span>
					</div>
				{/each}
			</div>
		{:else}
			<div class="flex h-full items-center justify-center">
				<p class="text-muted-foreground">{t('chart.no_data')}</p>
			</div>
		{/if}
	</div>
{/key}

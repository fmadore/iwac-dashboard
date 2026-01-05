<script lang="ts">
	import { scaleTime, scaleBand } from 'd3-scale';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';

	// Types for duration data
	interface CoveragePeriod {
		start: number;
		end: number;
	}

	interface NewspaperCoverage {
		name: string;
		country: string;
		totalArticles: number;
		periods: CoveragePeriod[];
	}

	interface Props {
		data?: NewspaperCoverage[];
		height?: number;
		class?: string;
	}

	let { data = [], height = 400, class: className = '' }: Props = $props();

	// Force re-render on language change
	const chartKey = $derived(`duration-chart-${languageStore.current}`);

	// Get unique countries for color scale
	const countries = $derived([...new Set(data.map((d) => d.country))]);

	// Color scale for countries - use CSS custom property names directly
	const colorRange = [
		'var(--color-chart-1)',
		'var(--color-chart-2)',
		'var(--color-chart-3)',
		'var(--color-chart-4)',
		'var(--color-chart-5)',
		'var(--color-chart-6)'
	];

	// Get color for country
	function getCountryColor(country: string): string {
		const index = countries.indexOf(country);
		return colorRange[index % colorRange.length];
	}

	// Flatten data for chart - each period becomes a separate bar
	const chartData = $derived.by(() => {
		const flattened: Array<{
			name: string;
			country: string;
			startDate: Date;
			endDate: Date;
			periodLabel: string;
			totalArticles: number;
		}> = [];

		for (const newspaper of data) {
			for (const period of newspaper.periods) {
				flattened.push({
					name: newspaper.name,
					country: newspaper.country,
					startDate: new Date(period.start, 0, 1),
					endDate: new Date(period.end, 11, 31),
					periodLabel: `${period.start}-${period.end}`,
					totalArticles: newspaper.totalArticles
				});
			}
		}

		return flattened;
	});

	// Get unique newspaper names for y-axis
	const newspaperNames = $derived([...new Set(data.map((d) => d.name))]);

	// Chart dimensions
	const margin = { top: 20, right: 30, bottom: 40, left: 150 };
	const chartWidth = $derived(800);
	const chartHeight = $derived(Math.max(100, newspaperNames.length * 60));
	const innerWidth = $derived(chartWidth - margin.left - margin.right);
	const innerHeight = $derived(chartHeight - margin.top - margin.bottom);

	// Calculate the year domain
	const yearDomain = $derived.by((): [Date, Date] => {
		if (chartData.length === 0) return [new Date(1955, 0, 1), new Date(2030, 11, 31)];

		const allDates = chartData.flatMap((d) => [d.startDate, d.endDate]);
		const minDate = new Date(Math.min(...allDates.map((d) => d.getTime())));
		const maxDate = new Date(Math.max(...allDates.map((d) => d.getTime())));

		// Add some padding
		minDate.setFullYear(minDate.getFullYear() - 3);
		maxDate.setFullYear(maxDate.getFullYear() + 3);

		return [minDate, maxDate];
	});

	// Create scales
	const xScale = $derived(scaleTime().domain(yearDomain).range([0, innerWidth]));

	const yScale = $derived(
		scaleBand<string>().domain(newspaperNames).range([0, innerHeight]).padding(0.3)
	);

	// Generate x-axis ticks
	const xTicks = $derived.by(() => {
		const [minDate, maxDate] = yearDomain;
		const ticks: Date[] = [];
		const startYear = Math.ceil(minDate.getFullYear() / 10) * 10;
		const endYear = maxDate.getFullYear();

		for (let year = startYear; year <= endYear; year += 10) {
			ticks.push(new Date(year, 0, 1));
		}
		return ticks;
	});
</script>

{#key chartKey}
	<div
		class="h-full w-full {className}"
		style="height: {height}px;"
		role="img"
		aria-label={t('coverage.chart_aria')}
	>
		{#if chartData.length > 0}
			<svg
				viewBox="0 0 {chartWidth} {chartHeight}"
				class="h-full w-full"
				preserveAspectRatio="xMidYMid meet"
			>
				<g transform="translate({margin.left}, {margin.top})">
					<!-- X Axis -->
					<g transform="translate(0, {innerHeight})">
						<line x1="0" y1="0" x2={innerWidth} y2="0" stroke="currentColor" stroke-opacity="0.2" />
						{#each xTicks as tick}
							{@const x = xScale(tick)}
							<g transform="translate({x}, 0)">
								<line y2="6" stroke="currentColor" stroke-opacity="0.4" />
								<text y="20" text-anchor="middle" class="fill-muted-foreground text-xs">
									{tick.getFullYear()}
								</text>
							</g>
						{/each}
					</g>

					<!-- Y Axis -->
					{#each newspaperNames as name}
						{@const y = (yScale(name) ?? 0) + yScale.bandwidth() / 2}
						<text
							x="-10"
							{y}
							text-anchor="end"
							dominant-baseline="middle"
							class="fill-foreground text-sm font-medium"
						>
							{name}
						</text>
					{/each}

					<!-- Bars -->
					{#each chartData as item, i (i)}
						{@const x1 = xScale(item.startDate)}
						{@const x2 = xScale(item.endDate)}
						{@const y = yScale(item.name) ?? 0}
						{@const barHeight = yScale.bandwidth()}
						{@const barWidth = Math.max(2, x2 - x1)}
						<rect
							x={x1}
							{y}
							width={barWidth}
							height={barHeight}
							fill={getCountryColor(item.country)}
							rx={4}
							ry={4}
							class="cursor-pointer transition-opacity duration-200 hover:opacity-70"
						>
							<title
								>{item.name}: {item.periodLabel} ({item.country}) - {item.totalArticles.toLocaleString()}
								articles</title
							>
						</rect>
					{/each}
				</g>
			</svg>
		{:else}
			<div class="flex h-full items-center justify-center">
				<p class="text-muted-foreground">{t('chart.no_data')}</p>
			</div>
		{/if}
	</div>
{/key}

<script lang="ts">
	import { scaleBand } from 'd3-scale';
	import { BarChart, Highlight, type ChartContextValue } from 'layerchart';
	import { cubicInOut } from 'svelte/easing';
	import { SvelteSet } from 'svelte/reactivity';
	import { ChartContainer, ChartTooltip, type ChartConfig } from '$lib/components/ui/chart/index.js';
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
		/** Map from original series name -> CSS var ("--chart-1") or any CSS color ("var(--chart-1)") */
		colors?: Record<string, string>;
		/** Enable/disable animations (auto-disabled for large datasets) */
		animate?: boolean;
	}

	let { title = '', years = [], series = [], height = '600px', colors = {}, animate = true }: Props = $props();
	let containerWidth = $state(0);
	let context = $state<ChartContextValue>();
	let mounted = $state(false);

	$effect(() => {
		mounted = true;
	});

	// Track hidden series for legend toggling
	const hiddenSeries = new SvelteSet<string>();

	// Compute whether to animate based on data size (disable for large datasets)
	const totalDataPoints = $derived(years.length * series.length);
	const shouldAnimate = $derived(animate && totalDataPoints < 500);
	// Faster animation duration (200ms instead of 500ms)
	const animationDuration = $derived(totalDataPoints > 200 ? 150 : 200);

	const defaultColorVars: Record<string, string> = {
		// Base document types
		'Press Article': '--chart-1',
		'Islamic Periodical': '--chart-2',
		Document: '--chart-3',
		Audiovisuel: '--chart-4',
		// Reference types
		'Article de revue': '--chart-2',
		Livre: '--chart-8',
		Chapitre: '--chart-3',
		Communication: '--chart-4',
		'Compte rendu': '--chart-1',
		'Article de blog': '--chart-12',
		'Ouvrage collectif': '--chart-7',
		Rapport: '--chart-10',
		Thèse: '--chart-14'
	};

	const chartColorVars = [
		'--chart-1',
		'--chart-2',
		'--chart-3',
		'--chart-4',
		'--chart-5',
		'--chart-6',
		'--chart-7',
		'--chart-8',
		'--chart-9',
		'--chart-10',
		'--chart-11',
		'--chart-12',
		'--chart-13',
		'--chart-14',
		'--chart-15',
		'--chart-16'
	];

	function normalizeColor(value: string): string {
		if (!value) return 'var(--chart-1)';
		if (value.startsWith('var(')) return value;
		if (value.startsWith('--')) return `var(${value})`;
		return value;
	}

	function colorForType(typeName: string, index: number): string {
		const override = colors[typeName];
		if (override) return normalizeColor(override);
		const varName = defaultColorVars[typeName];
		if (varName) return `var(${varName})`;
		return `var(${chartColorVars[index % chartColorVars.length]})`;
	}

	const seriesDefs = $derived.by(() => {
		const _ = languageStore.current;
		return series.map((s, index) => {
			const translationKey = `type.${s.name}`;
			const translated = t(translationKey) !== translationKey ? t(translationKey) : s.name;
			return {
				key: `s${index}`,
				name: s.name,
				label: translated,
				color: colorForType(s.name, index)
			};
		});
	});

	const chartConfig = $derived.by(() => {
		const config: ChartConfig = {};
		for (const def of seriesDefs) {
			config[def.key] = { label: def.label, color: def.color };
		}
		return config;
	});

	type Datum = { year: string } & Record<string, number>;
	const chartData = $derived.by(() => {
		return years.map((year, yearIndex) => {
			const row: Record<string, any> = { year: String(year) };
			for (const [seriesIndex, def] of seriesDefs.entries()) {
				row[def.key] = series[seriesIndex]?.data?.[yearIndex] ?? 0;
			}
			return row as Datum;
		});
	});

	const perItemWidth = $derived.by(() => {
		const count = Math.max(1, years.length);
		return containerWidth > 0 ? containerWidth / count : 0;
	});

	const effectiveXAxisLabelRotate = $derived.by(() => {
		if (perItemWidth <= 0) return 0;
		if (perItemWidth < 55) return 90;
		if (perItemWidth < 90) return 45;
		return 0;
	});

	const xAxisTicks = $derived.by(() => {
		if (years.length <= 1) return 1;
		if (!perItemWidth) return 1;
		const minLabelSpace = effectiveXAxisLabelRotate >= 45 ? 50 : 90;
		return Math.max(1, Math.ceil(minLabelSpace / perItemWidth));
	});

	const bottomPadding = $derived.by(() => {
		if (effectiveXAxisLabelRotate >= 90) return 110;
		if (effectiveXAxisLabelRotate > 0) return 80;
		return years.length > 15 ? 60 : 40;
	});

	function tooltipItemsWithValues(payload: any[]) {
		return (payload ?? []).filter((item) => {
			const raw = item?.value;
			const value = typeof raw === 'number' ? raw : Number(raw);
			return Number.isFinite(value) && value >= 1;
		});
	}

	// Filter series based on hidden state
	const visibleSeriesDefs = $derived.by(() => {
		return seriesDefs.filter((def) => !hiddenSeries.has(def.key));
	});

	// Sorted series definitions for legend display (alphabetical by label)
	const sortedSeriesDefs = $derived.by(() => {
		return [...seriesDefs].sort((a, b) => a.label.localeCompare(b.label));
	});

	// Toggle series visibility
	function toggleSeries(key: string) {
		if (hiddenSeries.has(key)) {
			hiddenSeries.delete(key);
		} else {
			hiddenSeries.add(key);
		}
	}
</script>

<div
	bind:clientWidth={containerWidth}
	class="flex w-full flex-col"
	style="height: {height};"
	role="img"
	aria-label={t('chart.documents_by_type_over_years_aria')}
>
	{#if mounted && containerWidth > 0 && chartData.length > 0 && seriesDefs.length > 0}
		<!-- Chart area takes remaining space -->
		<div class="min-h-0 flex-1">
			<ChartContainer
				config={chartConfig}
				class="h-full w-full min-w-0 aspect-auto justify-start"
			>
			<BarChart
				bind:context
				data={chartData}
				xScale={scaleBand().padding(0.25)}
				x="year"
				axis="x"
				rule={false}
				padding={{ left: 52, right: 16, top: title ? 24 : 8, bottom: bottomPadding }}
				series={visibleSeriesDefs.map((def, index) => ({
					key: def.key,
					label: def.label,
					color: def.color,
					props: index === 0 ? { rounded: 'bottom' } : undefined
				}))}
				seriesLayout="stack"
				legend={false}
				props={{
					bars: {
						stroke: 'none',
						initialY: shouldAnimate ? context?.height : undefined,
						initialHeight: shouldAnimate ? 0 : undefined,
						motion: shouldAnimate
							? {
									y: { type: 'tween', duration: animationDuration, easing: cubicInOut },
									height: { type: 'tween', duration: animationDuration, easing: cubicInOut }
								}
							: undefined
					},
					highlight: { area: false },
					xAxis: {
						ticks: xAxisTicks,
						format: (d: string) => d,
						tickLabelProps: {
							rotate: effectiveXAxisLabelRotate > 0 ? effectiveXAxisLabelRotate : undefined,
							textAnchor: effectiveXAxisLabelRotate > 0 ? 'start' : 'middle',
							dy: effectiveXAxisLabelRotate > 0 ? '0.5em' : undefined,
							dx: effectiveXAxisLabelRotate > 0 ? 2 : undefined
						}
					}
				}}
			>
				{#snippet belowMarks()}
					<Highlight area={{ class: 'fill-muted' }} />
				{/snippet}

				{#snippet tooltip({ context })}
					<ChartTooltip items={tooltipItemsWithValues(context.tooltip?.payload ?? [])} />
				{/snippet}
			</BarChart>
			</ChartContainer>
		</div>

		<!-- Custom centered legend with click-to-toggle (fixed height, no shrink) -->
		<div class="flex shrink-0 flex-wrap items-center justify-center gap-x-4 gap-y-2 pb-2 pt-3">
			{#each sortedSeriesDefs as def (def.key)}
				<button
					type="button"
					class="flex cursor-pointer items-center gap-1.5 text-sm transition-opacity hover:opacity-80"
					class:opacity-40={hiddenSeries.has(def.key)}
					onclick={() => toggleSeries(def.key)}
				>
					<span
						class="h-3 w-3 shrink-0 rounded-full"
						style="background-color: {def.color};"
					></span>
					<span class="text-foreground">{def.label}</span>
				</button>
			{/each}
		</div>
	{:else}
		<div class="flex h-full w-full items-center justify-center text-muted-foreground">{t('chart.no_data')}</div>
	{/if}
</div>

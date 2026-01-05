<script lang="ts">
	import { t } from '$lib/stores/translationStore.svelte.js';
	import StatsCard from '$lib/components/stats-card.svelte';
	import LayerChartDuration from '$lib/components/charts/LayerChartDuration.svelte';
	import { Card } from '$lib/components/ui/card/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';

	// Types
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

	// Placeholder data - to be replaced with real data from API/JSON later
	const placeholderData: NewspaperCoverage[] = [
		{
			name: 'Fraternité Matin',
			country: "Côte d'Ivoire",
			totalArticles: 931,
			periods: [{ start: 1960, end: 2023 }]
		},
		{
			name: 'Togo-Presse',
			country: 'Togo',
			totalArticles: 1129,
			periods: [
				{ start: 1960, end: 1973 },
				{ start: 1981, end: 2025 }
			]
		}
	];

	// State
	let loading = $state(false);
	let data = $state<NewspaperCoverage[]>(placeholderData);

	// Computed stats
	const totalNewspapers = $derived(data.length);
	const yearRange = $derived.by(() => {
		const allYears = data.flatMap((n) => n.periods.flatMap((p) => [p.start, p.end]));
		if (allYears.length === 0) return { min: 0, max: 0 };
		return { min: Math.min(...allYears), max: Math.max(...allYears) };
	});
	const countries = $derived([...new Set(data.map((n) => n.country))]);
	const totalArticles = $derived(data.reduce((sum, n) => sum + n.totalArticles, 0));
</script>

<svelte:head>
	<title>{t('coverage.title')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 py-6">
	<!-- Page Header -->
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight text-foreground">{t('coverage.title')}</h1>
		<p class="text-muted-foreground">{t('coverage.description')}</p>
	</div>

	{#if loading}
		<div class="grid gap-4 md:grid-cols-4">
			<Skeleton class="h-24" />
			<Skeleton class="h-24" />
			<Skeleton class="h-24" />
			<Skeleton class="h-24" />
		</div>
		<Skeleton class="h-100" />
	{:else}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-4">
			<StatsCard title={t('coverage.total_newspapers')} value={totalNewspapers.toLocaleString()} />
			<StatsCard title={t('coverage.year_range')} value="{yearRange.min}-{yearRange.max}" />
			<StatsCard title={t('stats.countries')} value={countries.length.toLocaleString()} />
			<StatsCard title={t('coverage.articles')} value={totalArticles.toLocaleString()} />
		</div>

		<!-- Duration Chart -->
		<Card class="p-6">
			<div class="mb-4 space-y-1">
				<h2 class="text-lg font-semibold">{t('coverage.chart_title')}</h2>
				<p class="text-sm text-muted-foreground">{t('coverage.chart_description')}</p>
			</div>
			<LayerChartDuration {data} height={Math.max(200, data.length * 60)} />
		</Card>

		<!-- Legend -->
		<Card class="p-4">
			<div class="flex flex-wrap gap-4">
				{#each countries as country}
					<div class="flex items-center gap-2">
						<div
							class="h-3 w-3 rounded-sm"
							style="background-color: {country === "Côte d'Ivoire"
								? 'var(--chart-1)'
								: 'var(--chart-2)'}"
						></div>
						<span class="text-sm">{country}</span>
					</div>
				{/each}
			</div>
		</Card>
	{/if}
</div>

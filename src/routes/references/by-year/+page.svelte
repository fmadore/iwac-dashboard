<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { Loader2 } from '@lucide/svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import { StackedBarChart } from '$lib/components/visualizations/charts/d3/index.js';

	// Use URL sync hook
	const urlSync = useUrlSync();

	interface SeriesData {
		name: string;
		data: number[];
	}

	interface ByYearData {
		years: number[];
		series: SeriesData[];
		total_records: number;
		year_range: {
			min: number;
			max: number;
		};
		country: string | null;
		generated_at: string;
	}

	interface MetadataResponse {
		total_records: number;
		records_with_year: number;
		temporal: {
			min_year: number;
			max_year: number;
			year_count: number;
		};
		countries: {
			count: number;
			values: string[];
			with_individual_files: string[];
			counts: Record<string, number>;
		};
		reference_types: {
			count: number;
			values: string[];
		};
	}

	// Get preloaded data from +page.ts
	let { data: pageData } = $props<{
		data: {
			globalData: ByYearData | null;
			metadata: MetadataResponse | null;
			error: string | null;
		};
	}>();

	// Use preloaded data directly - derive from props to stay reactive
	const globalData = $derived(pageData.globalData);
	const metadata = $derived(pageData.metadata);
	let countryData = $state<ByYearData | null>(null);
	let countryLoading = $state(false);
	let chartReady = $state(false);
	const error = $derived(pageData.error);

	// Defer chart rendering to allow other UI to paint
	onMount(() => {
		const timer = setTimeout(() => {
			chartReady = true;
		}, 100);
		return () => clearTimeout(timer);
	});

	// Filter states from URL
	const selectedCountry = $derived(urlSync.filters.country);

	async function loadCountryData(country: string | undefined) {
		if (!country) {
			countryData = null;
			return;
		}

		try {
			countryLoading = true;
			const filename = country.toLowerCase().replace(/\s+/g, '-');
			const response = await fetch(`${base}/data/references/by-year-${filename}.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			countryData = await response.json();
		} catch (e) {
			console.error(`Error loading country data for ${country}:`, e);
			countryData = null;
		} finally {
			countryLoading = false;
		}
	}

	// Watch for country selection changes
	$effect(() => {
		loadCountryData(selectedCountry);
	});

	// Get active data based on country selection
	const activeData = $derived(selectedCountry ? countryData : globalData);

	const countryOptions = $derived(metadata?.countries.with_individual_files ?? []);

	// Handlers for filter changes
	function handleCountryChange(value: string | undefined) {
		if (value && value !== 'all-countries') {
			urlSync.setFilter('country', value);
		} else {
			urlSync.clearFilter('country');
		}
	}

	function handleClearFilters() {
		urlSync.clearFilters();
	}
</script>

<svelte:head>
	<title>{t('nav.references_by_year')} - {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 p-6">
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight">{t('nav.references_by_year')}</h1>
		<p class="text-muted-foreground">
			Distribution of bibliographic references over time by document type
		</p>
	</div>

	{#if !globalData && !error}
		<Card.Root>
			<Card.Header>
				<Skeleton class="h-8 w-64" />
			</Card.Header>
			<Card.Content>
				<Skeleton class="h-96 w-full" />
			</Card.Content>
		</Card.Root>
	{:else if error}
		<Card.Root>
			<Card.Header>
				<Card.Title>Error</Card.Title>
			</Card.Header>
			<Card.Content>
				<p class="text-destructive">{error}</p>
				<p class="mt-4 text-sm text-muted-foreground">
					This visualization requires data generation. Please run:
					<code class="rounded bg-muted px-2 py-1">python scripts/generate_references.py</code>
				</p>
			</Card.Content>
		</Card.Root>
	{:else if activeData}
		<div class="space-y-4">
			<!-- Statistics Cards -->
			<div class="grid gap-4 md:grid-cols-3">
				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground"
							>Total References</Card.Title
						>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">{activeData.total_records.toLocaleString()}</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground">Year Range</Card.Title>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">
							{activeData.year_range.min}–{activeData.year_range.max}
						</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground"
							>Reference Types</Card.Title
						>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">{activeData.series.length}</div>
					</Card.Content>
				</Card.Root>
			</div>

			<!-- Country Filter -->
			<Card.Root>
				<Card.Header>
					<Card.Title>{t('filters.title')}</Card.Title>
					<Card.Description>{t('filters.description')}</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="flex flex-wrap items-center gap-4">
						<div class="flex items-center gap-2">
							<label for="countrySelect" class="text-sm font-medium">{t('filters.country')}:</label>
							<Select.Root
								type="single"
								value={selectedCountry ?? 'all-countries'}
								onValueChange={(v) => handleCountryChange(v === 'all-countries' ? undefined : v)}
							>
								<Select.Trigger class="w-50" id="countrySelect">
									{selectedCountry || t('filters.all_countries')}
								</Select.Trigger>
								<Select.Content>
									<Select.Item value="all-countries">{t('filters.all_countries')}</Select.Item>
									{#each countryOptions as country}
										<Select.Item value={country}>{country}</Select.Item>
									{/each}
								</Select.Content>
							</Select.Root>
						</div>
						{#if selectedCountry}
							<Button variant="secondary" size="sm" onclick={handleClearFilters}>
								{t('filters.clear')}
							</Button>
						{/if}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Stacked Bar Chart -->
			<Card.Root>
				<Card.Header>
					<Card.Title>
						{#if selectedCountry}
							References Distribution by Year and Type - {selectedCountry}
						{:else}
							References Distribution by Year and Type
						{/if}
					</Card.Title>
					<Card.Description>
						Temporal distribution of bibliographic references by document type
					</Card.Description>
				</Card.Header>
				<Card.Content>
					{#if chartReady && !countryLoading}
						<StackedBarChart years={activeData.years} series={activeData.series} height="600px" />
					{:else}
						<div class="flex h-[600px] w-full flex-col items-center justify-center gap-4">
							<Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
							<p class="text-sm text-muted-foreground">
								{countryLoading ? t('common.loading') : t('categories.loading_chart')}
							</p>
						</div>
					{/if}
				</Card.Content>
			</Card.Root>
		</div>
	{/if}
</div>

<style>
	:global(body) {
		overflow-y: auto;
	}
</style>

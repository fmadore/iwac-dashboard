<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { Loader2 } from '@lucide/svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Slider } from '$lib/components/ui/slider/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import StackedBarChart from '$lib/components/charts/StackedBarChart.svelte';

	// Use URL sync hook
	const urlSync = useUrlSync();

	interface SeriesData {
		name: string;
		data: number[];
	}

	interface CategoryData {
		years: number[];
		series: SeriesData[];
		total_records: number;
		year_range: {
			min: number;
			max: number;
		};
	}

	interface MetadataResponse {
		total_records: number;
		temporal: {
			min_year: number;
			max_year: number;
			year_count: number;
		};
		countries: {
			count: number;
			values: string[];
			with_individual_files: string[];
		};
		document_types: {
			count: number;
			values: string[];
		};
	}

	// Get preloaded data from +page.ts
	let { data: pageData } = $props<{
		data: {
			globalData: CategoryData | null;
			metadata: MetadataResponse | null;
			error: string | null;
		};
	}>();

	// Use preloaded data directly - derive from props to stay reactive
	const globalData = $derived(pageData.globalData);
	const metadata = $derived(pageData.metadata);
	let countryData = $state<CategoryData | null>(null);
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

	// Year range as derived value that reads from URL or defaults
	const yearRange = $derived<[number, number]>(
		(() => {
			const min = urlSync.filters.yearMin;
			const max = urlSync.filters.yearMax;
			if (min !== undefined && max !== undefined) {
				return [min, max];
			}
			return [metadata?.temporal.min_year || 1912, metadata?.temporal.max_year || 2025];
		})()
	);

	// Local state for slider to avoid heavy re-renders while dragging
	let localYearRange = $state<[number, number]>([1912, 2025]);

	// Sync local state with URL state
	$effect(() => {
		localYearRange = yearRange;
	});

	// Set initial year range from metadata on mount
	$effect(() => {
		if (metadata && !urlSync.hasFilter('yearMin') && !urlSync.hasFilter('yearMax')) {
			urlSync.setFilters({
				yearMin: metadata.temporal.min_year,
				yearMax: metadata.temporal.max_year
			});
		}
	});

	async function loadCountryData(country: string | undefined) {
		if (!country) {
			countryData = null;
			return;
		}

		try {
			countryLoading = true;
			const filename = country.toLowerCase().replace(/\s+/g, '-');
			const response = await fetch(`${base}/data/categories/${filename}.json`);
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
	const activeData = $derived(() => (selectedCountry ? countryData : globalData));

	// Filter data by year range
	const filteredData = $derived(() => {
		const data = activeData();
		if (!data) return null;

		const [minYear, maxYear] = yearRange;
		const yearIndices: number[] = [];
		const filteredYears: number[] = [];

		data.years.forEach((year, index) => {
			if (year >= minYear && year <= maxYear) {
				yearIndices.push(index);
				filteredYears.push(year);
			}
		});

		const filteredSeries = data.series.map((s) => ({
			name: s.name,
			data: yearIndices.map((i) => s.data[i])
		}));

		const total = filteredSeries.reduce((sum, s) => sum + s.data.reduce((a, b) => a + b, 0), 0);

		return {
			years: filteredYears,
			series: filteredSeries,
			total_records: total,
			year_range: {
				min: Math.min(...filteredYears),
				max: Math.max(...filteredYears)
			}
		};
	});

	const countryOptions = $derived(() => metadata?.countries.with_individual_files ?? []);

	// Handlers for filter changes
	function handleCountryChange(value: string | undefined) {
		if (value && value !== 'all-countries') {
			urlSync.setFilter('country', value);
		} else {
			urlSync.clearFilter('country');
		}
	}

	function handleYearRangeChange(value: number[]) {
		if (value.length === 2) {
			urlSync.setFilters({
				yearMin: value[0],
				yearMax: value[1]
			});
		}
	}

	function handleClearFilters() {
		urlSync.clearFilters();
	}
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{t('nav.categories')}</h2>
		<p class="text-muted-foreground">{t('categories.description')}</p>
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
			<Card.Content class="py-12">
				<div class="text-center">
					<p class="text-destructive">{t('errors.failed_to_load')}: {error}</p>
				</div>
			</Card.Content>
		</Card.Root>
	{:else if filteredData()}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-3">
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Title class="text-sm font-medium text-muted-foreground"
						>{t('categories.total_records')}</Card.Title
					>
					<div class="text-2xl font-bold">{filteredData()!.total_records.toLocaleString()}</div>
				</Card.Header>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Title class="text-sm font-medium text-muted-foreground"
						>{t('categories.year_range')}</Card.Title
					>
					<div class="text-2xl font-bold">
						{filteredData()!.year_range.min} - {filteredData()!.year_range.max}
					</div>
				</Card.Header>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Title class="text-sm font-medium text-muted-foreground"
						>{t('categories.document_types')}</Card.Title
					>
					<div class="text-2xl font-bold">{filteredData()!.series.length}</div>
				</Card.Header>
			</Card.Root>
		</div>

		<!-- Filters -->
		<Card.Root>
			<Card.Header>
				<Card.Title>{t('filters.title')}</Card.Title>
				<Card.Description>{t('filters.description')}</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="space-y-6">
					<!-- Country Filter -->
					<div class="flex flex-wrap items-center gap-4">
						<div class="flex items-center gap-2">
							<label for="countrySelect" class="text-sm font-medium">{t('filters.country')}:</label>
							<Select.Root
								type="single"
								value={selectedCountry ?? 'all-countries'}
								onValueChange={(v) => handleCountryChange(v === 'all-countries' ? undefined : v)}
							>
								<Select.Trigger class="w-[200px]" id="countrySelect">
									{selectedCountry || t('filters.all_countries')}
								</Select.Trigger>
								<Select.Content>
									<Select.Item value="all-countries">{t('filters.all_countries')}</Select.Item>
									{#each countryOptions() as country}
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

					<!-- Year Range Slider -->
					{#if metadata}
						<div class="space-y-2">
							<div class="text-sm font-medium">
								{t('filters.year_range')}: {localYearRange[0]} - {localYearRange[1]}
							</div>
							<Slider
								type="multiple"
								bind:value={localYearRange}
								onValueCommit={handleYearRangeChange}
								min={metadata.temporal.min_year}
								max={metadata.temporal.max_year}
								step={1}
								class="w-full"
							/>
							<div class="flex justify-between text-xs text-muted-foreground">
								<span>{metadata.temporal.min_year}</span>
								<span>{metadata.temporal.max_year}</span>
							</div>
						</div>
					{/if}
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Stacked Bar Chart -->
		<Card.Root>
			<Card.Header>
				<Card.Title>
					{#if selectedCountry}
						{t('categories.chart_title')} - {selectedCountry}
					{:else}
						{t('categories.chart_title')}
					{/if}
				</Card.Title>
				<Card.Description>{t('categories.chart_description')}</Card.Description>
			</Card.Header>
			<Card.Content>
				{#if chartReady && !countryLoading}
					<StackedBarChart
						years={filteredData()!.years}
						series={filteredData()!.series}
						height="600px"
					/>
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
	{/if}
</div>

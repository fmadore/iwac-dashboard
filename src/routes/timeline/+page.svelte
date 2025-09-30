<script lang="ts">
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import TimelineChart from '$lib/components/charts/TimelineChart.svelte';
	import { t } from '$lib/stores/translationStore.js';

	// Prerender this page
	export const prerender = true;

	interface TimelineData {
		months: string[];
		monthly_additions: number[];
		cumulative_total: number[];
		total_records: number;
		month_range: {
			min: string;
			max: string;
		};
	}

	interface FacetData {
		label_en?: string;
		label_fr?: string;
		months: string[];
		monthly_additions: number[];
		cumulative_total: number[];
		total_records: number;
		month_range: {
			min: string;
			max: string;
		};
	}

	interface TypeFacets {
		facets: Record<string, FacetData>;
		types: string[];
	}

	interface CountryFacets {
		facets: Record<string, FacetData>;
		countries: string[];
	}

	interface MetadataResponse {
		total_records: number;
		unique_months: number;
		month_range: {
			min: string;
			max: string;
		};
		countries: string[];
		country_count: number;
		types: string[];
		type_count: number;
	}

	let globalData = $state<TimelineData | null>(null);
	let typeFacets = $state<TypeFacets | null>(null);
	let countryFacets = $state<CountryFacets | null>(null);
	let metadata = $state<MetadataResponse | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Filter states
	let selectedCountry = $state<string>('');
	let selectedType = $state<string>('');

	async function loadData() {
		try {
			const response = await fetch(`${base}/data/timeline-growth.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			globalData = await response.json();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load timeline data';
		}
	}

	async function loadTypeFacets() {
		try {
			const response = await fetch(`${base}/data/timeline-types.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			typeFacets = await response.json();
		} catch (e) {
			console.error('Failed to load type facets:', e);
		}
	}

	async function loadCountryFacets() {
		try {
			const response = await fetch(`${base}/data/timeline-countries.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			countryFacets = await response.json();
		} catch (e) {
			console.error('Failed to load country facets:', e);
		}
	}

	async function loadMetadata() {
		try {
			const response = await fetch(`${base}/data/timeline-metadata.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			metadata = await response.json();
		} catch (e) {
			console.error('Failed to load metadata:', e);
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		Promise.all([
			loadData(),
			loadTypeFacets(),
			loadCountryFacets(),
			loadMetadata()
		]);
	});

	// Get active data based on filters
	const activeData = $derived.by((): TimelineData | null => {
		if (selectedType && typeFacets) {
			return typeFacets.facets[selectedType] || null;
		}
		if (selectedCountry && countryFacets) {
			return countryFacets.facets[selectedCountry] || null;
		}
		return globalData;
	});

	const clearFilters = () => {
		selectedCountry = '';
		selectedType = '';
	};

	const hasActiveFilters = $derived(selectedCountry || selectedType);

	const typeOptions = $derived(typeFacets?.types ?? []);
	const countryOptions = $derived(countryFacets?.countries ?? []);

	// Get display label for selected type (translate if needed)
	const selectedTypeLabel = $derived.by(() => {
		if (!selectedType || !typeFacets) return selectedType;
		const facet = typeFacets.facets[selectedType];
		if (!facet) return selectedType;
		// Use French or English label based on current language
		return facet.label_fr || facet.label_en || selectedType;
	});
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{$t('timeline.title')}</h2>
		<p class="text-muted-foreground">{$t('timeline.description')}</p>
	</div>

	{#if loading}
		<Card.Root class="p-6">
			<div class="space-y-4">
				<Skeleton class="h-8 w-64" />
				<Skeleton class="h-[500px] w-full" />
			</div>
		</Card.Root>
	{:else if error}
		<Card.Root class="p-6">
			<div class="text-center py-12">
				<h3 class="text-xl font-semibold mb-2 text-destructive">{$t('common.error')}</h3>
				<p class="text-muted-foreground">{error}</p>
			</div>
		</Card.Root>
	{:else if activeData}
		<!-- Filters -->
		<Card.Root>
			<Card.Header>
				<Card.Title>{$t('filters.title')}</Card.Title>
				<Card.Description>{$t('filters.description')}</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="flex items-center gap-4 flex-wrap">
					<!-- Type Filter -->
					<div class="flex items-center gap-2">
						<label for="typeSelect" class="text-sm font-medium">{$t('timeline.by_type')}:</label>
						<Select.Root bind:value={selectedType} type="single">
							<Select.Trigger class="w-[200px]" id="typeSelect">
								{selectedTypeLabel || $t('filters.all_countries')}
							</Select.Trigger>
							<Select.Content>
								<Select.Group>
									<Select.Item value="">{$t('filters.all_countries')}</Select.Item>
									{#each typeOptions as type}
										<Select.Item value={type}>{type}</Select.Item>
									{/each}
								</Select.Group>
							</Select.Content>
						</Select.Root>
					</div>

					<!-- Country Filter -->
					<div class="flex items-center gap-2">
						<label for="countrySelect" class="text-sm font-medium">{$t('filters.country')}:</label>
						<Select.Root bind:value={selectedCountry} type="single">
							<Select.Trigger class="w-[200px]" id="countrySelect">
								{selectedCountry || $t('filters.all_countries')}
							</Select.Trigger>
							<Select.Content>
								<Select.Group>
									<Select.Item value="">{$t('filters.all_countries')}</Select.Item>
									{#each countryOptions as country}
										<Select.Item value={country}>{country}</Select.Item>
									{/each}
								</Select.Group>
							</Select.Content>
						</Select.Root>
					</div>

					{#if hasActiveFilters}
						<Button 
							variant="secondary"
							size="sm"
							onclick={clearFilters}
						>
							{$t('filters.clear')}
						</Button>
					{/if}
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-3">
			<Card.Root>
				<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
					<Card.Title class="text-sm font-medium">{$t('timeline.total_records')}</Card.Title>
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">{activeData.total_records.toLocaleString()}</div>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
					<Card.Title class="text-sm font-medium">{$t('timeline.month_range')}</Card.Title>
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">
						{activeData.month_range?.min || 'N/A'} - {activeData.month_range?.max || 'N/A'}
					</div>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
					<Card.Title class="text-sm font-medium">{$t('timeline.monthly_additions')}</Card.Title>
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">
						{activeData.months.length > 0 ? Math.round(activeData.total_records / activeData.months.length).toLocaleString() : '0'}
					</div>
					<p class="text-xs text-muted-foreground">Average per month</p>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Main Chart -->
		<Card.Root class="p-6">
			<Card.Header>
				<Card.Title>
					{#if selectedType}
						{$t('timeline.chart_title')} - {selectedTypeLabel}
					{:else if selectedCountry}
						{$t('timeline.chart_title')} - {selectedCountry}
					{:else}
						{$t('timeline.chart_title')}
					{/if}
				</Card.Title>
				<Card.Description>{$t('timeline.chart_description')}</Card.Description>
			</Card.Header>
			<Card.Content>
				<TimelineChart
					months={activeData.months}
					monthlyAdditions={activeData.monthly_additions}
					cumulativeTotal={activeData.cumulative_total}
				/>
			</Card.Content>
		</Card.Root>
	{/if}
</div>
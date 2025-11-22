<script lang="ts">
	import EChartsPieChart from '$lib/components/charts/EChartsPieChart.svelte';
	import TrendingUpIcon from '@lucide/svelte/icons/trending-up';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import FacetPie from '$lib/components/facets/FacetPie.svelte';
	import type { PageData } from './$types.js';

	// Use URL sync hook
	const urlSync = useUrlSync();

	let { data }: { data: PageData } = $props();

	const chartData = $derived(() =>
		(data.global?.data || [])
			.map((item, index) => ({
				label: item.label,
				value: item.value,
				color: `var(--chart-${(index % 10) + 1})`,
				percentage: item.percentage?.toFixed?.(1) ?? undefined
			}))
			.sort((a, b) => b.value - a.value)
	);

	// Color configuration for consistency
	const colorMap = $derived(() => {
		const map: Record<string, string> = {};
		filteredChartData().forEach((item, index) => {
			map[item.label] = `var(--chart-${(index % 10) + 1})`;
		});
		return map;
	});

	// Facet selection state from URL
	const selectedType = $derived(urlSync.filters.type);
	const selectedCountry = $derived(urlSync.filters.country);

	const typeOptions = $derived(() => data.types?.types ?? []);
	const countryOptions = $derived(() => data.countries?.countries ?? []);

	// Main chart data that updates based on selected facets
	// Priority: country > type (only one can be active at a time)
	const filteredChartData = $derived(() => {
		let sourceData = data.global?.data || [];

		// Apply country filter first (higher priority)
		if (selectedCountry && data.countries) {
			const facet = data.countries.facets[selectedCountry];
			sourceData = facet ? facet.data : [];
		}
		// Apply type filter only if no country is selected
		else if (selectedType && data.types) {
			const facet = data.types.facets[selectedType];
			sourceData = facet ? facet.data : [];
		}

		return sourceData
			.map((item, index) => ({
				label: item.label,
				value: item.value,
				color: `var(--chart-${(index % 10) + 1})`,
				percentage: item.percentage?.toFixed?.(1) ?? undefined
			}))
			.sort((a, b) => b.value - a.value);
	});

	const totalDocs = $derived(() => {
		// Priority: country > type (only one can be active at a time)
		if (selectedCountry && data.countries) {
			const facet = data.countries.facets[selectedCountry];
			return facet ? facet.total : 0;
		}
		if (selectedType && data.types) {
			const facet = data.types.facets[selectedType];
			return facet ? facet.total : 0;
		}
		return data.global?.total ?? 0;
	});

	// Handlers for filter changes
	function handleTypeChange(value: string | undefined) {
		if (value) {
			// When selecting a type, clear country filter
			urlSync.setFilters({ type: value, country: undefined });
		} else {
			urlSync.clearFilter('type');
		}
	}

	function handleCountryChange(value: string | undefined) {
		if (value) {
			// When selecting a country, clear type filter
			urlSync.setFilters({ country: value, type: undefined });
		} else {
			urlSync.clearFilter('country');
		}
	}

	function handleClearFilters() {
		urlSync.clearFilters();
	}
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{t('nav.languages')}</h2>
		<p class="text-muted-foreground">{t('chart.language_distribution_desc')}</p>
	</div>

	<!-- Filters -->
	<Card.Root>
		<Card.Header>
			<Card.Title>Filters</Card.Title>
			<Card.Description>Select filters to view specific language distributions</Card.Description>
		</Card.Header>
		<Card.Content>
			<div class="flex flex-wrap gap-4">
				<div class="flex items-center gap-2">
					<label for="typeSelect" class="text-sm font-medium">Type:</label>
					<Select.Root
						type="single"
						value={selectedType ?? 'all-types'}
						onValueChange={(v) => handleTypeChange(v === 'all-types' ? undefined : v)}
					>
						<Select.Trigger class="w-[180px]" id="typeSelect">
							{selectedType || 'All Types'}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="all-types">All Types</Select.Item>
							{#each typeOptions() as opt}
								<Select.Item value={opt}>{opt}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>
				{#if countryOptions().length > 0}
					<div class="flex items-center gap-2">
						<label for="countrySelect" class="text-sm font-medium">Country:</label>
						<Select.Root
							type="single"
							value={selectedCountry ?? 'all-countries'}
							onValueChange={(v) => handleCountryChange(v === 'all-countries' ? undefined : v)}
						>
							<Select.Trigger class="w-[180px]" id="countrySelect">
								{selectedCountry || 'All Countries'}
							</Select.Trigger>
							<Select.Content>
								<Select.Item value="all-countries">All Countries</Select.Item>
								{#each countryOptions() as opt}
									<Select.Item value={opt}>{opt}</Select.Item>
								{/each}
							</Select.Content>
						</Select.Root>
					</div>
				{/if}
				{#if selectedType || selectedCountry}
					<Button variant="secondary" size="sm" onclick={handleClearFilters}>Clear Filters</Button>
				{/if}
			</div>
		</Card.Content>
	</Card.Root>

	{#if !data.global}
		<Card.Root>
			<Card.Content class="p-6">
				<div class="space-y-4">
					<Skeleton class="h-6 w-[200px]" />
					<div class="flex h-[400px] items-center justify-center">
						<Skeleton class="h-[300px] w-[300px] rounded-full" />
					</div>
				</div>
			</Card.Content>
		</Card.Root>
	{:else}
		<div class="grid gap-6 lg:grid-cols-2">
			<!-- Pie Chart -->
			<Card.Root>
				<Card.Header class="pb-3">
					<Card.Title>
						{#if selectedType && selectedCountry}
							Languages in {selectedType} - {selectedCountry}
						{:else if selectedType}
							Languages in {selectedType}
						{:else if selectedCountry}
							Languages in {selectedCountry}
						{:else}
							{t('chart.language_distribution')}
						{/if}
					</Card.Title>
					<Card.Description>
						{filteredChartData().length} languages • {totalDocs().toLocaleString()}
						{t('chart.documents').toLowerCase()}
					</Card.Description>
				</Card.Header>
				<Card.Content class="pt-0">
					<div class="flex h-[500px] w-full items-center justify-center">
						{#if filteredChartData().length > 0}
							<EChartsPieChart
								data={filteredChartData()}
								innerRadius="35%"
								outerRadius="70%"
								showLabels={true}
								showValues={false}
								animationDuration={1000}
								minSlicePercent={0.5}
							/>
						{:else}
							<div class="flex h-[200px] items-center justify-center text-muted-foreground">
								No data available for selected filters
							</div>
						{/if}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Language Stats Table -->
			<Card.Root>
				<Card.Header class="pb-3">
					<Card.Title class="text-lg">Language Statistics</Card.Title>
					<Card.Description class="text-sm">Detailed breakdown by language</Card.Description>
				</Card.Header>
				<Card.Content class="pt-0">
					<div class="space-y-1">
						{#each filteredChartData() as item, index}
							<div class="flex items-center justify-between rounded-md border p-2 text-sm">
								<div class="flex items-center gap-2">
									<div
										class="h-3 w-3 flex-shrink-0 rounded-full"
										style="background-color: {colorMap()[item.label]}"
									></div>
									<span class="truncate font-medium">{item.label}</span>
								</div>
								<div class="ml-2 flex-shrink-0 text-right">
									<p class="text-sm font-semibold">{item.value}</p>
									{#if item.percentage}
										<p class="text-xs text-muted-foreground">{item.percentage}%</p>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	{/if}
</div>

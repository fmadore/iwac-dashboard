<script lang="ts">
	import { PieChart as LayerChartPieChart } from '$lib/components/visualizations/charts/layerchart/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { useFilters } from '$lib/hooks/index.js';
	import type { PageData } from './$types.js';

	// Use enhanced filters hook with mutual exclusivity for type/country
	const filters = useFilters({
		mutuallyExclusive: [['type', 'country']]
	});

	let { data }: { data: PageData } = $props();

	// Stable, global label → color mapping.
	// This prevents filters from re-assigning colors (e.g. showing French as a different color).
	const globalColorMap = $derived(() => {
		const map: Record<string, string> = {};
		const global = data.global?.data ?? [];
		// Match the existing behavior on the unfiltered view: sort by value.
		const sorted = [...global].sort((a, b) => b.value - a.value);
		sorted.forEach((item, index) => {
			map[item.label] = `var(--chart-${(index % 16) + 1})`;
		});
		return map;
	});

	// Facet selection state from URL (now managed by useFilters)
	const selectedType = $derived(filters.get('type'));
	const selectedCountry = $derived(filters.get('country'));

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
				color: globalColorMap()[item.label] ?? `var(--chart-${(index % 16) + 1})`,
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

	// Handlers for filter changes - simplified with mutual exclusivity built in
	function handleTypeChange(value: string | undefined) {
		if (value) {
			filters.set('type', value); // Automatically clears country due to mutuallyExclusive config
		} else {
			filters.clear('type');
		}
	}

	function handleCountryChange(value: string | undefined) {
		if (value) {
			filters.set('country', value); // Automatically clears type due to mutuallyExclusive config
		} else {
			filters.clear('country');
		}
	}

	function handleClearFilters() {
		filters.clearAll();
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
			<Card.Title>{t('filters.title')}</Card.Title>
			<Card.Description>{t('filters.description')}</Card.Description>
		</Card.Header>
		<Card.Content>
			<div class="flex flex-wrap gap-4">
				<div class="flex items-center gap-2">
					<label for="typeSelect" class="text-sm font-medium">{t('filters.type')}:</label>
					<Select.Root
						type="single"
						value={selectedType ?? 'all-types'}
						onValueChange={(v) => handleTypeChange(v === 'all-types' ? undefined : v)}
					>
						<Select.Trigger class="w-[180px]" id="typeSelect">
							{selectedType || t('filters.all_types')}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="all-types">{t('filters.all_types')}</Select.Item>
							{#each typeOptions() as opt (opt)}
								<Select.Item value={opt}>{opt}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>
				{#if countryOptions().length > 0}
					<div class="flex items-center gap-2">
						<label for="countrySelect" class="text-sm font-medium">{t('filters.country')}:</label>
						<Select.Root
							type="single"
							value={selectedCountry ?? 'all-countries'}
							onValueChange={(v) => handleCountryChange(v === 'all-countries' ? undefined : v)}
						>
							<Select.Trigger class="w-[180px]" id="countrySelect">
								{selectedCountry || t('filters.all_countries')}
							</Select.Trigger>
							<Select.Content>
								<Select.Item value="all-countries">{t('filters.all_countries')}</Select.Item>
								{#each countryOptions() as opt (opt)}
									<Select.Item value={opt}>{opt}</Select.Item>
								{/each}
							</Select.Content>
						</Select.Root>
					</div>
				{/if}
				{#if filters.hasActiveFilters}
					<Button variant="secondary" size="sm" onclick={handleClearFilters}
						>{t('filters.clear')}</Button
					>
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
		<Card.Root>
			<Card.Header class="pb-3">
				<Card.Title>
					{#if selectedType && selectedCountry}
						{t('chart.languages_in_type_country', [selectedType, selectedCountry])}
					{:else if selectedType}
						{t('chart.languages_in_type', [selectedType])}
					{:else if selectedCountry}
						{t('chart.languages_in_country', [selectedCountry])}
					{:else}
						{t('chart.language_distribution')}
					{/if}
				</Card.Title>
				<Card.Description>
					{t('chart.languages_count', [String(filteredChartData().length)])} •
					{totalDocs().toLocaleString()}
					{t('chart.documents').toLowerCase()}
				</Card.Description>
			</Card.Header>
			<Card.Content class="pt-0">
				<div class="mx-auto w-full max-w-xl">
					{#if filteredChartData().length > 0}
						<LayerChartPieChart
							data={filteredChartData()}
							innerRadius="35%"
							outerRadius="80%"
							showLabels={true}
							showValues={true}
							animationDuration={1000}
							minSlicePercent={0.5}
						/>
					{:else}
						<div class="flex h-[200px] items-center justify-center text-muted-foreground">
							{t('chart.no_data_for_filters')}
						</div>
					{/if}
				</div>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

<script lang="ts">
	import PieChart from '$lib/components/charts/PieChart.svelte';
	import TrendingUpIcon from "@lucide/svelte/icons/trending-up";
	import * as Card from "$lib/components/ui/card/index.js";
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.js';
	import FacetPie from '$lib/components/facets/FacetPie.svelte';
	import type { PageData } from './$types.js';
	
	let { data }: { data: PageData } = $props();

	const chartData = $derived(() =>
		(data.global?.data || [])
			.map((item, index) => ({
				label: item.label,
				value: item.value,
				color: `var(--chart-${(index % 5) + 1})`,
				percentage: item.percentage?.toFixed?.(1) ?? undefined
			}))
			.sort((a, b) => b.value - a.value)
	);

	// Color configuration for consistency
	const colorMap = $derived(() => {
		const map: Record<string, string> = {};
		filteredChartData().forEach((item, index) => {
			map[item.label] = `var(--chart-${(index % 5) + 1})`;
		});
		return map;
	});

	// Facet selection state
	let selectedType = $state<string>('');
	let selectedCountry = $state<string>('');
	
	const typeOptions = $derived(() => data.types?.types ?? []);
	const countryOptions = $derived(() => data.countries?.countries ?? []);
	
	// Main chart data that updates based on selected facets
	const filteredChartData = $derived(() => {
		let sourceData = data.global?.data || [];
		
		// Apply type filter
		if (selectedType && data.types) {
			const facet = data.types.facets[selectedType];
			sourceData = facet ? facet.data : [];
		}
		
		// Apply country filter
		if (selectedCountry && data.countries) {
			const facet = data.countries.facets[selectedCountry];
			sourceData = facet ? facet.data : [];
		}
		
		return sourceData.map((item, index) => ({
			label: item.label,
			value: item.value,
			color: `var(--chart-${(index % 5) + 1})`,
			percentage: item.percentage?.toFixed?.(1) ?? undefined
		})).sort((a, b) => b.value - a.value);
	});
	
	const totalDocs = $derived(() => {
		if (selectedType && data.types) {
			const facet = data.types.facets[selectedType];
			return facet ? facet.total : 0;
		}
		if (selectedCountry && data.countries) {
			const facet = data.countries.facets[selectedCountry];
			return facet ? facet.total : 0;
		}
		return data.global?.total ?? 0;
	});
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{$t('nav.languages')}</h2>
		<p class="text-muted-foreground">{$t('chart.language_distribution_desc')}</p>
	</div>

	<!-- Filters -->
	<Card.Root>
		<Card.Header>
			<Card.Title>Filters</Card.Title>
			<Card.Description>Select filters to view specific language distributions</Card.Description>
		</Card.Header>
		<Card.Content>
			<div class="flex gap-4 flex-wrap">
				<div class="flex items-center gap-2">
					<label for="typeSelect" class="text-sm font-medium">Type:</label>
					<select id="typeSelect" bind:value={selectedType} class="border rounded px-3 py-1 min-w-[140px]">
						<option value="">All Types</option>
						{#each typeOptions() as opt}
							<option value={opt}>{opt}</option>
						{/each}
					</select>
				</div>
				{#if countryOptions().length > 0}
				<div class="flex items-center gap-2">
					<label for="countrySelect" class="text-sm font-medium">Country:</label>
					<select id="countrySelect" bind:value={selectedCountry} class="border rounded px-3 py-1 min-w-[140px]">
						<option value="">All Countries</option>
						{#each countryOptions() as opt}
							<option value={opt}>{opt}</option>
						{/each}
					</select>
				</div>
				{/if}
				{#if selectedType || selectedCountry}
				<button 
					class="px-3 py-1 text-sm bg-secondary text-secondary-foreground rounded hover:bg-secondary/80"
					onclick={() => { selectedType = ''; selectedCountry = ''; }}
				>
					Clear Filters
				</button>
				{/if}
			</div>
		</Card.Content>
	</Card.Root>

	{#if !data.global}
		<Card.Root>
			<Card.Content class="p-6">
				<div class="space-y-4">
					<Skeleton class="h-6 w-[200px]" />
					<div class="h-[400px] flex items-center justify-center">
						<Skeleton class="h-[300px] w-[300px] rounded-full" />
					</div>
				</div>
			</Card.Content>
		</Card.Root>
	{:else}
		<div class="grid gap-6 md:grid-cols-2">
			<!-- Pie Chart -->
			<Card.Root>
				<Card.Header>
					<Card.Title>
						{#if selectedType && selectedCountry}
							Languages in {selectedType} - {selectedCountry}
						{:else if selectedType}
							Languages in {selectedType}
						{:else if selectedCountry}
							Languages in {selectedCountry}
						{:else}
							{$t('chart.language_distribution')}
						{/if}
					</Card.Title>
					<Card.Description>
						Total: {totalDocs()} {$t('chart.documents').toLowerCase()}
					</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="mx-auto aspect-square max-h-[400px] flex items-center justify-center">
						{#if filteredChartData().length > 0}
							<PieChart
								data={filteredChartData()}
								innerRadius={60}
								outerRadius={160}
								showLabels={true}
								showValues={false}
								animationDuration={1000}
								padAngle={0.01}
								cornerRadius={4}
							/>
						{:else}
							<div class="flex items-center justify-center h-[200px] text-muted-foreground">
								No data available for selected filters
							</div>
						{/if}
					</div>
				</Card.Content>
				<Card.Footer class="flex-col items-start gap-2 text-sm">
					<div class="flex gap-2 font-medium leading-none">
						Language distribution <TrendingUpIcon class="h-4 w-4" />
					</div>
					<div class="leading-none text-muted-foreground">
						Showing distribution across {filteredChartData().length} languages
					</div>
				</Card.Footer>
			</Card.Root>

			<!-- Language Stats Table -->
			<Card.Root>
				<Card.Header>
					<Card.Title>Language Statistics</Card.Title>
					<Card.Description>Detailed breakdown by language</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="space-y-2">
						{#each filteredChartData() as item, index}
							<div class="flex items-center justify-between p-3 border rounded-lg">
								<div class="flex items-center gap-3">
									<div 
										class="w-4 h-4 rounded-full" 
										style="background-color: {colorMap()[item.label]}"
									></div>
									<span class="font-medium">{item.label}</span>
								</div>
								<div class="text-right">
									<p class="font-semibold">{item.value}</p>
									{#if item.percentage}
										<p class="text-sm text-muted-foreground">{item.percentage}%</p>
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

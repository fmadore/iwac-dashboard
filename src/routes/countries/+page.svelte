<script lang="ts">
	import { Card } from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { ChevronRight, ChevronDown } from '@lucide/svelte';
	import { itemsStore } from '$lib/stores/itemsStore.js';
	import { t } from '$lib/stores/translationStore.js';

	let expandedCountries: Set<string> = new Set();

	$: countryData = getCountryData($itemsStore.items);

	function getCountryData(items: any[]) {
		const countryMap = new Map();
		
		items.forEach(item => {
			if (!item.country) return;
			
			if (!countryMap.has(item.country)) {
				countryMap.set(item.country, {
					name: item.country,
					count: 0,
					types: new Map()
				});
			}
			
			const country = countryMap.get(item.country);
			country.count++;
			
			if (item.type) {
				if (!country.types.has(item.type)) {
					country.types.set(item.type, 0);
				}
				country.types.set(item.type, country.types.get(item.type) + 1);
			}
		});
		
		const total = items.length;
		return Array.from(countryMap.values())
			.map(country => ({
				...country,
				percentage: (country.count / total) * 100,
				children: Array.from(country.types.entries()).map(([type, count]: [string, number]) => ({
					name: type,
					count,
					percentage: (count / country.count) * 100
				}))
			}))
			.sort((a, b) => b.count - a.count);
	}

	function toggleCountry(country: string) {
		if (expandedCountries.has(country)) {
			expandedCountries.delete(country);
		} else {
			expandedCountries.add(country);
		}
		expandedCountries = expandedCountries;
	}
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{$t('nav.countries')}</h2>
		<p class="text-muted-foreground">Distribution of documents by country</p>
	</div>

	<Card class="p-6">
		<h3 class="text-xl font-semibold mb-6">Country Distribution</h3>
		
		<div class="space-y-2">
			{#each countryData as country}
				<div class="border rounded-lg">
					<button
						class="w-full flex items-center justify-between p-4 hover:bg-accent/5 transition-colors"
						on:click={() => toggleCountry(country.name)}
					>
						<div class="flex items-center gap-3">
							{#if expandedCountries.has(country.name)}
								<ChevronDown class="w-4 h-4" />
							{:else}
								<ChevronRight class="w-4 h-4" />
							{/if}
							<span class="font-medium">{country.name}</span>
							<Badge variant="secondary">{country.count} items</Badge>
						</div>
						<div class="text-sm text-muted-foreground">
							{country.percentage.toFixed(1)}%
						</div>
					</button>
					
					{#if expandedCountries.has(country.name)}
						<div class="border-t px-8 py-2">
							{#each country.children as category}
								<div class="py-2 flex justify-between items-center">
									<span class="text-sm">{category.name}</span>
									<div class="flex items-center gap-2">
										<span class="text-sm text-muted-foreground">
											{category.count} items
										</span>
										<Badge variant="outline" class="text-xs">
											{category.percentage.toFixed(1)}%
										</Badge>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/each}
		</div>
	</Card>
</div>

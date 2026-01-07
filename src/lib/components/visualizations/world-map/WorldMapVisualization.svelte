<script lang="ts">
	import Map from './Map.svelte';
	import ViewModeToggle from './ViewModeToggle.svelte';
	import MapFilters from './MapFilters.svelte';
	import { mapDataStore } from '$lib/stores/mapDataStore.svelte.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import * as Card from '$lib/components/ui/card/index.js';

	// Selected location display
	const selectedLocation = $derived(mapDataStore.selectedLocation);
	const hasFiltersAvailable = $derived(
		mapDataStore.availableSourceCountries.length > 0 || mapDataStore.yearRange !== null
	);
</script>

<div class="flex h-full flex-col overflow-hidden">
	<!-- Main Map Area -->
	<div class="relative z-0 flex-1">
		<Card.Root class="h-full rounded-none border-0">
			<Card.Header class="pb-2">
				<div class="flex flex-col gap-3">
					<div class="flex items-start justify-between">
						<div class="flex-1">
							<Card.Title>{t('worldmap.title')}</Card.Title>
							<p class="text-sm text-muted-foreground">
								{t('worldmap.description')}
							</p>
						</div>
						<div class="ml-4">
							<ViewModeToggle />
						</div>
					</div>

					<!-- Filters Row -->
					{#if hasFiltersAvailable}
						<MapFilters />
					{/if}
				</div>
			</Card.Header>
			<Card.Content class="h-full p-0">
				<Map />
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Selected Location Details -->
	{#if selectedLocation}
		<div class="border-t border-border bg-background p-4">
			<div class="rounded-lg border border-border bg-card p-4 shadow-sm">
				<h3 class="mb-2 text-lg font-semibold text-foreground">{selectedLocation.name}</h3>
				<div class="space-y-1 text-sm text-muted-foreground">
					<p><strong>{t('table.countries')}:</strong> {selectedLocation.country}</p>
					<p>
						<strong>{t('worldmap.article_count')}:</strong>
						{selectedLocation.articleCount === 1
							? t('worldmap.article')
							: t('worldmap.articles', [selectedLocation.articleCount.toLocaleString()])}
					</p>
				</div>
			</div>
		</div>
	{/if}
</div>

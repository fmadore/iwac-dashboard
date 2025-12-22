<script lang="ts">
	import Map from '$lib/components/world-map/Map.svelte';
	import ViewModeToggle from '$lib/components/world-map/ViewModeToggle.svelte';
	import { mapDataStore } from '$lib/stores/mapDataStore.svelte.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import * as Card from '$lib/components/ui/card/index.js';

	// Selected location display
	const selectedLocation = $derived(mapDataStore.selectedLocation);
</script>

<div class="flex h-full flex-col overflow-hidden">
	<!-- Main Map Area -->
	<div class="flex-1 relative z-0">
		<Card.Root class="h-full border-0 rounded-none">
			<Card.Header class="pb-2">
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
			</Card.Header>
			<Card.Content class="h-full p-0">
				<Map />
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Selected Location Details -->
	{#if selectedLocation}
		<div class="border-t border-border p-4 bg-background">
			<div class="bg-card rounded-lg p-4 shadow-sm border border-border">
				<h3 class="font-semibold text-lg mb-2 text-foreground">{selectedLocation.name}</h3>
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

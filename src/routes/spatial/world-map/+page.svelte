<script lang="ts">
	import WorldMapVisualization from '$lib/components/world-map/WorldMapVisualization.svelte';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { mapDataStore } from '$lib/stores/mapDataStore.svelte.js';
	import StatsCard from '$lib/components/stats-card.svelte';
	import { MapPin, FileText, Globe } from '@lucide/svelte';

	// Reactive metadata
	const metadata = $derived(mapDataStore.metadata);
</script>

<svelte:head>
	<title>{t('worldmap.title')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto py-6 space-y-6">
	<!-- Page Header -->
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight text-foreground">{t('worldmap.title')}</h1>
		<p class="text-muted-foreground">{t('worldmap.description')}</p>
	</div>

	<!-- Stats Cards -->
	{#if metadata}
		<div class="grid gap-4 md:grid-cols-3">
			<StatsCard
				title={t('worldmap.total_locations')}
				value={metadata.totalLocations.toLocaleString()}
				icon={MapPin}
			/>
			<StatsCard
				title={t('worldmap.total_articles')}
				value={metadata.totalArticles.toLocaleString()}
				icon={FileText}
			/>
			<StatsCard
				title={t('worldmap.countries_covered')}
				value={metadata.countriesWithData.length.toLocaleString()}
				icon={Globe}
			/>
		</div>
	{/if}

	<!-- Map Visualization -->
	<div class="min-h-[600px]">
		<WorldMapVisualization />
	</div>
</div>

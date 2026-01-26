<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { onMount } from 'svelte';
	import { StatsCard } from '$lib/components/dashboard/index.js';
	import { MapLocationPopover } from '$lib/components/visualizations/map/index.js';
	import { BaseMap, CircleLayer, type CircleDataPoint } from '$lib/components/visualizations/maplibre/index.js';
	import { base } from '$app/paths';
	import type { MapLocation, PopoverPosition } from '$lib/types/map-location.js';

	// Types
	interface Source {
		name: string;
		count: number;
		lat?: number;
		lng?: number;
		id?: number | string;
		byType: Record<string, number>;
		countries: string[];
	}

	interface SourcesData {
		sources: Source[];
		metadata: {
			totalSources: number;
			sourcesWithCoordinates: number;
			sourcesWithoutCoordinates: number;
			totalItems: number;
			byType: Record<string, number>;
			countries: string[];
			generatedAt: string;
			dataSource: string;
		};
	}

	// State
	let data = $state<SourcesData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Popover state
	let hoveredLocation = $state<MapLocation | null>(null);
	let popoverPosition = $state<PopoverPosition | null>(null);

	// Derived
	const sourcesWithCoords = $derived(
		data?.sources.filter((s) => s.lat !== undefined && s.lng !== undefined) ?? []
	);
	const metadata = $derived(data?.metadata);

	// Transform sources to CircleDataPoints for MapLibre
	const circleData = $derived<CircleDataPoint[]>(
		sourcesWithCoords.map((source) => ({
			id: source.id ?? source.name,
			lat: source.lat!,
			lng: source.lng!,
			value: source.count,
			label: source.name,
			// Store additional data for popover
			countries: source.countries,
			byType: source.byType
		}))
	);

	// Load data
	onMount(async () => {
		try {
			const response = await fetch(`${base}/data/sources.json`);
			if (!response.ok) {
				throw new Error(`Failed to load sources data: ${response.status}`);
			}
			data = await response.json();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	});

	// Helper function to get the source URL based on current locale
	function getSourceUrl(id: number | string): string {
		const baseUrl =
			languageStore.current === 'fr'
				? 'https://islam.zmo.de/s/afrique_ouest/item/'
				: 'https://islam.zmo.de/s/westafrica/item/';
		return baseUrl + id;
	}

	// Handle hover from CircleLayer
	function handleHover(item: CircleDataPoint | null, position: PopoverPosition | null) {
		if (item) {
			// Find the original source to get full data
			const source = sourcesWithCoords.find((s) => (s.id ?? s.name) === item.id);
			if (source) {
				hoveredLocation = {
					name: source.name,
					lat: source.lat!,
					lng: source.lng!,
					count: source.count,
					country: source.countries.length > 0 ? source.countries[0] : undefined,
					externalUrl: source.id ? getSourceUrl(source.id) : undefined,
					items: []
				};
				popoverPosition = position;
			}
		} else {
			hoveredLocation = null;
			popoverPosition = null;
		}
	}
</script>

<svelte:head>
	<title>{t('sources.title')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 py-6">
	<!-- Page Header -->
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight text-foreground">{t('sources.title')}</h1>
		<p class="text-muted-foreground">{t('sources.description')}</p>
	</div>

	{#if loading}
		<div class="flex min-h-100 items-center justify-center">
			<p class="text-muted-foreground">{t('common.loading')}</p>
		</div>
	{:else if error}
		<div class="flex min-h-100 items-center justify-center">
			<p class="text-destructive">{error}</p>
		</div>
	{:else if metadata}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-4">
			<StatsCard
				title={t('sources.total_sources')}
				value={metadata.totalSources.toLocaleString()}
			/>
			<StatsCard
				title={t('sources.items_with_sources')}
				value={metadata.totalItems.toLocaleString()}
			/>
			<StatsCard
				title={t('sources.sources_with_coordinates')}
				value={metadata.sourcesWithCoordinates.toLocaleString()}
			/>
			<StatsCard title={t('stats.countries')} value={metadata.countries.length.toLocaleString()} />
		</div>

		<!-- Map Container -->
		<div class="rounded-lg border bg-card">
			<div class="border-b p-4">
				<h2 class="text-lg font-semibold">{t('sources.map_title')}</h2>
				<p class="text-sm text-muted-foreground">{t('sources.map_description')}</p>
			</div>
			<div class="relative" style="z-index: 0;">
				<BaseMap height="500px" center={[0, 10]} zoom={4}>
					{#if circleData.length > 0}
						<CircleLayer
							data={circleData}
							radiusRange={[8, 28]}
							onHover={handleHover}
						/>
					{/if}
				</BaseMap>
				<!-- Hover popover -->
				<MapLocationPopover
					location={hoveredLocation}
					position={popoverPosition}
					itemLabel="articles"
				/>
			</div>
		</div>

		<!-- Sources Table -->
		<div class="rounded-lg border bg-card">
			<div class="border-b p-4">
				<h2 class="text-lg font-semibold">{t('sources.top_sources')}</h2>
			</div>
			<div class="overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/50">
							<th class="p-3 text-left font-medium">{t('table.title')}</th>
							<th class="p-3 text-right font-medium">{t('sources.items')}</th>
							<th class="p-3 text-left font-medium">{t('table.countries')}</th>
							<th class="p-3 text-center font-medium">{t('sources.has_coordinates')}</th>
						</tr>
					</thead>
					<tbody>
						{#each data?.sources.slice(0, 20) ?? [] as source}
							<tr class="border-b hover:bg-muted/30">
								<td class="p-3">
									{#if source.id}
										<a
											href={getSourceUrl(source.id)}
											target="_blank"
											rel="noopener noreferrer"
											class="text-primary hover:underline">{source.name}</a
										>
									{:else}
										{source.name}
									{/if}
								</td>
								<td class="p-3 text-right font-mono">{source.count.toLocaleString()}</td>
								<td class="p-3 text-sm text-muted-foreground">
									{source.countries.slice(0, 3).join(', ')}
									{#if source.countries.length > 3}
										<span class="text-xs"> +{source.countries.length - 3}</span>
									{/if}
								</td>
								<td class="p-3 text-center">
									{#if source.lat !== undefined}
										<span class="polarity-positive">✓</span>
									{:else}
										<span class="text-muted-foreground">—</span>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>

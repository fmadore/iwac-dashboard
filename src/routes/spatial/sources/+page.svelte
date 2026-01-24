<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { onMount } from 'svelte';
	import { StatsCard } from '$lib/components/dashboard/index.js';
	import { MapLocationPopover } from '$lib/components/visualizations/map/index.js';
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
	let map = $state<any>(null);
	let mapContainer = $state<HTMLDivElement | null>(null);
	let L = $state<any>(null);

	// Popover state
	let hoveredLocation = $state<MapLocation | null>(null);
	let popoverPosition = $state<PopoverPosition | null>(null);

	// Transform Source to MapLocation
	function toMapLocation(source: Source): MapLocation {
		return {
			name: source.name,
			lat: source.lat!,
			lng: source.lng!,
			count: source.count,
			country: source.countries.length > 0 ? source.countries[0] : undefined,
			externalUrl: source.id ? getSourceUrl(source.id) : undefined,
			items: []
		};
	}

	// Derived
	const sourcesWithCoords = $derived(
		data?.sources.filter((s) => s.lat !== undefined && s.lng !== undefined) ?? []
	);
	const metadata = $derived(data?.metadata);

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

	// Initialize map when data and container are ready
	$effect(() => {
		if (!loading && data && mapContainer && !map && typeof window !== 'undefined') {
			initMap();
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

	// Helper function to resolve CSS variable color values for Leaflet
	function getCssColor(varName: string): string {
		if (typeof document === 'undefined') return '#000';
		return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || '#000';
	}

	async function initMap() {
		if (!mapContainer) return;

		// Dynamically import Leaflet
		const leaflet = await import('leaflet');
		L = leaflet.default;

		// Import Leaflet CSS
		await import('leaflet/dist/leaflet.css');

		// Define world bounds to prevent panning outside the world
		const southWest = L.latLng(-85, -180);
		const northEast = L.latLng(85, 180);
		const worldBounds = L.latLngBounds(southWest, northEast);

		// Create map centered on West Africa with bounds restrictions
		map = L.map(mapContainer, {
			maxBounds: worldBounds,
			maxBoundsViscosity: 1.0,
			minZoom: 2
		}).setView([10.0, 0.0], 4);

		// Add tile layer
		L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '© OpenStreetMap contributors',
			noWrap: true
		}).addTo(map);

		// Add markers for sources with coordinates
		addMarkers();
	}

	function addMarkers() {
		if (!map || !L || !sourcesWithCoords.length) return;

		// Calculate size range
		const counts = sourcesWithCoords.map((s) => s.count);
		const maxCount = Math.max(...counts);
		const minCount = Math.min(...counts);

		sourcesWithCoords.forEach((source) => {
			if (source.lat === undefined || source.lng === undefined) return;

			// Calculate marker size based on count
			const sizeScale =
				minCount === maxCount ? 1 : (source.count - minCount) / (maxCount - minCount);
			const radius = 8 + sizeScale * 20;

			// Create circle marker with resolved CSS colors
			const primaryColor = getCssColor('--primary');
			const primaryForeground = getCssColor('--primary-foreground');
			const marker = L.circleMarker([source.lat, source.lng], {
				radius,
				fillColor: primaryColor,
				color: primaryForeground,
				weight: 2,
				opacity: 0.9,
				fillOpacity: 0.6
			}).addTo(map);

			// Hover handlers for popover
			marker.on('mouseover', (e: any) => {
				marker.setStyle({ fillOpacity: 0.85, weight: 3 });

				// Calculate position relative to map container
				if (mapContainer && map) {
					const containerPoint = map.latLngToContainerPoint(e.latlng);
					const placement = containerPoint.y < 150 ? 'bottom' : 'top';

					popoverPosition = {
						x: containerPoint.x,
						y: placement === 'top' ? containerPoint.y - 10 : containerPoint.y + 10,
						placement
					};
					hoveredLocation = toMapLocation(source);
				}
			});

			marker.on('mouseout', () => {
				marker.setStyle({ fillOpacity: 0.6, weight: 2 });
				hoveredLocation = null;
				popoverPosition = null;
			});
		});
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
			<div class="relative h-125 w-full" style="z-index: 0;">
				<div bind:this={mapContainer} class="h-full w-full"></div>
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

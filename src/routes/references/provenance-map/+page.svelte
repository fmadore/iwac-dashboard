<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { StatsCard } from '$lib/components/dashboard/index.js';
	import { MapLocationPopover, MapLocationSheet } from '$lib/components/visualizations/map/index.js';
	import { ExternalLink, MapPin } from '@lucide/svelte';
	import { scaleSqrt } from 'd3-scale';
	import type { ProvenanceMapData } from './+page.js';
	import type { MapLocation, PopoverPosition } from '$lib/types/map-location.js';

	// Get preloaded data from +page.ts
	let { data: pageData } = $props<{
		data: {
			mapData: ProvenanceMapData | null;
			error: string | null;
		};
	}>();

	const mapData = $derived(pageData.mapData);
	const error = $derived(pageData.error);

	// Map state
	let mapElement: HTMLDivElement | null = $state(null);
	let map: L.Map | null = $state(null);
	let L: typeof import('leaflet') | null = null;
	let markersLayer: L.LayerGroup | null = null;
	let mapLoading = $state(true);

	// Popover and sheet state
	let hoveredLocation = $state<MapLocation | null>(null);
	let selectedLocation = $state<MapLocation | null>(null);
	let popoverPosition = $state<PopoverPosition | null>(null);

	// Build islam.zmo.de URL based on current language
	function getItemUrl(oId: string): string {
		const lang = languageStore.current;
		const path = lang === 'fr' ? 'afrique_ouest' : 'westafrica';
		return `https://islam.zmo.de/s/${path}/item/${oId}`;
	}

	// Transform ProvenanceLocation to MapLocation
	function toMapLocation(location: ProvenanceMapData['locations'][0]): MapLocation {
		return {
			name: location.name,
			lat: location.lat,
			lng: location.lng,
			count: location.count,
			yearRange: location.earliestYear && location.latestYear
				? { start: location.earliestYear, end: location.latestYear }
				: undefined,
			externalUrl: location.o_id ? getItemUrl(location.o_id) : undefined,
			items: location.publications.map(pub => ({
				id: pub.pub_id,
				title: pub.title,
				type: pub.type,
				year: pub.year,
				authors: pub.authors
			}))
		};
	}

	// Tile layer configuration
	const tileLayerOptions = {
		light: {
			url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
			attribution:
				'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
		},
		dark: {
			url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
			attribution:
				'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
		}
	};

	function isDarkActive(): boolean {
		if (!browser) return false;
		return document.documentElement.classList.contains('dark');
	}

	async function initMap() {
		if (!browser || !mapElement || !mapData) return;

		try {
			L = await import('leaflet');
			await import('leaflet/dist/leaflet.css');

			// Clean up existing map
			if (map) {
				map.remove();
				map = null;
			}

			// Create map
			const isDark = isDarkActive();
			const tileOptions = isDark ? tileLayerOptions.dark : tileLayerOptions.light;

			map = L.map(mapElement, {
				zoomControl: true,
				scrollWheelZoom: true
			});

			// Add tile layer
			L.tileLayer(tileOptions.url, {
				attribution: tileOptions.attribution,
				maxZoom: 18
			}).addTo(map);

			// Set initial view
			if (mapData.bounds) {
				const bounds = L.latLngBounds(
					[mapData.bounds.south, mapData.bounds.west],
					[mapData.bounds.north, mapData.bounds.east]
				);
				map.fitBounds(bounds, { padding: [50, 50] });
			} else {
				// Default to West Africa
				map.setView([12, 0], 5);
			}

			// Create markers layer
			markersLayer = L.layerGroup().addTo(map);

			// Add markers
			addMarkers();

			mapLoading = false;
		} catch (e) {
			console.error('Failed to initialize map:', e);
			mapLoading = false;
		}
	}

	function addMarkers() {
		if (!L || !map || !markersLayer || !mapData || !mapElement) return;

		markersLayer.clearLayers();

		// Create size scale
		const sizeScale = scaleSqrt()
			.domain([1, mapData.meta.maxCount])
			.range([8, 40]);

		const isDark = isDarkActive();
		const fillColor = isDark ? '#f97316' : '#ea580c';
		const strokeColor = isDark ? '#fed7aa' : '#9a3412';

		for (const location of mapData.locations) {
			const radius = sizeScale(location.count);

			const marker = L.circleMarker([location.lat, location.lng], {
				radius: radius,
				fillColor: fillColor,
				color: strokeColor,
				weight: 2,
				opacity: 0.9,
				fillOpacity: 0.6
			});

			// Hover handlers
			marker.on('mouseover', (e: L.LeafletMouseEvent) => {
				marker.setStyle({ fillOpacity: 0.85, weight: 3 });

				// Calculate position relative to map container
				if (mapElement) {
					const containerPoint = map!.latLngToContainerPoint(e.latlng);
					const mapRect = mapElement.getBoundingClientRect();

					// Determine if popover should appear above or below
					const placement = containerPoint.y < 150 ? 'bottom' : 'top';

					popoverPosition = {
						x: containerPoint.x,
						y: placement === 'top' ? containerPoint.y - 10 : containerPoint.y + 10,
						placement
					};
					hoveredLocation = toMapLocation(location);
				}
			});

			marker.on('mouseout', () => {
				marker.setStyle({ fillOpacity: 0.6, weight: 2 });
				hoveredLocation = null;
				popoverPosition = null;
			});

			// Click handler opens sheet
			marker.on('click', () => {
				selectedLocation = toMapLocation(location);
				hoveredLocation = null;
				popoverPosition = null;
			});

			marker.addTo(markersLayer);
		}
	}

	function handleSheetClose() {
		selectedLocation = null;
	}

	// Watch for theme changes
	$effect(() => {
		if (browser && map && L && mapData) {
			const isDark = isDarkActive();
			const tileOptions = isDark ? tileLayerOptions.dark : tileLayerOptions.light;

			// Update tile layer
			map.eachLayer((layer: L.Layer) => {
				if ((layer as L.TileLayer).setUrl) {
					(layer as L.TileLayer).setUrl(tileOptions.url);
				}
			});

			// Refresh markers with new colors
			addMarkers();
		}
	});

	onMount(() => {
		if (mapData) {
			initMap();
		}

		// Theme observer
		const observer = new MutationObserver(() => {
			if (map && L) {
				const isDark = isDarkActive();
				const tileOptions = isDark ? tileLayerOptions.dark : tileLayerOptions.light;

				map.eachLayer((layer: L.Layer) => {
					if ((layer as L.TileLayer).setUrl) {
						(layer as L.TileLayer).setUrl(tileOptions.url);
					}
				});

				addMarkers();
			}
		});

		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['class']
		});

		return () => {
			observer.disconnect();
			if (map) {
				map.remove();
			}
		};
	});
</script>

<svelte:head>
	<title>{t('provenance.title')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 py-6">
	<!-- Page Header -->
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight text-foreground">{t('provenance.title')}</h1>
		<p class="text-muted-foreground">{t('provenance.description')}</p>
	</div>

	{#if !mapData && !error}
		<div class="space-y-4">
			<div class="grid gap-4 md:grid-cols-3">
				{#each Array(3) as _, i (i)}
					<Skeleton class="h-24" />
				{/each}
			</div>
			<Skeleton class="h-[600px]" />
		</div>
	{:else if error}
		<Card.Root class="p-6">
			<div class="py-12 text-center">
				<h3 class="mb-2 text-xl font-semibold text-destructive">{t('common.error')}</h3>
				<p class="text-muted-foreground">{error}</p>
				<p class="mt-4 text-sm text-muted-foreground">
					{t('provenance.run_script_hint')}
				</p>
			</div>
		</Card.Root>
	{:else if mapData}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-3">
			<StatsCard title={t('provenance.total_locations')} value={mapData.meta.totalLocations} />
			<StatsCard
				title={t('provenance.total_publications')}
				value={mapData.meta.totalPublications}
			/>
			<StatsCard title={t('provenance.top_location')} value={mapData.locations[0]?.name || '—'} />
		</div>

		<!-- Map Card -->
		<Card.Root class="overflow-hidden">
			<Card.Header>
				<Card.Title class="flex items-center gap-2">
					<MapPin class="h-5 w-5" />
					{t('provenance.map_title')}
				</Card.Title>
				<Card.Description>{t('provenance.map_description')}</Card.Description>
			</Card.Header>
			<Card.Content class="p-0">
				<div class="relative h-[600px]" bind:this={mapElement}>
					{#if mapLoading}
						<div class="absolute inset-0 flex items-center justify-center bg-muted/50">
							<Skeleton class="h-full w-full" />
						</div>
					{/if}

					<!-- Hover popover -->
					<MapLocationPopover
						location={hoveredLocation}
						position={popoverPosition}
						itemLabel="publications"
					/>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Legend -->
		<Card.Root>
			<Card.Content class="py-4">
				<div class="flex flex-wrap items-center gap-6 text-sm">
					<div class="flex items-center gap-2">
						<div class="h-4 w-4 rounded-full bg-orange-500/60 border-2 border-orange-700"></div>
						<span class="text-muted-foreground">{t('provenance.legend_size')}</span>
					</div>
					<div class="flex items-center gap-4">
						<div class="flex items-center gap-1">
							<div class="h-3 w-3 rounded-full bg-orange-500/60 border border-orange-700"></div>
							<span class="text-xs text-muted-foreground">1</span>
						</div>
						<div class="flex items-center gap-1">
							<div class="h-6 w-6 rounded-full bg-orange-500/60 border-2 border-orange-700"></div>
							<span class="text-xs text-muted-foreground">{mapData.meta.maxCount}</span>
						</div>
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Top Locations Table -->
		<Card.Root>
			<Card.Header>
				<Card.Title>{t('provenance.top_locations')}</Card.Title>
				<Card.Description>{t('provenance.top_locations_description')}</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b">
								<th class="py-2 text-left font-medium">{t('provenance.location')}</th>
								<th class="py-2 text-right font-medium">{t('provenance.publications')}</th>
								<th class="py-2 text-left font-medium">{t('provenance.year_range')}</th>
								<th class="py-2 text-left font-medium">{t('provenance.top_type')}</th>
							</tr>
						</thead>
						<tbody>
							{#each mapData.locations.slice(0, 20) as location (location.name)}
								{@const topType = Object.entries(location.types).sort((a, b) => (b[1] as number) - (a[1] as number))[0]}
								<tr class="border-b border-border/50 hover:bg-muted/50">
									<td class="py-2">
										{#if location.o_id}
											<a
												href={getItemUrl(location.o_id)}
												target="_blank"
												rel="noopener noreferrer"
												class="inline-flex items-center gap-1 text-primary hover:underline"
											>
												{location.name}
												<ExternalLink class="h-3 w-3" />
											</a>
										{:else}
											{location.name}
										{/if}
									</td>
									<td class="py-2 text-right font-medium">{location.count}</td>
									<td class="py-2 text-muted-foreground">
										{#if location.earliestYear && location.latestYear}
											{location.earliestYear}–{location.latestYear}
										{:else}
											—
										{/if}
									</td>
									<td class="py-2">
										{#if topType}
											<Badge variant="outline" class="text-xs">
												{t(`type.${topType[0]}`, [topType[0]])} ({topType[1]})
											</Badge>
										{:else}
											—
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

<!-- Sheet for location details (at page level to avoid clipping) -->
<MapLocationSheet
	location={selectedLocation}
	onClose={handleSheetClose}
	itemLabel="publications"
/>

<style>
	:global(.leaflet-popup-content-wrapper) {
		background: var(--card);
		color: var(--foreground);
		border-radius: 0.5rem;
		box-shadow: 0 4px 12px color-mix(in oklch, var(--foreground) 18%, transparent);
	}

	:global(.leaflet-popup-tip) {
		background: var(--card);
	}

	:global(.leaflet-control-zoom) {
		border: 1px solid var(--border) !important;
		border-radius: 8px !important;
		overflow: hidden;
	}

	:global(.leaflet-control-zoom a) {
		background: var(--card) !important;
		color: var(--foreground) !important;
		border-color: var(--border) !important;
	}

	:global(.leaflet-control-zoom a:hover) {
		background: var(--accent) !important;
	}
</style>

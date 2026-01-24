<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { entitySpatialStore } from '$lib/stores/entitySpatialStore.svelte.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { MapLocationPopover } from '$lib/components/visualizations/map/index.js';
	import type { EntityLocation } from '$lib/types/entity-spatial.js';
	import type { MapLocation, PopoverPosition } from '$lib/types/map-location.js';
	import { scaleSqrt, scaleLinear } from 'd3-scale';

	interface Props {
		height?: string;
	}

	let { height = '500px' }: Props = $props();

	// Local state
	let mapElement: HTMLDivElement | undefined = $state();
	let map: L.Map | null = $state(null);
	let L: typeof import('leaflet') | null = null;
	let markersLayer: L.LayerGroup | null = null;
	let tileLayer: L.TileLayer | null = null;
	let worldBounds: L.LatLngBounds | null = null;
	let themeObserver: MutationObserver | null = null;
	let mapLoading = $state(true);

	// Derived state from store
	const locations = $derived(entitySpatialStore.currentLocations);
	const selectedLocation = $derived(entitySpatialStore.selectedLocation);
	const currentEntity = $derived(entitySpatialStore.currentEntity);

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	// Popover state
	let hoveredLocation = $state<MapLocation | null>(null);
	let popoverPosition = $state<PopoverPosition | null>(null);

	// Transform EntityLocation to MapLocation
	function toMapLocation(location: EntityLocation): MapLocation {
		return {
			name: location.name,
			lat: location.lat,
			lng: location.lng,
			count: location.articleCount,
			country: location.country,
			items: [] // Items are loaded separately via entitySpatialStore
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

	function getCssVar(varName: string, fallback: string): string {
		if (!browser) return fallback;
		const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
		return value || fallback;
	}

	function isDarkActive(): boolean {
		if (!browser) return false;
		return document.documentElement.classList.contains('dark');
	}

	function updateTileLayer() {
		if (!L || !map) return;

		const option = isDarkActive() ? tileLayerOptions.dark : tileLayerOptions.light;
		if (!tileLayer) {
			tileLayer = L.tileLayer(option.url, {
				attribution: option.attribution,
				maxZoom: 19,
				noWrap: true,
				bounds: worldBounds ?? undefined
			}).addTo(map);
			return;
		}

		tileLayer.setUrl(option.url);
	}

	onMount(() => {
		if (!browser) return;

		const initMap = async () => {
			try {
				// Dynamically import Leaflet
				const leaflet = await import('leaflet');
				L = leaflet.default || leaflet;

				// Create and inject Leaflet CSS
				if (!document.getElementById('leaflet-css')) {
					const link = document.createElement('link');
					link.id = 'leaflet-css';
					link.rel = 'stylesheet';
					link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
					link.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
					link.crossOrigin = '';
					document.head.appendChild(link);
					await new Promise((resolve) => setTimeout(resolve, 100));
				}

				// Initialize map
				worldBounds = L.latLngBounds(L.latLng(-85, -180), L.latLng(85, 180));

				map = L.map(mapElement!, {
					center: [12, 0], // West Africa center
					zoom: 4,
					minZoom: 2,
					maxZoom: 12,
					zoomControl: true,
					maxBounds: worldBounds,
					maxBoundsViscosity: 1.0,
					worldCopyJump: false
				});

				updateTileLayer();

				// React to theme changes
				themeObserver = new MutationObserver(() => {
					updateTileLayer();
				});
				themeObserver.observe(document.documentElement, {
					attributes: true,
					attributeFilter: ['class']
				});

				// Create markers layer group
				markersLayer = L.layerGroup().addTo(map);

				mapLoading = false;
			} catch (error) {
				console.error('Failed to initialize map:', error);
				mapLoading = false;
			}
		};

		initMap();

		return () => {
			if (themeObserver) {
				themeObserver.disconnect();
				themeObserver = null;
			}
			if (map) {
				map.remove();
				map = null;
			}
		};
	});

	// Update markers when locations change
	$effect(() => {
		if (!map || !L || !markersLayer) return;

		// Access lang for reactivity
		void lang;

		// Clear existing markers
		markersLayer.clearLayers();

		if (locations.length === 0) return;

		// Create scales
		const maxCount = Math.max(...locations.map((l) => l.articleCount));
		const minCount = Math.min(...locations.map((l) => l.articleCount));

		const radiusScale = scaleSqrt()
			.domain([minCount, maxCount])
			.range([8, 35]);

		const lowColor = getCssVar('--chart-2', 'oklch(0.55 0.18 250)');
		const highColor = getCssVar('--chart-6', 'oklch(0.6 0.18 15)');

		const colorScale = scaleLinear<string>().domain([minCount, maxCount]).range([lowColor, highColor]);

		const strokeColor = getCssVar('--background', '#ffffff');

		// Add circle markers for each location
		for (const location of locations) {
			const radius = radiusScale(location.articleCount);
			const color = colorScale(location.articleCount);
			const isSelected = selectedLocation?.name === location.name;

			const marker = L.circleMarker([location.lat, location.lng], {
				radius: isSelected ? radius * 1.2 : radius,
				fillColor: color,
				color: isSelected ? getCssVar('--primary', '#3b82f6') : strokeColor,
				weight: isSelected ? 3 : 2,
				opacity: 1,
				fillOpacity: isSelected ? 0.9 : 0.7
			});

			const articleText =
				location.articleCount === 1
					? t('worldmap.article')
					: t('worldmap.articles', [location.articleCount.toLocaleString()]);

			// Hover handlers for popover
			marker.on('mouseover', (e: L.LeafletMouseEvent) => {
				marker.setStyle({ fillOpacity: 0.9, weight: 3 });

				// Calculate position relative to map container
				if (mapElement && map) {
					const containerPoint = map.latLngToContainerPoint(e.latlng);
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
				if (selectedLocation?.name !== location.name) {
					marker.setStyle({ fillOpacity: 0.7, weight: 2 });
				}
				hoveredLocation = null;
				popoverPosition = null;
			});

			marker.on('click', () => {
				entitySpatialStore.setSelectedLocation(location);
				hoveredLocation = null;
				popoverPosition = null;
			});

			markersLayer!.addLayer(marker);
		}

		// Fit bounds to show all markers if we have locations
		if (locations.length > 0) {
			const bounds = L.latLngBounds(locations.map((l) => [l.lat, l.lng] as [number, number]));
			map.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });
		}
	});
</script>

<div class="map-wrapper relative">
	<div
		class="map-container relative z-0"
		bind:this={mapElement}
		style="height: {height};"
		data-testid="entity-map-container"
	>
		<!-- Hover popover -->
		<MapLocationPopover
			location={hoveredLocation}
			position={popoverPosition}
			itemLabel="articles"
		/>
	</div>

	{#if mapLoading}
		<div class="absolute inset-0 flex items-center justify-center bg-background/80">
			<div class="text-center">
				<Skeleton class="mx-auto mb-2 h-8 w-32" />
				<p class="text-sm text-muted-foreground">{t('common.loading')}</p>
			</div>
		</div>
	{/if}

	{#if !mapLoading && locations.length === 0 && currentEntity}
		<div class="absolute inset-0 flex items-center justify-center bg-background/50">
			<p class="text-muted-foreground">{t('entity_spatial.no_locations')}</p>
		</div>
	{/if}

	{#if !mapLoading && !currentEntity}
		<div class="absolute inset-0 flex items-center justify-center bg-background/50">
			<p class="text-muted-foreground">{t('entity_spatial.no_entity_selected')}</p>
		</div>
	{/if}
</div>

<style>
	.map-wrapper {
		width: 100%;
	}

	.map-container {
		width: 100%;
		background: linear-gradient(135deg, var(--muted) 0%, var(--background) 100%);
		border-radius: 12px;
		overflow: hidden;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
		border: 1px solid var(--border);
	}

	:global(.leaflet-container) {
		font-family: inherit;
		border-radius: 12px;
	}

	:global(.leaflet-popup-content-wrapper) {
		background: var(--card);
		color: var(--foreground);
		border-radius: 8px;
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

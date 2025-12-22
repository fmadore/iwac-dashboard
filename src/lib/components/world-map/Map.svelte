<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { base } from '$app/paths';
	import { mapDataStore } from '$lib/stores/mapDataStore.svelte.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import ChoroplethLayer from './ChoroplethLayer.svelte';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import type { GeoJsonData, LocationData } from '$lib/types/worldmap.js';
	import { scaleLinear, scaleSqrt } from 'd3-scale';

	// Props
	let { height = '600px' }: { height?: string } = $props();

	// Local state
	let mapElement: HTMLDivElement;
	let map: L.Map | null = $state(null);
	let L: typeof import('leaflet') | null = null;
	let worldGeo: GeoJsonData | null = $state(null);
	let markersLayer: L.LayerGroup | null = null;
	let mapLoading = $state(true);
	let dataLoading = $state(true);

	// Legend state
	let showLegend = $state(true);
	let legendItems = $state<{ color: string; label: string }[]>([]);

	// Derived state
	const viewMode = $derived(mapDataStore.viewMode);
	const locations = $derived(mapDataStore.locations);
	const countryCounts = $derived(mapDataStore.countryCounts);

	// Tile layer configuration
	const tileLayerOptions = {
		light: {
			url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
			attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
		}
	};

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
					// Wait a bit for CSS to load
					await new Promise(resolve => setTimeout(resolve, 100));
				}

				// Initialize map
				map = L.map(mapElement, {
					center: [8, 2], // West Africa center
					zoom: 4,
					minZoom: 2,
					maxZoom: 12,
					zoomControl: true
				});

				// Add tile layer
				L.tileLayer(tileLayerOptions.light.url, {
					attribution: tileLayerOptions.light.attribution,
					maxZoom: 19
				}).addTo(map);

				// Create markers layer group
				markersLayer = L.layerGroup().addTo(map);

				mapLoading = false;

				// Load data
				await loadMapData();
			} catch (error) {
				console.error('Failed to initialize map:', error);
				mapDataStore.setError(t('worldmap.error'));
				mapLoading = false;
			}
		};

		initMap();

		return () => {
			if (map) {
				map.remove();
				map = null;
			}
		};
	});

	async function loadMapData() {
		try {
			dataLoading = true;

			// Load world GeoJSON for choropleth
			const geoResponse = await fetch(`${base}/data/maps/world_countries.geojson`);
			if (geoResponse.ok) {
				worldGeo = await geoResponse.json();
			}

			// Load pre-computed world map data
			const dataResponse = await fetch(`${base}/data/world-map.json`);
			if (dataResponse.ok) {
				const mapData = await dataResponse.json();
				mapDataStore.setData(mapData);
			} else {
				// If no pre-computed data, try loading from treemap
				console.warn('No world-map.json found, using treemap data as fallback');
				await loadFallbackData();
			}

			dataLoading = false;
		} catch (error) {
			console.error('Failed to load map data:', error);
			mapDataStore.setError(t('worldmap.error'));
			dataLoading = false;
		}
	}

	async function loadFallbackData() {
		// Fallback: use treemap data to build country counts
		try {
			const response = await fetch(`${base}/data/treemap-countries.json`);
			if (response.ok) {
				const treemapData = await response.json();
				const countryCounts: Record<string, number> = {};
				
				if (treemapData.children) {
					for (const country of treemapData.children) {
						if (country.name && country.value) {
							countryCounts[country.name] = country.value;
						}
					}
				}

				mapDataStore.setData({
					locations: [],
					countryCounts,
					metadata: {
						totalLocations: 0,
						totalArticles: Object.values(countryCounts).reduce((a, b) => a + b, 0),
						countriesWithData: Object.keys(countryCounts),
						updatedAt: new Date().toISOString()
					}
				});
			}
		} catch (error) {
			console.error('Fallback data load failed:', error);
		}
	}

	// Update bubbles when view mode or data changes
	$effect(() => {
		if (!map || !L || !markersLayer) return;

		// Clear existing markers
		markersLayer.clearLayers();

		if (viewMode === 'bubbles' && locations.length > 0) {
			renderBubbles();
		}
	});

	function renderBubbles() {
		if (!L || !map || !markersLayer || locations.length === 0) return;

		const maxCount = Math.max(...locations.map(l => l.articleCount));
		const minCount = Math.min(...locations.map(l => l.articleCount));

		// Create scales
		const radiusScale = scaleSqrt()
			.domain([minCount, maxCount])
			.range([5, 40]);

		const colorScale = scaleLinear<string>()
			.domain([minCount, maxCount])
			.range(['#60a5fa', '#dc2626']); // Blue to red

		// Build legend
		const legendBreaks = [minCount, Math.round((minCount + maxCount) / 2), maxCount];
		legendItems = legendBreaks.map(value => ({
			color: colorScale(value),
			label: value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value.toString()
		}));

		// Add circle markers for each location
		for (const location of locations) {
			const radius = radiusScale(location.articleCount);
			const color = colorScale(location.articleCount);

			const marker = L.circleMarker([location.lat, location.lng], {
				radius,
				fillColor: color,
				color: 'white',
				weight: 2,
				opacity: 1,
				fillOpacity: 0.7
			});

			const articleText = location.articleCount === 1 
				? t('worldmap.article') 
				: t('worldmap.articles', [location.articleCount.toLocaleString()]);

			marker.bindPopup(`
				<strong>${location.name}</strong><br>
				<span style="color: var(--muted-foreground)">${location.country}</span><br>
				${articleText}
			`);

			marker.on('mouseover', () => {
				marker.setStyle({ fillOpacity: 0.9, weight: 3 });
				marker.openPopup();
			});

			marker.on('mouseout', () => {
				marker.setStyle({ fillOpacity: 0.7, weight: 2 });
			});

			marker.on('click', () => {
				mapDataStore.setSelectedLocation(location);
			});

			markersLayer!.addLayer(marker);
		}
	}
</script>

<div class="map-wrapper relative">
	<div 
		class="map-container relative z-0" 
		bind:this={mapElement} 
		style="height: {height};" 
		data-testid="map-container"
	></div>

	{#if mapLoading}
		<div class="absolute inset-0 flex items-center justify-center bg-background/80">
			<div class="text-center">
				<Skeleton class="h-8 w-32 mx-auto mb-2" />
				<p class="text-sm text-muted-foreground">{t('worldmap.loading')}</p>
			</div>
		</div>
	{/if}

	{#if dataLoading && !mapLoading}
		<div class="absolute top-4 left-1/2 -translate-x-1/2 bg-card px-4 py-2 rounded-lg shadow-lg border border-border">
			<p class="text-sm text-muted-foreground">{t('common.loading')}</p>
		</div>
	{/if}

	<!-- Bubble Legend -->
	{#if showLegend && viewMode === 'bubbles' && legendItems.length > 0 && !mapLoading && !dataLoading}
		<div class="absolute bottom-4 left-4 bg-card p-3 rounded-lg shadow-lg border border-border">
			<div class="flex items-center justify-between mb-2">
				<span class="text-xs font-semibold text-foreground">{t('worldmap.article_count')}</span>
				<button 
					class="text-muted-foreground hover:text-foreground transition-colors"
					onclick={() => showLegend = false}
					aria-label="Close legend"
				>
					<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
			</div>
			<div class="flex items-center gap-4">
				{#each legendItems as item}
					<div class="flex items-center gap-1.5">
						<span 
							class="w-3 h-3 rounded-full" 
							style="background: {item.color}"
						></span>
						<span class="text-xs text-muted-foreground">{item.label}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Legend Toggle -->
	{#if !showLegend && viewMode === 'bubbles' && legendItems.length > 0 && !mapLoading && !dataLoading}
		<button
			class="absolute bottom-4 left-4 bg-card p-2 rounded-lg shadow-lg border border-border hover:bg-accent transition-colors"
			onclick={() => showLegend = true}
			aria-label="Show legend"
		>
			<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<line x1="8" y1="6" x2="21" y2="6"></line>
				<line x1="8" y1="12" x2="21" y2="12"></line>
				<line x1="8" y1="18" x2="21" y2="18"></line>
				<line x1="3" y1="6" x2="3.01" y2="6"></line>
				<line x1="3" y1="12" x2="3.01" y2="12"></line>
				<line x1="3" y1="18" x2="3.01" y2="18"></line>
			</svg>
		</button>
	{/if}
</div>

<!-- Choropleth Layer -->
{#if browser && map && worldGeo && viewMode === 'choropleth'}
	<ChoroplethLayer
		{map}
		geoJson={worldGeo}
		data={countryCounts}
		scaleMode="log"
	/>
{/if}

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

	:global(.leaflet-control-layers) {
		border-radius: 8px !important;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
		border: 1px solid var(--border) !important;
	}

	:global(.leaflet-popup-content-wrapper) {
		background: var(--card);
		color: var(--foreground);
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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

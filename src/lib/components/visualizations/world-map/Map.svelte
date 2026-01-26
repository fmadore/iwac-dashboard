<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { base } from '$app/paths';
	import { mapDataStore } from '$lib/stores/mapDataStore.svelte.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { MapLocationPopover } from '$lib/components/visualizations/map/index.js';
	import {
		BaseMap,
		CircleLayer,
		ChoroplethLayer,
		type CircleDataPoint,
		getCssVarAsHex
	} from '$lib/components/visualizations/maplibre/index.js';
	import type { GeoJsonData, LocationData } from '$lib/types/worldmap.js';
	import type { MapLocation, PopoverPosition } from '$lib/types/map-location.js';
	import { scaleLinear, scaleSqrt } from 'd3-scale';

	// Props
	let { height = '600px' }: { height?: string } = $props();

	// Local state
	let worldGeo: GeoJsonData | null = $state(null);
	let dataLoading = $state(true);
	let bubbleColorRange = $state<[string, string]>(['#3b82f6', '#ef4444']);
	// Sequential orange gradient (light to dark) for choropleth
	let choroplethColorRange = $state<string[]>([
		'#fff7ed', // orange-50
		'#ffedd5', // orange-100
		'#fed7aa', // orange-200
		'#fdba74', // orange-300
		'#fb923c', // orange-400
		'#f97316', // orange-500
		'#ea580c'  // orange-600
	]);

	// Legend state
	let showLegend = $state(true);
	let legendItems = $state<{ color: string; label: string }[]>([]);

	// Popover state
	let hoveredLocation = $state<MapLocation | null>(null);
	let popoverPosition = $state<PopoverPosition | null>(null);

	// Transform LocationData to MapLocation
	function toMapLocation(location: LocationData): MapLocation {
		return {
			name: location.name,
			lat: location.lat,
			lng: location.lng,
			count: location.articleCount,
			country: location.country,
			items: [] // World map locations don't have item details
		};
	}

	// Derived state - use filtered data when filters are active
	const viewMode = $derived(mapDataStore.viewMode);
	const locations = $derived(mapDataStore.filteredLocations);
	const countryCounts = $derived(mapDataStore.filteredCountryCounts);
	const selectedSourceCountry = $derived(mapDataStore.selectedSourceCountry);
	const selectedYearRange = $derived(mapDataStore.selectedYearRange);

	function syncThemeDerivedValues() {
		if (!browser) return;

		// Bubble colors: low -> high (hex for D3 compatibility)
		bubbleColorRange = [
			getCssVarAsHex('--chart-2', '#3b82f6'),
			getCssVarAsHex('--chart-6', '#ef4444')
		];

		// Sequential orange gradient for choropleth (consistent light to dark)
		choroplethColorRange = [
			'#fff7ed', // orange-50
			'#ffedd5', // orange-100
			'#fed7aa', // orange-200
			'#fdba74', // orange-300
			'#fb923c', // orange-400
			'#f97316', // orange-500
			'#ea580c'  // orange-600
		];
	}

	onMount(() => {
		if (!browser) return;

		syncThemeDerivedValues();
		loadMapData();
	});

	async function loadMapData() {
		try {
			dataLoading = true;

			// Load simplified world GeoJSON for choropleth (1MB vs 5MB original)
			const geoResponse = await fetch(`${base}/data/maps/world_countries_simple.geojson`);
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
					filterData: {
						sourceCountries: [],
						years: [],
						yearRange: { min: null, max: null },
						countsBySourceCountryYear: {},
						locationCountsByFilter: {}
					},
					metadata: {
						totalLocations: 0,
						totalArticles: Object.values(countryCounts).reduce((a, b) => a + b, 0),
						countriesWithData: Object.keys(countryCounts),
						sourceCountries: [],
						yearRange: { min: null, max: null },
						generatedAt: new Date().toISOString(),
						dataSource: 'fallback'
					}
				});
			}
		} catch (error) {
			console.error('Fallback data load failed:', error);
		}
	}

	// Transform locations to CircleDataPoints for MapLibre
	const circleData = $derived<CircleDataPoint[]>(
		locations.map((location) => ({
			id: location.name,
			lat: location.lat,
			lng: location.lng,
			value: location.articleCount,
			label: location.name,
			country: location.country
		}))
	);

	// Update legend when locations change
	$effect(() => {
		if (viewMode !== 'bubbles' || locations.length === 0) {
			legendItems = [];
			return;
		}

		const maxCount = Math.max(...locations.map((l) => l.articleCount));
		const minCount = Math.min(...locations.map((l) => l.articleCount));

		const colorScale = scaleLinear<string>()
			.domain([minCount, maxCount])
			.range([bubbleColorRange[0], bubbleColorRange[1]]);

		const legendBreaks = [minCount, Math.round((minCount + maxCount) / 2), maxCount];
		legendItems = legendBreaks.map((value) => ({
			color: colorScale(value),
			label: value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value.toString()
		}));
	});

	// Handle hover from CircleLayer
	function handleHover(item: CircleDataPoint | null, position: PopoverPosition | null) {
		if (item) {
			const location = locations.find((l) => l.name === item.id);
			if (location) {
				hoveredLocation = toMapLocation(location);
				popoverPosition = position;
			}
		} else {
			hoveredLocation = null;
			popoverPosition = null;
		}
	}

	// Handle click from CircleLayer
	function handleClick(item: CircleDataPoint) {
		const location = locations.find((l) => l.name === item.id);
		if (location) {
			mapDataStore.setSelectedLocation(location);
			hoveredLocation = null;
			popoverPosition = null;
		}
	}
</script>

<div class="map-wrapper relative">
	<div class="relative z-0" data-testid="map-container">
		<BaseMap height={height} center={[2, 8]} zoom={4}>
			{#if viewMode === 'bubbles' && circleData.length > 0}
				<CircleLayer
					data={circleData}
					radiusRange={[5, 40]}
					colorRange={bubbleColorRange}
					onHover={handleHover}
					onClick={handleClick}
				/>
			{/if}

			{#if viewMode === 'choropleth' && worldGeo}
				<ChoroplethLayer
					geoJson={worldGeo}
					data={countryCounts}
					colorRange={choroplethColorRange}
					scaleMode="log"
				/>
			{/if}
		</BaseMap>

		<!-- Hover popover (for bubbles mode) -->
		{#if viewMode === 'bubbles'}
			<MapLocationPopover
				location={hoveredLocation}
				position={popoverPosition}
				itemLabel="articles"
			/>
		{/if}
	</div>

	{#if dataLoading}
		<div
			class="absolute top-4 left-1/2 -translate-x-1/2 bg-card px-4 py-2 rounded-lg shadow-lg border border-border"
		>
			<p class="text-sm text-muted-foreground">{t('common.loading')}</p>
		</div>
	{/if}

	<!-- Bubble Legend -->
	{#if showLegend && viewMode === 'bubbles' && legendItems.length > 0 && !dataLoading}
		<div class="absolute bottom-4 left-4 bg-card p-3 rounded-lg shadow-lg border border-border z-10">
			<div class="flex items-center justify-between mb-2">
				<span class="text-xs font-semibold text-foreground">{t('worldmap.article_count')}</span>
				<button
					class="text-muted-foreground hover:text-foreground transition-colors"
					onclick={() => (showLegend = false)}
					aria-label="Close legend"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="14"
						height="14"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
			</div>
			<div class="flex items-center gap-4">
				{#each legendItems as item}
					<div class="flex items-center gap-1.5">
						<span class="w-3 h-3 rounded-full" style="background: {item.color}"></span>
						<span class="text-xs text-muted-foreground">{item.label}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Legend Toggle -->
	{#if !showLegend && viewMode === 'bubbles' && legendItems.length > 0 && !dataLoading}
		<button
			class="absolute bottom-4 left-4 bg-card p-2 rounded-lg shadow-lg border border-border hover:bg-accent transition-colors z-10"
			onclick={() => (showLegend = true)}
			aria-label="Show legend"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
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

<style>
	.map-wrapper {
		width: 100%;
	}
</style>

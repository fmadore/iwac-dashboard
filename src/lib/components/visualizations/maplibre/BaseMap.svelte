<script lang="ts" module>
	import type { Map as MapLibreMap } from 'maplibre-gl';

	// Context key for child components
	export const MAP_CONTEXT_KEY = Symbol('maplibre-map');

	export interface MapContext {
		getMap: () => MapLibreMap | null;
		onMapReady: (callback: (map: MapLibreMap) => void) => void;
	}
</script>

<script lang="ts">
	import { onMount, setContext } from 'svelte';
	import { browser } from '$app/environment';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import {
		isDarkTheme,
		createThemeObserver,
		getThemeColors
	} from './utils/theme.js';
	import { createRasterStyle } from './types.js';
	import { WEST_AFRICA_CENTER, DEFAULT_ZOOM } from './utils/coordinates.js';

	interface Props {
		center?: [number, number]; // [lng, lat]
		zoom?: number;
		bounds?: [[number, number], [number, number]]; // [[sw], [ne]]
		height?: string;
		minZoom?: number;
		maxZoom?: number;
		onMapReady?: (map: MapLibreMap) => void;
		children?: import('svelte').Snippet;
	}

	let {
		center = WEST_AFRICA_CENTER,
		zoom = DEFAULT_ZOOM,
		bounds,
		height = '500px',
		minZoom = 2,
		maxZoom = 12,
		onMapReady,
		children
	}: Props = $props();

	let mapContainer: HTMLDivElement;
	let map: MapLibreMap | null = $state(null);
	let mapLoading = $state(true);
	let cleanupThemeObserver: (() => void) | null = null;
	let readyCallbacks: Array<(map: MapLibreMap) => void> = [];

	// Provide context for child layer components
	setContext<MapContext>(MAP_CONTEXT_KEY, {
		getMap: () => map,
		onMapReady: (callback) => {
			if (map) {
				callback(map);
			} else {
				readyCallbacks.push(callback);
			}
		}
	});

	function updateMapStyle() {
		if (!map) return;

		const isDark = isDarkTheme();
		const newStyle = createRasterStyle(isDark);

		// Update the style - this preserves sources/layers we've added
		map.setStyle(newStyle);
	}

	onMount(() => {
		if (!browser) return;

		const initMap = async () => {
			try {
				const maplibregl = await import('maplibre-gl');

				// Import MapLibre CSS
				await import('maplibre-gl/dist/maplibre-gl.css');

				const isDark = isDarkTheme();
				const initialStyle = createRasterStyle(isDark);

				map = new maplibregl.Map({
					container: mapContainer,
					style: initialStyle,
					center: center,
					zoom: zoom,
					minZoom: minZoom,
					maxZoom: maxZoom
				});

				// Fit to bounds if provided
				if (bounds) {
					map.fitBounds(bounds, { padding: 50 });
				}

				// Add navigation controls
				map.addControl(new maplibregl.NavigationControl(), 'top-right');

				// Wait for map to be ready
				map.on('load', () => {
					mapLoading = false;

					// Notify parent
					if (onMapReady && map) {
						onMapReady(map);
					}

					// Notify child components
					for (const callback of readyCallbacks) {
						if (map) callback(map);
					}
					readyCallbacks = [];
				});

				// Set up theme observer
				cleanupThemeObserver = createThemeObserver(() => {
					updateMapStyle();
				});
			} catch (error) {
				console.error('Failed to initialize MapLibre map:', error);
				mapLoading = false;
			}
		};

		initMap();

		return () => {
			if (cleanupThemeObserver) {
				cleanupThemeObserver();
			}
			if (map) {
				map.remove();
				map = null;
			}
		};
	});

	// Update center/zoom when props change
	$effect(() => {
		if (map && center) {
			map.setCenter(center);
		}
	});

	$effect(() => {
		if (map && zoom) {
			map.setZoom(zoom);
		}
	});

	$effect(() => {
		if (map && bounds) {
			map.fitBounds(bounds, { padding: 50 });
		}
	});
</script>

<div class="map-wrapper relative">
	<div
		class="map-container relative z-0"
		bind:this={mapContainer}
		style="height: {height};"
		data-testid="maplibre-container"
	>
		{#if !mapLoading && children}
			{@render children()}
		{/if}
	</div>

	{#if mapLoading}
		<div class="absolute inset-0 flex items-center justify-center bg-background/80 rounded-xl">
			<div class="text-center">
				<Skeleton class="h-8 w-32 mx-auto mb-2" />
				<p class="text-sm text-muted-foreground">{t('common.loading')}</p>
			</div>
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

	:global(.maplibregl-map) {
		font-family: inherit;
		border-radius: 12px;
	}

	:global(.maplibregl-ctrl-group) {
		border-radius: 8px !important;
		box-shadow: 0 2px 8px color-mix(in oklch, var(--foreground) 18%, transparent) !important;
		border: 1px solid var(--border) !important;
		overflow: hidden;
	}

	:global(.maplibregl-ctrl-group button) {
		background: var(--card) !important;
		border-color: var(--border) !important;
	}

	:global(.maplibregl-ctrl-group button:hover) {
		background: var(--accent) !important;
	}

	:global(.maplibregl-ctrl-group button span) {
		/* Navigation icons - use filter to colorize */
		filter: var(--maplibre-icon-filter, none);
	}

	:global(.dark .maplibregl-ctrl-group button span) {
		filter: invert(1);
	}

	:global(.maplibregl-ctrl-attrib) {
		background: color-mix(in oklch, var(--card) 90%, transparent) !important;
		border-radius: 4px;
		font-size: 10px;
	}

	:global(.maplibregl-ctrl-attrib a) {
		color: var(--muted-foreground) !important;
	}

	:global(.maplibregl-popup-content) {
		background: var(--card);
		color: var(--foreground);
		border-radius: 8px;
		box-shadow: 0 4px 12px color-mix(in oklch, var(--foreground) 18%, transparent);
		border: 1px solid var(--border);
		padding: 8px 12px;
	}

	:global(.maplibregl-popup-tip) {
		border-top-color: var(--card) !important;
		border-bottom-color: var(--card) !important;
	}
</style>

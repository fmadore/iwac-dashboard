<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Map as MapLibreMap, GeoJSONSource } from 'maplibre-gl';
	import { MAP_CONTEXT_KEY, type MapContext } from './BaseMap.svelte';
	import { createLineWidthScale, createOpacityScale } from './utils/scales.js';
	import { getThemeColors, createThemeObserver } from './utils/theme.js';
	import { createLineFeature, toGeoJsonSource, type NetworkEdge } from './types.js';

	interface Props {
		edges: NetworkEdge[];
		highlightedNodeId?: string | null;
		widthRange?: [number, number];
		opacityRange?: [number, number];
		color?: string;
		highlightColor?: string;
	}

	let {
		edges = [],
		highlightedNodeId = null,
		widthRange = [1, 4],
		opacityRange = [0.3, 0.8],
		color,
		highlightColor
	}: Props = $props();

	const SOURCE_ID = 'line-layer-source';
	const LAYER_ID = 'line-layer';

	const mapContext = getContext<MapContext>(MAP_CONTEXT_KEY);
	let map: MapLibreMap | null = null;
	let cleanupThemeObserver: (() => void) | null = null;

	// Computed min/max weights
	const minWeight = $derived(edges.length > 0 ? Math.min(...edges.map((e) => e.weight)) : 0);
	const maxWeight = $derived(edges.length > 0 ? Math.max(...edges.map((e) => e.weight)) : 1);

	// Scales
	const widthScale = $derived(createLineWidthScale([minWeight, maxWeight], widthRange));
	const opacityScale = $derived(createOpacityScale([minWeight, maxWeight], opacityRange));

	function getColors() {
		const colors = getThemeColors();
		return {
			default: color || colors.chart3,
			highlight: highlightColor || colors.chart1
		};
	}

	function createGeoJsonData() {
		const colors = getColors();

		const features = edges.map((edge, index) => {
			const width = widthScale(edge.weight);
			let opacity = opacityScale(edge.weight);
			let lineColor = colors.default;

			// Highlighting logic
			if (highlightedNodeId) {
				// Check if this edge connects to the highlighted node
				// We need to match by checking source/target coordinates or ids
				// For simplicity, we use the edge id if available
				const isHighlighted = edge.id?.includes(highlightedNodeId) ?? false;

				if (isHighlighted) {
					lineColor = colors.highlight;
					opacity = 0.8;
				} else {
					opacity = 0.15;
				}
			}

			return createLineFeature(edge.id || `edge-${index}`, [edge.source, edge.target], {
				weight: edge.weight,
				width,
				opacity,
				color: lineColor
			});
		});

		return toGeoJsonSource(features);
	}

	function updateLayer() {
		if (!map) return;

		const source = map.getSource(SOURCE_ID) as GeoJSONSource | undefined;
		if (source) {
			source.setData(createGeoJsonData());
		}
	}

	function setupLayer(mapInstance: MapLibreMap) {
		map = mapInstance;

		// Add source
		if (!map.getSource(SOURCE_ID)) {
			map.addSource(SOURCE_ID, {
				type: 'geojson',
				data: createGeoJsonData()
			});
		}

		// Add line layer (render below circles by adding before circle layer if it exists)
		if (!map.getLayer(LAYER_ID)) {
			map.addLayer({
				id: LAYER_ID,
				type: 'line',
				source: SOURCE_ID,
				layout: {
					'line-cap': 'round',
					'line-join': 'round'
				},
				paint: {
					'line-color': ['get', 'color'],
					'line-width': ['get', 'width'],
					'line-opacity': ['get', 'opacity']
				}
			});
		}

		// Theme observer
		cleanupThemeObserver = createThemeObserver(() => {
			updateLayer();
		});
	}

	function cleanup() {
		if (cleanupThemeObserver) {
			cleanupThemeObserver();
		}

		if (map) {
			if (map.getLayer(LAYER_ID)) {
				map.removeLayer(LAYER_ID);
			}
			if (map.getSource(SOURCE_ID)) {
				map.removeSource(SOURCE_ID);
			}
		}
	}

	onMount(() => {
		mapContext.onMapReady(setupLayer);
		return cleanup;
	});

	// Update when data or highlight changes
	$effect(() => {
		void edges;
		void highlightedNodeId;
		void color;
		void highlightColor;

		updateLayer();
	});
</script>

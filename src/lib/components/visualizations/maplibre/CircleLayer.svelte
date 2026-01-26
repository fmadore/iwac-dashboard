<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Map as MapLibreMap, MapLayerMouseEvent, GeoJSONSource } from 'maplibre-gl';
	import { MAP_CONTEXT_KEY, type MapContext } from './BaseMap.svelte';
	import { createRadiusScale, createColorScale, darkenColor } from './utils/scales.js';
	import { getThemeColors, createThemeObserver } from './utils/theme.js';
	import { getPopoverPosition } from './utils/coordinates.js';
	import { createPointFeature, toGeoJsonSource, type CircleDataPoint } from './types.js';
	import type { PopoverPosition } from '$lib/types/map-location.js';

	interface Props {
		data: CircleDataPoint[];
		radiusRange?: [number, number];
		colorRange?: [string, string];
		selectedId?: string | number | null;
		onHover?: (item: CircleDataPoint | null, position: PopoverPosition | null) => void;
		onClick?: (item: CircleDataPoint) => void;
	}

	let {
		data = [],
		radiusRange = [5, 40],
		colorRange,
		selectedId = null,
		onHover,
		onClick
	}: Props = $props();

	const SOURCE_ID = 'circle-layer-source';
	const LAYER_ID = 'circle-layer';
	const LAYER_ID_STROKE = 'circle-layer-stroke';

	const mapContext = getContext<MapContext>(MAP_CONTEXT_KEY);
	let map: MapLibreMap | null = null;
	let hoveredId: string | number | null = null;
	let cleanupThemeObserver: (() => void) | null = null;

	// Computed min/max values
	const minValue = $derived(data.length > 0 ? Math.min(...data.map((d) => d.value)) : 0);
	const maxValue = $derived(data.length > 0 ? Math.max(...data.map((d) => d.value)) : 1);

	// Create scales
	const radiusScale = $derived(createRadiusScale([minValue, maxValue], radiusRange));

	function getColorRange(): [string, string] {
		if (colorRange) return colorRange;
		const colors = getThemeColors();
		return [colors.chart2, colors.chart6];
	}

	function createGeoJsonData() {
		const currentColorRange = getColorRange();
		const colorScale = createColorScale([minValue, maxValue], currentColorRange);
		const colors = getThemeColors();

		const features = data.map((point) => {
			const radius = radiusScale(point.value);
			const color = colorScale(point.value);
			const isSelected = selectedId !== null && point.id === selectedId;
			const isHovered = hoveredId !== null && point.id === hoveredId;

			// Subtle stroke - slightly darker than fill for definition
			const strokeColor = isSelected
				? colors.primary
				: darkenColor(color, 0.15);

			return createPointFeature(point.id, point.lng, point.lat, {
				...point,
				radius: isSelected ? radius * 1.2 : radius,
				color,
				strokeColor,
				strokeWidth: isSelected || isHovered ? 2 : 1,
				opacity: isSelected || isHovered ? 0.9 : 0.8
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

		// Add circle fill layer
		if (!map.getLayer(LAYER_ID)) {
			map.addLayer({
				id: LAYER_ID,
				type: 'circle',
				source: SOURCE_ID,
				paint: {
					'circle-radius': ['get', 'radius'],
					'circle-color': ['get', 'color'],
					'circle-opacity': ['get', 'opacity']
				}
			});
		}

		// Add circle stroke layer
		if (!map.getLayer(LAYER_ID_STROKE)) {
			map.addLayer({
				id: LAYER_ID_STROKE,
				type: 'circle',
				source: SOURCE_ID,
				paint: {
					'circle-radius': ['get', 'radius'],
					'circle-color': 'transparent',
					'circle-stroke-color': ['get', 'strokeColor'],
					'circle-stroke-width': ['get', 'strokeWidth']
				}
			});
		}

		// Add event handlers
		map.on('mouseenter', LAYER_ID, handleMouseEnter);
		map.on('mouseleave', LAYER_ID, handleMouseLeave);
		map.on('click', LAYER_ID, handleClick);

		// Change cursor on hover
		map.on('mouseenter', LAYER_ID, () => {
			if (map) map.getCanvas().style.cursor = 'pointer';
		});
		map.on('mouseleave', LAYER_ID, () => {
			if (map) map.getCanvas().style.cursor = '';
		});

		// Theme observer to update colors
		cleanupThemeObserver = createThemeObserver(() => {
			updateLayer();
		});
	}

	function handleMouseEnter(e: MapLayerMouseEvent) {
		if (!map || !e.features || e.features.length === 0) return;

		const feature = e.features[0];
		const props = feature.properties;
		hoveredId = props?.id ?? null;

		// Find the original data point
		const point = data.find((d) => d.id === props?.id);
		if (point && onHover) {
			const position = getPopoverPosition(map, e.lngLat);
			onHover(point, position);
		}

		updateLayer();
	}

	function handleMouseLeave() {
		hoveredId = null;
		if (onHover) {
			onHover(null, null);
		}
		updateLayer();
	}

	function handleClick(e: MapLayerMouseEvent) {
		if (!e.features || e.features.length === 0) return;

		const feature = e.features[0];
		const props = feature.properties;

		// Find the original data point
		const point = data.find((d) => d.id === props?.id);
		if (point && onClick) {
			onClick(point);
		}
	}

	function cleanup() {
		if (cleanupThemeObserver) {
			cleanupThemeObserver();
		}

		if (map) {
			map.off('mouseenter', LAYER_ID, handleMouseEnter);
			map.off('mouseleave', LAYER_ID, handleMouseLeave);
			map.off('click', LAYER_ID, handleClick);

			if (map.getLayer(LAYER_ID_STROKE)) {
				map.removeLayer(LAYER_ID_STROKE);
			}
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

	// Update when data or selection changes
	$effect(() => {
		// Track reactive dependencies
		void data;
		void selectedId;
		void colorRange;

		updateLayer();
	});
</script>

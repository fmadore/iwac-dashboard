<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Map as MapLibreMap, MapLayerMouseEvent, GeoJSONSource } from 'maplibre-gl';
	import { MAP_CONTEXT_KEY, type MapContext } from './BaseMap.svelte';
	import { createChoroplethScale } from './utils/scales.js';
	import { getThemeColors, createThemeObserver, getCssVarAsHex } from './utils/theme.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import type { ChoroplethData } from './types.js';

	// GeoJSON feature with name property
	interface GeoFeature {
		type: 'Feature';
		properties?: { name?: string; [key: string]: unknown };
		geometry: unknown;
	}

	// Accept any FeatureCollection-like structure
	interface Props {
		geoJson: { type: 'FeatureCollection'; features: GeoFeature[] };
		data: ChoroplethData;
		colorRange?: string[];
		scaleMode?: 'linear' | 'log' | 'quantile';
		onHover?: (countryName: string | null, value: number | null) => void;
		onClick?: (countryName: string, value: number) => void;
	}

	// Sequential orange gradient (light to dark) for MapLibre compatibility
	const DEFAULT_COLOR_RANGE = [
		'#fff7ed', // orange-50
		'#ffedd5', // orange-100
		'#fed7aa', // orange-200
		'#fdba74', // orange-300
		'#fb923c', // orange-400
		'#f97316', // orange-500
		'#ea580c'  // orange-600
	];

	let {
		geoJson,
		data = {},
		colorRange = DEFAULT_COLOR_RANGE,
		scaleMode = 'log',
		onHover,
		onClick
	}: Props = $props();

	const SOURCE_ID = 'choropleth-source';
	const FILL_LAYER_ID = 'choropleth-fill';
	const LINE_LAYER_ID = 'choropleth-line';
	const HIGHLIGHT_LAYER_ID = 'choropleth-highlight';

	const mapContext = getContext<MapContext>(MAP_CONTEXT_KEY);
	let map: MapLibreMap | null = null;
	let hoveredFeatureId: string | number | null = null;
	let cleanupThemeObserver: (() => void) | null = null;
	let legendControl: HTMLDivElement | null = null;
	let infoControl: HTMLDivElement | null = null;

	// Force reactivity on language changes
	const lang = $derived(languageStore.current);

	// Create color scale from data
	const colorScale = $derived.by(() => {
		const values = Object.values(data);
		return createChoroplethScale(values, colorRange, scaleMode);
	});

	function getFeatureColor(countryName: string): string {
		const value = data[countryName];
		if (value === undefined || value === 0 || !Number.isFinite(value)) {
			return getCssVarAsHex('--muted', '#e5e7eb');
		}
		const color = colorScale(value);
		// Safeguard against invalid colors (NaN in interpolation)
		if (!color || color.includes('NaN')) {
			return getCssVarAsHex('--muted', '#e5e7eb');
		}
		return color;
	}

	function createGeoJsonWithColors() {
		const features = geoJson.features.map((feature, index) => {
			const countryName = feature.properties?.name || '';
			const value = data[countryName] || 0;
			const color = getFeatureColor(countryName);

			return {
				type: 'Feature' as const,
				id: index, // MapLibre needs numeric IDs for feature-state
				geometry: feature.geometry,
				properties: {
					...feature.properties,
					fillColor: color,
					value,
					countryName
				}
			};
		});

		return {
			type: 'FeatureCollection' as const,
			features
		} as GeoJSON.FeatureCollection;
	}

	function updateLayer() {
		if (!map) return;

		const source = map.getSource(SOURCE_ID) as GeoJSONSource | undefined;
		if (source) {
			source.setData(createGeoJsonWithColors());
		}

		// Update legend
		updateLegend();
	}

	function createLegend() {
		if (!map) return;

		legendControl = document.createElement('div');
		legendControl.className = 'choropleth-legend';
		legendControl.style.cssText = `
			position: absolute;
			bottom: 24px;
			right: 10px;
			padding: 8px 12px;
			background: var(--card);
			border-radius: 8px;
			box-shadow: 0 2px 8px color-mix(in oklch, var(--foreground) 18%, transparent);
			border: 1px solid var(--border);
			color: var(--foreground);
			font-size: 0.75rem;
			line-height: 1.5;
			z-index: 10;
		`;

		updateLegend();

		map.getContainer().appendChild(legendControl);
	}

	function updateLegend() {
		if (!legendControl) return;

		const values = Object.values(data).filter((v) => v > 0);
		if (values.length === 0) {
			legendControl.innerHTML = `<div style="font-weight: 600;">${t('worldmap.no_data')}</div>`;
			return;
		}

		const min = Math.min(...values);
		const max = Math.max(...values);
		const bins = computeLegendBins(min, max, colorRange.length);

		let html = `<div style="margin-bottom: 4px; font-weight: 600;">${t('worldmap.article_count')}</div>`;
		for (let i = 0; i < bins.length; i++) {
			html += `
				<div style="display: flex; align-items: center; gap: 6px;">
					<span style="width: 16px; height: 16px; background: ${colorRange[i]}; border-radius: 2px; display: inline-block;"></span>
					<span>${formatValue(bins[i])}</span>
				</div>
			`;
		}

		legendControl.innerHTML = html;
	}

	function createInfoControl() {
		if (!map) return;

		infoControl = document.createElement('div');
		infoControl.className = 'choropleth-info';
		infoControl.style.cssText = `
			position: absolute;
			top: 10px;
			right: 10px;
			padding: 8px 12px;
			background: var(--card);
			border-radius: 8px;
			box-shadow: 0 2px 8px color-mix(in oklch, var(--foreground) 18%, transparent);
			border: 1px solid var(--border);
			color: var(--foreground);
			font-size: 0.875rem;
			z-index: 10;
		`;

		updateInfoControl(null, null);
		map.getContainer().appendChild(infoControl);
	}

	function updateInfoControl(countryName: string | null, value: number | null) {
		if (!infoControl) return;

		if (countryName && value !== null) {
			const articleText =
				value === 1
					? t('worldmap.article')
					: t('worldmap.articles', [value.toLocaleString()]);
			infoControl.innerHTML = `
				<h4 style="margin: 0 0 4px 0; font-weight: 600;">${countryName}</h4>
				<p style="margin: 0;">${articleText}</p>
			`;
		} else {
			infoControl.innerHTML = `
				<h4 style="margin: 0; font-weight: 500; color: var(--muted-foreground);">${t('worldmap.hover_country')}</h4>
			`;
		}
	}

	function computeLegendBins(min: number, max: number, binCount: number): number[] {
		if (scaleMode === 'log') {
			const safeMin = Math.max(1, min);
			const logMin = Math.log10(safeMin);
			const logMax = Math.log10(max);
			const step = (logMax - logMin) / (binCount - 1);
			return Array.from({ length: binCount }, (_, i) =>
				Math.round(Math.pow(10, logMin + i * step))
			);
		}

		const step = (max - min) / (binCount - 1);
		return Array.from({ length: binCount }, (_, i) => Math.round(min + i * step));
	}

	function formatValue(v: number): string {
		if (v >= 1000) return `${(v / 1000).toFixed(1)}k`;
		return v.toString();
	}

	function handleMouseMove(e: MapLayerMouseEvent) {
		if (!map || !e.features || e.features.length === 0) return;

		const feature = e.features[0];
		const countryName = feature.properties?.countryName || feature.properties?.name;
		const value = feature.properties?.value ?? 0;

		// Update hover state
		if (hoveredFeatureId !== null) {
			map.setFeatureState({ source: SOURCE_ID, id: hoveredFeatureId }, { hover: false });
		}

		hoveredFeatureId = feature.id as number;
		map.setFeatureState({ source: SOURCE_ID, id: hoveredFeatureId }, { hover: true });

		// Update info control
		updateInfoControl(countryName, value);

		// Callback
		if (onHover) {
			onHover(countryName, value);
		}

		map.getCanvas().style.cursor = 'pointer';
	}

	function handleMouseLeave() {
		if (!map) return;

		if (hoveredFeatureId !== null) {
			map.setFeatureState({ source: SOURCE_ID, id: hoveredFeatureId }, { hover: false });
			hoveredFeatureId = null;
		}

		updateInfoControl(null, null);

		if (onHover) {
			onHover(null, null);
		}

		map.getCanvas().style.cursor = '';
	}

	function handleClick(e: MapLayerMouseEvent) {
		if (!e.features || e.features.length === 0) return;

		const feature = e.features[0];
		const countryName = feature.properties?.countryName || feature.properties?.name;
		const value = feature.properties?.value ?? 0;

		if (onClick && countryName) {
			onClick(countryName, value);
		}
	}

	function setupLayer(mapInstance: MapLibreMap) {
		map = mapInstance;

		// Add source
		if (!map.getSource(SOURCE_ID)) {
			map.addSource(SOURCE_ID, {
				type: 'geojson',
				data: createGeoJsonWithColors(),
				generateId: false
			});
		}

		// Add fill layer
		if (!map.getLayer(FILL_LAYER_ID)) {
			map.addLayer({
				id: FILL_LAYER_ID,
				type: 'fill',
				source: SOURCE_ID,
				paint: {
					'fill-color': ['get', 'fillColor'],
					'fill-opacity': [
						'case',
						['boolean', ['feature-state', 'hover'], false],
						0.9,
						0.7
					]
				}
			});
		}

		// Add line layer for borders
		if (!map.getLayer(LINE_LAYER_ID)) {
			const colors = getThemeColors();
			map.addLayer({
				id: LINE_LAYER_ID,
				type: 'line',
				source: SOURCE_ID,
				paint: {
					'line-color': [
						'case',
						['boolean', ['feature-state', 'hover'], false],
						colors.primary,
						colors.border
					],
					'line-width': [
						'case',
						['boolean', ['feature-state', 'hover'], false],
						2,
						0.5
					]
				}
			});
		}

		// Event handlers
		map.on('mousemove', FILL_LAYER_ID, handleMouseMove);
		map.on('mouseleave', FILL_LAYER_ID, handleMouseLeave);
		map.on('click', FILL_LAYER_ID, handleClick);

		// Create controls
		createLegend();
		createInfoControl();

		// Theme observer
		cleanupThemeObserver = createThemeObserver(() => {
			updateLayer();
		});
	}

	function cleanup() {
		if (cleanupThemeObserver) {
			cleanupThemeObserver();
		}

		if (legendControl) {
			legendControl.remove();
			legendControl = null;
		}

		if (infoControl) {
			infoControl.remove();
			infoControl = null;
		}

		if (map) {
			map.off('mousemove', FILL_LAYER_ID, handleMouseMove);
			map.off('mouseleave', FILL_LAYER_ID, handleMouseLeave);
			map.off('click', FILL_LAYER_ID, handleClick);

			if (map.getLayer(LINE_LAYER_ID)) {
				map.removeLayer(LINE_LAYER_ID);
			}
			if (map.getLayer(FILL_LAYER_ID)) {
				map.removeLayer(FILL_LAYER_ID);
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

	// Update when data or colors change (only if map is ready)
	$effect(() => {
		// Track dependencies
		void data;
		void colorRange;
		void scaleMode;
		void lang;

		// Only update if map and source exist
		if (map && map.getSource(SOURCE_ID)) {
			updateLayer();
		}
	});
</script>

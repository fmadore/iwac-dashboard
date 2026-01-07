<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { scaleQuantize, scaleQuantile, scaleLog, scaleLinear } from 'd3-scale';
	import type { GeoJsonData, GeoJsonFeature, ChoroplethScaleConfig } from '$lib/types/worldmap.js';
	import { browser } from '$app/environment';
	import { t } from '$lib/stores/translationStore.svelte.js';

	// Chart colors from our CSS variables
	const DEFAULT_COLOR_RANGE = [
		'oklch(0.95 0.02 220)', // Very light
		'oklch(0.85 0.06 55)',
		'oklch(0.75 0.10 55)',
		'oklch(0.65 0.13 55)',
		'oklch(0.55 0.15 55)',
		'oklch(0.50 0.16 55)',
		'oklch(0.45 0.17 55)' // Darkest - primary-ish
	];

	// Props
	let {
		map,
		geoJson,
		data = {},
		colorRange = DEFAULT_COLOR_RANGE,
		scaleMode = 'log'
	}: {
		map: L.Map;
		geoJson: GeoJsonData;
		data?: Record<string, number>;
		colorRange?: string[];
		scaleMode?: ChoroplethScaleConfig['mode'];
	} = $props();

	// Local state
	let layer: L.GeoJSON | null = null;
	let info: L.Control | null = null;
	let legend: L.Control | null = null;
	let L: typeof import('leaflet') | null = null;

	const dispatch = createEventDispatcher();

	// Derived color scale
	const colorScale = $derived.by(() => generateColorScale(data, colorRange, scaleMode));

	onMount(() => {
		if (!browser || !map || !geoJson) return undefined;

		const initLayer = async () => {
			const leaflet = await import('leaflet');
			L = leaflet.default || leaflet;

			createLayer();
			createInfoControl();
			createLegendControl();
		};

		initLayer();

		return () => {
			if (layer && map) {
				map.removeLayer(layer);
			}
			if (info && map) {
				map.removeControl(info);
			}
			if (legend && map) {
				map.removeControl(legend);
			}
		};
	});

	function createLayer() {
		if (!L || !map || !geoJson) return;

		layer = L.geoJSON(geoJson, {
			style: styleFeature,
			onEachFeature: (feature, featureLayer) => {
				featureLayer.on({
					mouseover: highlightFeature,
					mouseout: resetHighlight,
					click: zoomToFeature
				});

				// Add popup
				const name = feature.properties?.name || 'Unknown';
				const value = data[name] || 0;
				const articleText = value === 1 ? t('worldmap.article') : t('worldmap.articles', [value.toLocaleString()]);
				featureLayer.bindPopup(`<strong>${name}</strong><br>${articleText}`);
			},
			interactive: true
		}).addTo(map);

		// Update styles if data is available
		if (Object.keys(data).length > 0) {
			updateLayerStyles();
		}
	}

	function createInfoControl() {
		if (!L || !map) return;
		const Leaflet = L;

		const InfoControl = L.Control.extend({
			options: { position: 'topright' },
			onAdd: function () {
				const div = Leaflet.DomUtil.create('div', 'choropleth-info');
				div.innerHTML = '<h4>' + t('worldmap.article_count') + '</h4><p>' + t('common.loading') + '</p>';
				div.style.cssText = `
					padding: 8px 12px;
					background: var(--card);
					border-radius: 8px;
					box-shadow: 0 2px 8px color-mix(in oklch, var(--foreground) 18%, transparent);
					border: 1px solid var(--border);
					color: var(--foreground);
					font-size: 0.875rem;
				`;
				return div;
			},
			update: function (props?: GeoJsonFeature['properties']) {
				const div = (this as any)._container;
				if (!div) return;
				
				if (props && props.name) {
					const value = data[props.name] || 0;
					const articleText = value === 1 ? t('worldmap.article') : t('worldmap.articles', [value.toLocaleString()]);
					div.innerHTML = `<h4 style="margin: 0 0 4px 0; font-weight: 600;">${props.name}</h4><p style="margin: 0;">${articleText}</p>`;
				} else {
					div.innerHTML = `<h4 style="margin: 0; font-weight: 500; color: var(--muted-foreground);">${t('worldmap.hover_country')}</h4>`;
				}
			}
		});

		info = new InfoControl();
		info.addTo(map);
		(info as any).update();
	}

	function createLegendControl() {
		if (!L || !map) return;
		const Leaflet = L;

		const bins = computeLegendBins(data, colorRange.length, scaleMode);

		const LegendControl = L.Control.extend({
			options: { position: 'bottomright' },
			onAdd: function () {
				const div = Leaflet.DomUtil.create('div', 'choropleth-legend');
				div.style.cssText = `
					padding: 8px 12px;
						background: var(--card);
					border-radius: 8px;
						box-shadow: 0 2px 8px color-mix(in oklch, var(--foreground) 18%, transparent);
						border: 1px solid var(--border);
						color: var(--foreground);
					font-size: 0.75rem;
					line-height: 1.5;
				`;

				let html = `<div style="margin-bottom: 4px; font-weight: 600;">${t('worldmap.article_count')}</div>`;
				for (let i = 0; i < bins.length; i++) {
					html += `
						<div style="display: flex; align-items: center; gap: 6px;">
							<span style="width: 16px; height: 16px; background: ${colorRange[i]}; border-radius: 2px; display: inline-block;"></span>
							<span>${formatLegendValue(bins[i])}</span>
						</div>
					`;
				}
				div.innerHTML = html;
				return div;
			}
		});

		legend = new LegendControl();
		legend.addTo(map);
	}

	function styleFeature(feature: GeoJsonFeature | any) {
		if (!feature.properties || !feature.properties.name) {
			return {
				fillColor: 'var(--muted)',
				weight: 1,
				opacity: 1,
				color: 'var(--border)',
				fillOpacity: 0.7
			};
		}

		const regionName = feature.properties.name;
		const value = data[regionName] || 0;
		const scale = colorScale;

		let fillColor = 'oklch(0.95 0.01 220)';
		try {
			fillColor = scale(value);
		} catch (e) {
			console.warn('Color scale error for', regionName, e);
		}

		return {
			fillColor,
			weight: 1,
			opacity: 1,
			color: 'var(--border)',
			fillOpacity: 0.7
		};
	}

	function highlightFeature(e: L.LeafletMouseEvent) {
		if (!L) return;

		const featureLayer = e.target;
		featureLayer.setStyle({
			weight: 2,
			color: 'var(--primary)',
			fillOpacity: 0.9
		});

		if (info) {
			(info as any).update(featureLayer.feature.properties);
		}

		dispatch('highlightRegion', {
			region: featureLayer.feature.properties.name
		});
	}

	function resetHighlight(e: L.LeafletMouseEvent) {
		if (layer) {
			layer.resetStyle(e.target);
		}

		if (info) {
			(info as any).update();
		}

		dispatch('resetHighlight', {
			region: e.target.feature.properties.name
		});
	}

	function zoomToFeature(e: L.LeafletMouseEvent) {
		map.fitBounds(e.target.getBounds());
		if (e?.target && typeof e.target.openPopup === 'function') {
			e.target.openPopup();
		}

		dispatch('selectRegion', {
			region: e.target.feature.properties.name
		});
	}

	function generateColorScale(
		data: Record<string, number>,
		range: string[],
		mode: ChoroplethScaleConfig['mode']
	) {
		const raw = Object.values(data).filter((v) => Number.isFinite(v) && v > 0);

		if (raw.length === 0) {
			return () => range[0];
		}

		if (mode === 'quantile') {
			return scaleQuantile<string>().domain(raw).range(range);
		}

		const min = Math.min(...raw);
		const max = Math.max(...raw);

		if (mode === 'log') {
			const safeMin = Math.max(1, min);
			return scaleLog<string>()
				.domain([safeMin, max])
				.range([range[0], range[range.length - 1]])
				.clamp(true);
		}

		return scaleLinear<string>()
			.domain([min, max])
			.range([range[0], range[range.length - 1]]);
	}

	function computeLegendBins(
		data: Record<string, number>,
		binCount: number,
		mode: ChoroplethScaleConfig['mode']
	): (number | null)[] {
		const raw = Object.values(data).filter((v) => Number.isFinite(v) && v > 0);
		if (raw.length === 0) return Array(binCount).fill(null);

		const min = Math.min(...raw);
		const max = Math.max(...raw);

		if (mode === 'quantile') {
			const sorted = [...raw].sort((a, b) => a - b);
			const step = sorted.length / binCount;
			return Array.from({ length: binCount }, (_, i) => sorted[Math.floor(i * step)] || null);
		}

		if (mode === 'log') {
			const safeMin = Math.max(1, min);
			const logMin = Math.log10(safeMin);
			const logMax = Math.log10(max);
			const step = (logMax - logMin) / (binCount - 1);
			return Array.from({ length: binCount }, (_, i) => Math.round(Math.pow(10, logMin + i * step)));
		}

		const step = (max - min) / (binCount - 1);
		return Array.from({ length: binCount }, (_, i) => Math.round(min + i * step));
	}

	function formatLegendValue(v?: number | null): string {
		if (v === null || v === undefined) return '—';
		if (v >= 1000) return `${(v / 1000).toFixed(1)}k`;
		return v.toString();
	}

	function updateLayerStyles() {
		if (!layer) return;

		layer.eachLayer((featureLayer: any) => {
			if (featureLayer.feature) {
				featureLayer.setStyle(styleFeature(featureLayer.feature));
			}
		});
	}

	// Watch for data changes and update layer styles
	$effect(() => {
		if (layer && Object.keys(data).length > 0) {
			updateLayerStyles();
		}
	});

	// Refresh legend when palette/mode changes (e.g. light/dark theme swap)
	$effect(() => {
		if (!map || !L) return;

		// Track dependencies explicitly
		const _palette = colorRange;
		const _mode = scaleMode;
		const _dataSize = Object.keys(data).length;
		void _palette;
		void _mode;
		void _dataSize;

		if (legend) {
			map.removeControl(legend);
			legend = null;
			createLegendControl();
		}
	});
</script>

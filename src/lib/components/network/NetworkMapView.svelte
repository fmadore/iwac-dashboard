<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import type { NetworkNode, NetworkEdge, NodeSizeBy } from '$lib/types/network.js';

	interface Props {
		nodes: NetworkNode[];
		edges: NetworkEdge[];
		selectedNodeId?: string | null;
		nodeSizeBy?: NodeSizeBy;
		minEdgeWeight?: number;
		onNodeClick?: (node: NetworkNode | null) => void;
		onNodeHover?: (node: NetworkNode | null) => void;
		bounds?: { north: number; south: number; east: number; west: number } | null;
	}

	let {
		nodes = [],
		edges = [],
		selectedNodeId = null,
		nodeSizeBy = 'count',
		minEdgeWeight = 1,
		onNodeClick,
		onNodeHover,
		bounds = null
	}: Props = $props();

	let mapElement: HTMLDivElement | null = $state(null);
	let map: L.Map | null = $state(null);
	let L: typeof import('leaflet') | null = null;
	let markersLayer: L.LayerGroup | null = null;
	let edgesLayer: L.LayerGroup | null = null;
	let tileLayer: L.TileLayer | null = null;
	let isLoading = $state(true);

	// Filter edges by minimum weight
	const filteredEdges = $derived(edges.filter((e) => e.weight >= minEdgeWeight));

	// Calculate node sizes based on selected metric
	const nodeSizes = $derived.by(() => {
		const sizes: Record<string, number> = {};
		let maxValue = 1;

		for (const node of nodes) {
			const value =
				nodeSizeBy === 'count' ? node.count : nodeSizeBy === 'degree' ? node.degree : node.strength;
			sizes[node.id] = value;
			if (value > maxValue) maxValue = value;
		}

		// Normalize to 6-25 range for map markers
		for (const id in sizes) {
			sizes[id] = 6 + (sizes[id] / maxValue) * 19;
		}

		return sizes;
	});

	// Build node lookup for edges
	const nodeById = $derived(
		nodes.reduce(
			(acc, node) => {
				acc[node.id] = node;
				return acc;
			},
			{} as Record<string, NetworkNode>
		)
	);

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

	function getThemeColors() {
		return {
			primary: getCssVar('--chart-1', '#e8590c'),
			secondary: getCssVar('--chart-2', '#2563eb'),
			muted: getCssVar('--muted-foreground', '#666666'),
			edge: getCssVar('--chart-3', '#16a34a'),
			edgeHighlight: getCssVar('--chart-1', '#e8590c')
		};
	}

	async function initMap() {
		if (!browser || !mapElement) return;

		try {
			L = await import('leaflet');

			// Initialize map
			map = L.map(mapElement, {
				center: [10, 0],
				zoom: 3,
				minZoom: 2,
				maxZoom: 12,
				zoomControl: true,
				scrollWheelZoom: true
			});

			// Add tile layer
			const tileConfig = isDarkActive() ? tileLayerOptions.dark : tileLayerOptions.light;
			tileLayer = L.tileLayer(tileConfig.url, {
				attribution: tileConfig.attribution,
				maxZoom: 19
			}).addTo(map);

			// Create layer groups
			edgesLayer = L.layerGroup().addTo(map);
			markersLayer = L.layerGroup().addTo(map);

			// Fit to bounds if provided
			if (bounds) {
				map.fitBounds([
					[bounds.south, bounds.west],
					[bounds.north, bounds.east]
				]);
			}

			isLoading = false;
			renderNetwork();
		} catch (error) {
			console.error('Failed to initialize map:', error);
			isLoading = false;
		}
	}

	function renderNetwork() {
		if (!L || !map || !markersLayer || !edgesLayer) return;

		const colors = getThemeColors();

		// Clear existing layers
		markersLayer.clearLayers();
		edgesLayer.clearLayers();

		// Draw edges first (so nodes appear on top)
		for (const edge of filteredEdges) {
			const sourceNode = nodeById[edge.source];
			const targetNode = nodeById[edge.target];

			if (!sourceNode || !targetNode) continue;

			const isHighlighted =
				selectedNodeId && (edge.source === selectedNodeId || edge.target === selectedNodeId);

			const polyline = L.polyline(
				[
					[sourceNode.coordinates[0], sourceNode.coordinates[1]],
					[targetNode.coordinates[0], targetNode.coordinates[1]]
				],
				{
					color: isHighlighted ? colors.edgeHighlight : colors.edge,
					weight: 1 + edge.weightNorm * 3,
					opacity: isHighlighted ? 0.8 : selectedNodeId ? 0.15 : 0.4
				}
			);

			polyline.addTo(edgesLayer);
		}

		// Draw nodes
		for (const node of nodes) {
			const isSelected = node.id === selectedNodeId;
			const isConnected =
				selectedNodeId &&
				filteredEdges.some(
					(e) =>
						(e.source === selectedNodeId && e.target === node.id) ||
						(e.target === selectedNodeId && e.source === node.id)
				);

			let markerColor = colors.primary;
			let markerOpacity = 0.85;
			let markerSize = nodeSizes[node.id] || 10;

			if (selectedNodeId) {
				if (isSelected) {
					markerColor = colors.secondary;
					markerSize *= 1.3;
				} else if (isConnected) {
					markerColor = colors.primary;
				} else {
					markerColor = colors.muted;
					markerOpacity = 0.4;
					markerSize *= 0.8;
				}
			}

			const marker = L.circleMarker([node.coordinates[0], node.coordinates[1]], {
				radius: markerSize,
				fillColor: markerColor,
				fillOpacity: markerOpacity,
				color: isSelected ? colors.secondary : '#ffffff',
				weight: isSelected ? 3 : 1.5,
				opacity: 1
			});

			// Tooltip
			marker.bindTooltip(
				`<strong>${node.label}</strong><br/>
				${t('network.articles')}: ${node.count}<br/>
				${t('network.connections')}: ${node.degree}`,
				{ direction: 'top', offset: [0, -markerSize] }
			);

			// Events
			marker.on('click', () => {
				onNodeClick?.(node);
			});

			marker.on('mouseover', () => {
				onNodeHover?.(node);
			});

			marker.on('mouseout', () => {
				onNodeHover?.(null);
			});

			marker.addTo(markersLayer);
		}
	}

	// Re-render when data or selection changes
	$effect(() => {
		if (map && L) {
			// Access reactive values to track them
			const _ = [nodes, filteredEdges, selectedNodeId, nodeSizeBy, minEdgeWeight];
			renderNetwork();
		}
	});

	onMount(() => {
		initMap();

		// Watch for theme changes
		const observer = new MutationObserver(() => {
			if (map && L && tileLayer) {
				const tileConfig = isDarkActive() ? tileLayerOptions.dark : tileLayerOptions.light;
				tileLayer.setUrl(tileConfig.url);
				renderNetwork();
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
				map = null;
			}
		};
	});

	export function resetView() {
		if (map && bounds) {
			map.fitBounds([
				[bounds.south, bounds.west],
				[bounds.north, bounds.east]
			]);
		}
	}

	export function focusNode(nodeId: string) {
		const node = nodeById[nodeId];
		if (map && node) {
			map.setView([node.coordinates[0], node.coordinates[1]], 8, { animate: true });
		}
	}
</script>

<svelte:head>
	<link
		rel="stylesheet"
		href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
		integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
		crossorigin=""
	/>
</svelte:head>

<div class="relative h-full w-full">
	<div bind:this={mapElement} class="h-full w-full rounded-lg"></div>
	{#if isLoading}
		<div class="absolute inset-0 flex items-center justify-center bg-background/80 rounded-lg">
			<div class="text-center">
				<div
					class="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"
				></div>
				<p class="mt-2 text-sm text-muted-foreground">{t('network.loading_map')}</p>
			</div>
		</div>
	{/if}
</div>

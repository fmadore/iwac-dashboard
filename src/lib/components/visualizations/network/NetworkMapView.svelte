<script lang="ts">
	import { t } from '$lib/stores/translationStore.svelte.js';
	import {
		BaseMap,
		CircleLayer,
		LineLayer,
		type CircleDataPoint,
		type NetworkEdge as MapLibreNetworkEdge,
		calculateBounds
	} from '$lib/components/visualizations/maplibre/index.js';
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

	// Filter edges by minimum weight
	const filteredEdges = $derived(edges.filter((e) => e.weight >= minEdgeWeight));

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

	// Transform nodes to CircleDataPoints for MapLibre
	const circleData = $derived<CircleDataPoint[]>(
		nodes.map((node) => {
			const value =
				nodeSizeBy === 'count' ? node.count : nodeSizeBy === 'degree' ? node.degree : node.strength;

			return {
				id: node.id,
				lat: node.coordinates[0],
				lng: node.coordinates[1],
				value,
				label: node.label,
				count: node.count,
				degree: node.degree,
				strength: node.strength
			};
		})
	);

	// Transform edges to LineLayer format
	const lineEdges = $derived.by(() => {
		const result: MapLibreNetworkEdge[] = [];

		for (const edge of filteredEdges) {
			const sourceNode = nodeById[edge.source];
			const targetNode = nodeById[edge.target];

			if (!sourceNode || !targetNode) continue;

			result.push({
				id: `${edge.source}-${edge.target}`,
				source: [sourceNode.coordinates[1], sourceNode.coordinates[0]], // [lng, lat]
				target: [targetNode.coordinates[1], targetNode.coordinates[0]],
				weight: edge.weight
			});
		}

		return result;
	});

	// Calculate map bounds
	const mapBounds = $derived.by(() => {
		if (bounds) {
			return [
				[bounds.west, bounds.south],
				[bounds.east, bounds.north]
			] as [[number, number], [number, number]];
		}
		if (nodes.length === 0) return undefined;
		const coords = nodes.map((n) => ({ lat: n.coordinates[0], lng: n.coordinates[1] }));
		return calculateBounds(coords) ?? undefined;
	});

	// Handle node hover
	function handleNodeHover(item: CircleDataPoint | null) {
		if (item && onNodeHover) {
			const node = nodeById[item.id as string];
			onNodeHover(node ?? null);
		} else if (onNodeHover) {
			onNodeHover(null);
		}
	}

	// Handle node click
	function handleNodeClick(item: CircleDataPoint) {
		if (onNodeClick) {
			const node = nodeById[item.id as string];
			onNodeClick(node ?? null);
		}
	}

	// Exported methods for parent component
	export function resetView() {
		// BaseMap handles this via bounds prop reactivity
	}

	export function focusNode(nodeId: string) {
		// This would require a ref to the map, which we could add later
	}
</script>

<div class="relative h-full w-full">
	<BaseMap height="100%" bounds={mapBounds} zoom={3} minZoom={2} maxZoom={12}>
		{#if lineEdges.length > 0}
			<LineLayer edges={lineEdges} highlightedNodeId={selectedNodeId} widthRange={[1, 4]} />
		{/if}

		{#if circleData.length > 0}
			<CircleLayer
				data={circleData}
				radiusRange={[6, 25]}
				selectedId={selectedNodeId}
				onHover={(item, _pos) => handleNodeHover(item)}
				onClick={handleNodeClick}
			/>
		{/if}
	</BaseMap>
</div>

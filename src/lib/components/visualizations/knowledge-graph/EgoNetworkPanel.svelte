<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import type { GlobalNetworkNode, GlobalNetworkEdge } from '$lib/types/network.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Users, Building2, Calendar, Tag, MapPin, BookMarked } from '@lucide/svelte';

	interface EntityTypeConfig {
		label: string;
		color: string;
		icon: typeof Users;
	}

	interface Props {
		selectedNode: GlobalNetworkNode;
		allNodes: GlobalNetworkNode[];
		allEdges: GlobalNetworkEdge[];
		entityTypeColors: Record<string, EntityTypeConfig>;
		edgeTypeColors: Record<string, string>;
		onNodeClick?: (node: GlobalNetworkNode) => void;
	}

	let { selectedNode, allNodes, allEdges, entityTypeColors, edgeTypeColors, onNodeClick }: Props =
		$props();

	// Container width for SVG layout (bound from the wrapping div)
	let containerWidth = $state(0);
	const svgHeight = 350;
	// Force reactivity on language change (used by t() in markup)
	const _lang = $derived(languageStore.current);

	const DIRECTED_EDGE_TYPES = new Set(['part_of', 'has_part', 'located_in', 'succeeded_by']);

	type RenderEdge = {
		key: string;
		x1: number;
		y1: number;
		x2: number;
		y2: number;
		color: string;
		strokeWidth: number;
		isDirected: boolean;
		arrowPoints?: string;
	};

	type RenderNode = {
		id: string;
		x: number;
		y: number;
		size: number;
		color: string;
		label: string;
		showLabel: boolean;
		node: GlobalNetworkNode;
	};

	// Edge type labels for display
	const edgeTypeLabels: Record<string, string> = {
		part_of: 'kg.edge_part_of',
		has_part: 'kg.edge_has_part',
		related_to: 'kg.edge_related_to',
		succeeded_by: 'kg.edge_succeeded_by',
		located_in: 'kg.edge_located_in',
		co_occurs_with: 'kg.edge_co_occurs',
		co_authored_with: 'kg.edge_co_authored'
	};

	// Get ego network data
	const egoData = $derived.by(() => {
		const id = selectedNode.id;

		// Get edges connected to selected node
		const egoEdges = allEdges.filter((e) => e.source === id || e.target === id);

		// Get neighbor IDs
		// eslint-disable-next-line svelte/prefer-svelte-reactivity
		const neighborIds = new Set<string>(); // Local procedural Set; not reactive state.
		neighborIds.add(id);
		for (const edge of egoEdges) {
			neighborIds.add(edge.source);
			neighborIds.add(edge.target);
		}

		// Get neighbor nodes
		const nodeMap = new Map(allNodes.map((n) => [n.id, n]));
		const egoNodes = [...neighborIds]
			.map((nid) => nodeMap.get(nid))
			.filter((n): n is GlobalNetworkNode => n !== undefined);

		// Sort edges by weight
		const sortedEdges = [...egoEdges].sort((a, b) => b.weight - a.weight);

		// Group connections by edge type
		// eslint-disable-next-line svelte/prefer-svelte-reactivity
		const byType = new Map<string, Array<{ node: GlobalNetworkNode; edge: GlobalNetworkEdge }>>(); // Local procedural Map; not reactive state.
		for (const edge of sortedEdges) {
			const neighborId = edge.source === id ? edge.target : edge.source;
			const neighborNode = nodeMap.get(neighborId);
			if (!neighborNode) continue;

			const type = edge.type || 'unknown';
			if (!byType.has(type)) byType.set(type, []);
			byType.get(type)!.push({ node: neighborNode, edge });
		}

		return { nodes: egoNodes, edges: sortedEdges, byType };
	});

	// Compute the SVG layout reactively. Renders via Svelte template instead of
	// imperative DOM mutation so the runtime stays in sync.
	type EgoLayout = {
		width: number;
		centerX: number;
		centerY: number;
		centerColor: string;
		centerLabel: string;
		edges: RenderEdge[];
		nodes: RenderNode[];
	};

	const layout = $derived.by<EgoLayout | null>(() => {
		const width = containerWidth;
		if (width <= 0) return null;

		const centerX = width / 2;
		const centerY = svgHeight / 2;

		const neighbors = egoData.nodes.filter((n) => n.id !== selectedNode.id);
		if (neighbors.length === 0) {
			return {
				width,
				centerX,
				centerY,
				centerColor: entityTypeColors[selectedNode.type]?.color || '#888',
				centerLabel:
					selectedNode.label.length > 25
						? selectedNode.label.slice(0, 23) + '...'
						: selectedNode.label,
				edges: [],
				nodes: []
			};
		}

		const maxNeighbors = Math.min(neighbors.length, 30);
		const visibleNeighbors = neighbors
			.sort((a, b) => b.strength - a.strength)
			.slice(0, maxNeighbors);
		const visibleIds = new Set([selectedNode.id, ...visibleNeighbors.map((n) => n.id)]);

		const radius = Math.min(width, svgHeight) * 0.36;
		// eslint-disable-next-line svelte/prefer-svelte-reactivity
		const nodePositions = new Map<string, { x: number; y: number }>();
		nodePositions.set(selectedNode.id, { x: centerX, y: centerY });
		visibleNeighbors.forEach((n, i) => {
			const angle = (2 * Math.PI * i) / visibleNeighbors.length - Math.PI / 2;
			nodePositions.set(n.id, {
				x: centerX + radius * Math.cos(angle),
				y: centerY + radius * Math.sin(angle)
			});
		});

		const visibleEdges = egoData.edges.filter(
			(e) => visibleIds.has(e.source) && visibleIds.has(e.target)
		);
		const maxWeight = Math.max(...visibleEdges.map((e) => e.weight), 1);

		const edges: RenderEdge[] = [];
		for (const edge of visibleEdges) {
			const from = nodePositions.get(edge.source);
			const to = nodePositions.get(edge.target);
			if (!from || !to) continue;

			const color = edgeTypeColors[edge.type] || 'var(--muted-foreground)';
			const strokeWidth = 1 + (edge.weight / maxWeight) * 3;
			const isDirected = DIRECTED_EDGE_TYPES.has(edge.type);

			let arrowPoints: string | undefined;
			if (isDirected) {
				const dx = to.x - from.x;
				const dy = to.y - from.y;
				const len = Math.sqrt(dx * dx + dy * dy);
				if (len > 0) {
					const arrowSize = 6;
					const nodeRadius = 8;
					const mx = to.x - (dx / len) * (nodeRadius + 2);
					const my = to.y - (dy / len) * (nodeRadius + 2);
					const ux = dx / len;
					const uy = dy / len;
					const px = -uy;
					const py = ux;
					arrowPoints = [
						`${mx},${my}`,
						`${mx - ux * arrowSize + px * arrowSize * 0.5},${my - uy * arrowSize + py * arrowSize * 0.5}`,
						`${mx - ux * arrowSize - px * arrowSize * 0.5},${my - uy * arrowSize - py * arrowSize * 0.5}`
					].join(' ');
				}
			}

			edges.push({
				key: `${edge.source}-${edge.target}-${edge.type}`,
				x1: from.x,
				y1: from.y,
				x2: to.x,
				y2: to.y,
				color,
				strokeWidth,
				isDirected,
				arrowPoints
			});
		}

		const labelThreshold = visibleNeighbors[4]?.strength ?? 0;
		const renderNodes: RenderNode[] = visibleNeighbors.map((node) => {
			const pos = nodePositions.get(node.id)!;
			const color = entityTypeColors[node.type]?.color || '#888';
			const size = 5 + Math.min(node.strength / 10, 8);
			const showLabel = visibleNeighbors.length <= 15 || node.strength >= labelThreshold;
			const label = node.label.length > 20 ? node.label.slice(0, 18) + '...' : node.label;
			return { id: node.id, x: pos.x, y: pos.y, size, color, label, showLabel, node };
		});

		return {
			width,
			centerX,
			centerY,
			centerColor: entityTypeColors[selectedNode.type]?.color || '#888',
			centerLabel:
				selectedNode.label.length > 25
					? selectedNode.label.slice(0, 23) + '...'
					: selectedNode.label,
			edges,
			nodes: renderNodes
		};
	});

	// Icon map for display
	const iconMap: Record<string, typeof Users> = {
		person: Users,
		organization: Building2,
		event: Calendar,
		subject: Tag,
		location: MapPin,
		authority: BookMarked
	};
</script>

<div class="space-y-4">
	<!-- Ego Network SVG -->
	<div bind:clientWidth={containerWidth} class="w-full overflow-hidden rounded-lg border bg-card">
		{#if layout}
			<svg
				class="h-[350px] w-full"
				viewBox="0 0 {layout.width} {svgHeight}"
				width={layout.width}
				height={svgHeight}
			>
				{#each layout.edges as edge (edge.key)}
					<line
						x1={edge.x1}
						y1={edge.y1}
						x2={edge.x2}
						y2={edge.y2}
						stroke={edge.color}
						stroke-width={edge.strokeWidth}
						stroke-opacity="0.5"
					/>
					{#if edge.isDirected && edge.arrowPoints}
						<polygon points={edge.arrowPoints} fill={edge.color} opacity="0.6" />
					{/if}
				{/each}

				{#each layout.nodes as renderNode (renderNode.id)}
					<circle
						class="ego-node-circle cursor-pointer"
						cx={renderNode.x}
						cy={renderNode.y}
						r={renderNode.size}
						fill={renderNode.color}
						stroke="var(--background)"
						stroke-width="1.5"
						role="button"
						tabindex="0"
						aria-label={renderNode.node.label}
						onclick={() => onNodeClick?.(renderNode.node)}
						onkeydown={(e) => {
							if (e.key === 'Enter' || e.key === ' ') {
								e.preventDefault();
								onNodeClick?.(renderNode.node);
							}
						}}
					/>
					{#if renderNode.showLabel}
						<text
							class="pointer-events-none"
							x={renderNode.x}
							y={renderNode.y + renderNode.size + 12}
							text-anchor="middle"
							fill="var(--foreground)"
							font-size="10"
						>
							{renderNode.label}
						</text>
					{/if}
				{/each}

				<!-- Center node -->
				<circle
					cx={layout.centerX}
					cy={layout.centerY}
					r="18"
					fill={layout.centerColor}
					stroke="var(--foreground)"
					stroke-width="3"
				/>
				<text
					class="pointer-events-none"
					x={layout.centerX}
					y={layout.centerY + 30}
					text-anchor="middle"
					fill="var(--foreground)"
					font-size="12"
					font-weight="bold"
				>
					{layout.centerLabel}
				</text>
			</svg>
		{:else}
			<div class="h-[350px]"></div>
		{/if}
	</div>

	<!-- Connection list grouped by edge type -->
	<div class="max-h-[400px] space-y-3 overflow-y-auto">
		{#each [...egoData.byType.entries()] as [edgeType, connections] (edgeType)}
			<div>
				<div class="mb-1.5 flex items-center gap-2">
					<div
						class="h-2.5 w-2.5 rounded-full"
						style:background-color={edgeTypeColors[edgeType] || 'var(--muted-foreground)'}
					></div>
					<span class="text-xs font-medium text-muted-foreground">
						{t(edgeTypeLabels[edgeType] || edgeType)}
					</span>
					<Badge variant="outline" class="h-4 px-1 text-[10px]">{connections.length}</Badge>
				</div>
				<div class="space-y-1">
					{#each connections.slice(0, 10) as { node, edge } (node.id + edge.type)}
						{@const Icon = iconMap[node.type] || Tag}
						{@const nodeColor = entityTypeColors[node.type]?.color || '#888'}
						<button
							class="flex w-full items-center gap-2 rounded px-2 py-1 text-left text-sm transition-colors hover:bg-muted/50"
							onclick={() => onNodeClick?.(node)}
						>
							<span style:color={nodeColor}><Icon class="h-3.5 w-3.5 shrink-0" /></span>
							<span class="min-w-0 flex-1 truncate">{node.label}</span>
							{#if edge.weight > 1}
								<span class="shrink-0 text-xs text-muted-foreground">
									{edge.weight}
								</span>
							{/if}
						</button>
					{/each}
					{#if connections.length > 10}
						<p class="px-2 text-xs text-muted-foreground">
							+{connections.length - 10}
							{t('common.more')}
						</p>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</div>

<style>
	.ego-node-circle {
		transition:
			r 0.15s ease,
			stroke-width 0.15s ease;
	}
	.ego-node-circle:hover,
	.ego-node-circle:focus-visible {
		stroke-width: 2.5;
		outline: none;
	}
</style>

<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { browser } from '$app/environment';
	import type { GlobalNetworkNode, GlobalNetworkEdge, EntityType } from '$lib/types/network.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import {
		Users,
		Building2,
		Calendar,
		Tag,
		MapPin,
		BookMarked,
		ArrowRight,
		ExternalLink
	} from '@lucide/svelte';

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

	let {
		selectedNode,
		allNodes,
		allEdges,
		entityTypeColors,
		edgeTypeColors,
		onNodeClick
	}: Props = $props();

	let svgContainer: SVGSVGElement | null = $state(null);
	let containerDiv: HTMLDivElement | null = $state(null);
	const lang = $derived(languageStore.current);

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
		const neighborIds = new Set<string>();
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
		const byType = new Map<string, Array<{ node: GlobalNetworkNode; edge: GlobalNetworkEdge }>>();
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

	// Draw the D3 ego network
	$effect(() => {
		if (!browser || !svgContainer || !containerDiv || !egoData) return;
		const _ = lang; // reactive dependency

		drawEgoNetwork();
	});

	function drawEgoNetwork() {
		if (!svgContainer || !containerDiv) return;

		const width = containerDiv.clientWidth;
		const height = 350;
		const centerX = width / 2;
		const centerY = height / 2;

		// Clear previous
		while (svgContainer.firstChild) {
			svgContainer.removeChild(svgContainer.firstChild);
		}
		svgContainer.setAttribute('viewBox', `0 0 ${width} ${height}`);
		svgContainer.setAttribute('width', String(width));
		svgContainer.setAttribute('height', String(height));

		const neighbors = egoData.nodes.filter((n) => n.id !== selectedNode.id);
		if (neighbors.length === 0) return;

		// Limit visible neighbors for readability
		const maxNeighbors = Math.min(neighbors.length, 30);
		const visibleNeighbors = neighbors
			.sort((a, b) => b.strength - a.strength)
			.slice(0, maxNeighbors);
		const visibleIds = new Set([selectedNode.id, ...visibleNeighbors.map((n) => n.id)]);

		// Position neighbors in a circle around center
		const radius = Math.min(width, height) * 0.36;
		const nodePositions = new Map<string, { x: number; y: number }>();
		nodePositions.set(selectedNode.id, { x: centerX, y: centerY });

		visibleNeighbors.forEach((node, i) => {
			const angle = (2 * Math.PI * i) / visibleNeighbors.length - Math.PI / 2;
			nodePositions.set(node.id, {
				x: centerX + radius * Math.cos(angle),
				y: centerY + radius * Math.sin(angle)
			});
		});

		// SVG namespace
		const ns = 'http://www.w3.org/2000/svg';

		// Draw edges
		const visibleEdges = egoData.edges.filter(
			(e) => visibleIds.has(e.source) && visibleIds.has(e.target)
		);

		const maxWeight = Math.max(...visibleEdges.map((e) => e.weight), 1);

		for (const edge of visibleEdges) {
			const from = nodePositions.get(edge.source);
			const to = nodePositions.get(edge.target);
			if (!from || !to) continue;

			const line = document.createElementNS(ns, 'line');
			line.setAttribute('x1', String(from.x));
			line.setAttribute('y1', String(from.y));
			line.setAttribute('x2', String(to.x));
			line.setAttribute('y2', String(to.y));

			const edgeColor = edgeTypeColors[edge.type] || 'var(--muted-foreground)';
			const strokeWidth = 1 + (edge.weight / maxWeight) * 3;

			line.setAttribute('stroke', edgeColor);
			line.setAttribute('stroke-width', String(strokeWidth));
			line.setAttribute('stroke-opacity', '0.5');
			svgContainer.appendChild(line);

			// Directed edge arrow for directed types
			const directedTypes = ['part_of', 'has_part', 'located_in', 'succeeded_by'];
			if (directedTypes.includes(edge.type)) {
				const dx = to.x - from.x;
				const dy = to.y - from.y;
				const len = Math.sqrt(dx * dx + dy * dy);
				if (len > 0) {
					const arrowSize = 6;
					const nodeRadius = 8;
					// Position arrow at edge of target node
					const mx = to.x - (dx / len) * (nodeRadius + 2);
					const my = to.y - (dy / len) * (nodeRadius + 2);
					const ux = dx / len;
					const uy = dy / len;
					const px = -uy;
					const py = ux;

					const arrow = document.createElementNS(ns, 'polygon');
					const points = [
						`${mx},${my}`,
						`${mx - ux * arrowSize + px * arrowSize * 0.5},${my - uy * arrowSize + py * arrowSize * 0.5}`,
						`${mx - ux * arrowSize - px * arrowSize * 0.5},${my - uy * arrowSize - py * arrowSize * 0.5}`
					].join(' ');
					arrow.setAttribute('points', points);
					arrow.setAttribute('fill', edgeColor);
					arrow.setAttribute('opacity', '0.6');
					svgContainer.appendChild(arrow);
				}
			}
		}

		// Draw neighbor nodes
		for (const node of visibleNeighbors) {
			const pos = nodePositions.get(node.id);
			if (!pos) continue;

			const config = entityTypeColors[node.type];
			const nodeColor = config?.color || '#888';
			const nodeSize = 5 + Math.min(node.strength / 10, 8);

			// Node circle
			const circle = document.createElementNS(ns, 'circle');
			circle.setAttribute('cx', String(pos.x));
			circle.setAttribute('cy', String(pos.y));
			circle.setAttribute('r', String(nodeSize));
			circle.setAttribute('fill', nodeColor);
			circle.setAttribute('stroke', 'var(--background)');
			circle.setAttribute('stroke-width', '1.5');
			circle.setAttribute('class', 'cursor-pointer');
			circle.style.transition = 'r 0.15s';

			circle.addEventListener('mouseenter', () => {
				circle.setAttribute('r', String(nodeSize + 3));
				circle.setAttribute('stroke-width', '2.5');
			});
			circle.addEventListener('mouseleave', () => {
				circle.setAttribute('r', String(nodeSize));
				circle.setAttribute('stroke-width', '1.5');
			});
			circle.addEventListener('click', () => {
				onNodeClick?.(node);
			});

			svgContainer.appendChild(circle);

			// Label (only for top neighbors or if few)
			if (visibleNeighbors.length <= 15 || node.strength >= visibleNeighbors[4]?.strength) {
				const text = document.createElementNS(ns, 'text');
				text.setAttribute('x', String(pos.x));
				text.setAttribute('y', String(pos.y + nodeSize + 12));
				text.setAttribute('text-anchor', 'middle');
				text.setAttribute('fill', 'var(--foreground)');
				text.setAttribute('font-size', '10');
				text.setAttribute('class', 'pointer-events-none');

				const label = node.label.length > 20 ? node.label.slice(0, 18) + '...' : node.label;
				text.textContent = label;
				svgContainer.appendChild(text);
			}
		}

		// Draw center node (selected)
		const centerCircle = document.createElementNS(ns, 'circle');
		centerCircle.setAttribute('cx', String(centerX));
		centerCircle.setAttribute('cy', String(centerY));
		centerCircle.setAttribute('r', '18');

		const centerConfig = entityTypeColors[selectedNode.type];
		centerCircle.setAttribute('fill', centerConfig?.color || '#888');
		centerCircle.setAttribute('stroke', 'var(--foreground)');
		centerCircle.setAttribute('stroke-width', '3');
		svgContainer.appendChild(centerCircle);

		// Center label
		const centerText = document.createElementNS(ns, 'text');
		centerText.setAttribute('x', String(centerX));
		centerText.setAttribute('y', String(centerY + 30));
		centerText.setAttribute('text-anchor', 'middle');
		centerText.setAttribute('fill', 'var(--foreground)');
		centerText.setAttribute('font-size', '12');
		centerText.setAttribute('font-weight', 'bold');
		centerText.setAttribute('class', 'pointer-events-none');
		centerText.textContent =
			selectedNode.label.length > 25
				? selectedNode.label.slice(0, 23) + '...'
				: selectedNode.label;
		svgContainer.appendChild(centerText);
	}

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
	<div bind:this={containerDiv} class="w-full overflow-hidden rounded-lg border bg-card">
		<svg bind:this={svgContainer} class="h-[350px] w-full"></svg>
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
							+{connections.length - 10} {t('common.more')}
						</p>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</div>

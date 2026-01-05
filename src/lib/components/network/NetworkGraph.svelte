<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { browser } from '$app/environment';
	import type { GlobalNetworkNode, GlobalNetworkEdge, NodeSizeBy, EntityType } from '$lib/types/network.js';
	import { t } from '$lib/stores/translationStore.svelte.js';

	interface EntityTypeConfig {
		label: string;
		color: string;
		icon: any;
	}

	interface Props {
		nodes: GlobalNetworkNode[];
		edges: GlobalNetworkEdge[];
		selectedNodeId?: string | null;
		nodeSizeBy?: NodeSizeBy;
		entityTypeColors?: Record<EntityType, EntityTypeConfig>;
		onNodeClick?: (node: GlobalNetworkNode | null) => void;
		onNodeHover?: (node: GlobalNetworkNode | null) => void;
	}

	let {
		nodes = [],
		edges = [],
		selectedNodeId = null,
		nodeSizeBy = 'strength',
		entityTypeColors,
		onNodeClick,
		onNodeHover
	}: Props = $props();

	let containerElement: HTMLDivElement | null = $state(null);
	let sigmaInstance: any = $state(null);
	let graphInstance: any = $state(null);
	let isLayoutRunning = $state(false);
	let layoutProgress = $state(0);
	let isInitialized = $state(false);
	let currentNodesKey = $state('');
	
	// Cache layout positions to reuse when nodes reappear
	let positionCache: Map<string, { x: number; y: number }> = new Map();

	// Default colors per entity type
	const defaultColors: Record<EntityType, string> = {
		person: '#3b82f6',
		organization: '#8b5cf6',
		event: '#f97316',
		subject: '#22c55e',
		location: '#ec4899'
	};

	function getNodeColor(type: EntityType): string {
		return entityTypeColors?.[type]?.color ?? defaultColors[type] ?? '#666666';
	}

	// Calculate node sizes based on selected metric
	const nodeSizes = $derived.by(() => {
		const sizes: Record<string, number> = {};
		let maxValue = 1;

		for (const node of nodes) {
			const value =
				nodeSizeBy === 'count'
					? node.count
					: nodeSizeBy === 'degree'
						? node.degree
						: node.strength;
			sizes[node.id] = value;
			if (value > maxValue) maxValue = value;
		}

		// Normalize to 4-20 range (smaller for better performance)
		for (const id in sizes) {
			sizes[id] = 4 + (sizes[id] / maxValue) * 16;
		}

		return sizes;
	});

	// Create a stable key for the current node set (use length + hash for perf)
	const nodesKey = $derived(() => {
		if (nodes.length === 0) return '';
		// Create a lighter-weight key using length and a sample of IDs
		const ids = nodes.map((n) => n.id);
		const sample = [ids[0], ids[Math.floor(ids.length / 2)], ids[ids.length - 1]].join('|');
		return `${nodes.length}:${sample}`;
	});

	async function initGraph() {
		if (!browser || !containerElement) return;
		if (nodes.length === 0) return;

		// If same nodes, just update attributes instead of rebuilding
		if (isInitialized && sigmaInstance && graphInstance && currentNodesKey === nodesKey()) {
			updateGraphAttributes();
			return;
		}

		const container = containerElement;
		const rect = container.getBoundingClientRect();
		if (rect.width === 0 || rect.height === 0) {
			requestAnimationFrame(() => initGraph());
			return;
		}

		// Cleanup existing
		if (sigmaInstance) {
			sigmaInstance.kill();
			sigmaInstance = null;
			graphInstance = null;
		}

		isLayoutRunning = true;
		layoutProgress = 0;

		try {
			const [graphologyModule, { default: Sigma }, forceAtlas2Module] = await Promise.all([
				import('graphology'),
				import('sigma'),
				import('graphology-layout-forceatlas2')
			]);

			const Graph = graphologyModule.default || graphologyModule;
			const forceAtlas2 = forceAtlas2Module;

			const graph = new (Graph as any)();
			graphInstance = graph;

			// Build node lookup
			const nodeById: Record<string, GlobalNetworkNode> = {};
			for (const node of nodes) {
				nodeById[node.id] = node;
			}

			// Check how many nodes have cached positions
			let cachedCount = 0;
			for (const node of nodes) {
				if (positionCache.has(node.id)) cachedCount++;
			}
			const hasMostlyCachedPositions = cachedCount > nodes.length * 0.5;

			// Add nodes - use cached positions when available
			for (const node of nodes) {
				const cached = positionCache.get(node.id);
				graph.addNode(node.id, {
					label: node.label,
					x: cached?.x ?? Math.random() * 100,
					y: cached?.y ?? Math.random() * 100,
					size: nodeSizes[node.id] || 8,
					color: getNodeColor(node.type),
					// Don't use 'type' as Sigma reserves it for rendering programs
					entityType: node.type,
					nodeData: node
				});
			}

			// Add edges
			for (const edge of edges) {
				if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
					try {
						graph.addEdge(edge.source, edge.target, {
							weight: edge.weight,
							size: 0.5 + edge.weightNorm * 2,
							color: '#a3a3a380',
							edgeData: edge
						});
					} catch {
						// Edge may already exist (multigraph issue)
					}
				}
			}

			// Run layout - use fewer iterations if we have cached positions
			const nodeCount = nodes.length;
			const baseIterations = Math.min(100, Math.max(50, 150 - nodeCount));
			const iterations = hasMostlyCachedPositions ? Math.min(20, baseIterations) : baseIterations;
			
			layoutProgress = 10;
			await tick();

			(forceAtlas2 as any).assign(graph, {
				iterations,
				settings: {
					gravity: 0.3,
					scalingRatio: nodeCount > 100 ? 80 : 40,
					strongGravityMode: false,
					slowDown: hasMostlyCachedPositions ? 10 : 3, // Slow down more if using cached positions
					barnesHutOptimize: nodeCount > 30,
					barnesHutTheta: 0.6,
					edgeWeightInfluence: 0.5,
					linLogMode: true,
					outboundAttractionDistribution: true
				}
			});

			// Cache the computed positions
			graph.forEachNode((nodeId: string, attrs: { x: number; y: number }) => {
				positionCache.set(nodeId, { x: attrs.x, y: attrs.y });
			});

			layoutProgress = 80;
			await tick();

			// Get theme-aware colors
			const isDark = document.documentElement.classList.contains('dark');
			const foregroundColor = isDark ? '#fafafa' : '#171717';
			const mutedColor = isDark ? '#a3a3a3' : '#737373';

			sigmaInstance = new Sigma(graph, container, {
				renderEdgeLabels: false,
				allowInvalidContainer: true,
				defaultEdgeColor: mutedColor + '60',
				labelColor: { color: foregroundColor },
				labelFont: 'system-ui, sans-serif',
				labelSize: 11,
				labelWeight: '500',
				labelRenderedSizeThreshold: 6,
				zIndex: true,
				nodeReducer: (node, data) => {
					const isSelected = node === selectedNodeId;
					const isNeighbor = selectedNodeId && graph.hasEdge(node, selectedNodeId);

					if (selectedNodeId) {
						if (isSelected) {
							return { ...data, size: data.size * 1.4, zIndex: 2, highlighted: true };
						} else if (isNeighbor) {
							return { ...data, zIndex: 1 };
						} else {
							return { ...data, color: data.color + '40', size: data.size * 0.8, zIndex: 0 };
						}
					}
					return data;
				},
				edgeReducer: (edge, data) => {
					if (selectedNodeId) {
						const [source, target] = graph.extremities(edge);
						if (source === selectedNodeId || target === selectedNodeId) {
							return { ...data, color: '#f9731690', size: data.size * 2 };
						} else {
							return { ...data, color: '#a3a3a320', size: data.size * 0.5 };
						}
					}
					return data;
				}
			});

			// Event handlers
			sigmaInstance.on('clickNode', ({ node }: { node: string }) => {
				const nodeData = graph.getNodeAttribute(node, 'nodeData') as GlobalNetworkNode;
				onNodeClick?.(nodeData);
			});

			sigmaInstance.on('clickStage', () => {
				onNodeClick?.(null);
			});

			sigmaInstance.on('enterNode', ({ node }: { node: string }) => {
				const nodeData = graph.getNodeAttribute(node, 'nodeData') as GlobalNetworkNode;
				onNodeHover?.(nodeData);
				container.style.cursor = 'pointer';
			});

			sigmaInstance.on('leaveNode', () => {
				onNodeHover?.(null);
				container.style.cursor = 'default';
			});

			currentNodesKey = nodesKey();
			isInitialized = true;
			layoutProgress = 100;
		} catch (error) {
			console.error('Failed to initialize Sigma graph:', error);
		} finally {
			isLayoutRunning = false;
		}
	}

	function updateGraphAttributes() {
		if (!graphInstance || !sigmaInstance) return;

		// Update node sizes and colors
		for (const node of nodes) {
			if (graphInstance.hasNode(node.id)) {
				graphInstance.setNodeAttribute(node.id, 'size', nodeSizes[node.id] || 8);
				graphInstance.setNodeAttribute(node.id, 'color', getNodeColor(node.type));
			}
		}
		sigmaInstance.refresh();
	}

	// Re-render when selection changes
	$effect(() => {
		const _ = selectedNodeId;
		if (sigmaInstance && graphInstance) {
			sigmaInstance.refresh();
		}
	});

	// Rebuild graph when nodes change significantly
	$effect(() => {
		if (browser && containerElement && nodes.length > 0) {
			// Access nodesKey to track it
			const currentKey = nodesKey();
			// Debounce rebuilds - longer delay to batch rapid filter changes
			const timeout = setTimeout(() => {
				if (currentKey !== currentNodesKey) {
					initGraph();
				} else {
					updateGraphAttributes();
				}
			}, 300);
			return () => clearTimeout(timeout);
		}
	});

	onMount(() => {
		if (containerElement && nodes.length > 0) {
			initGraph();
		}

		return () => {
			if (sigmaInstance) {
				sigmaInstance.kill();
				sigmaInstance = null;
			}
		};
	});

	export function resetCamera() {
		sigmaInstance?.getCamera()?.animatedReset();
	}

	export function zoomIn() {
		sigmaInstance?.getCamera()?.animatedZoom({ duration: 200 });
	}

	export function zoomOut() {
		sigmaInstance?.getCamera()?.animatedUnzoom({ duration: 200 });
	}

	export function focusNode(nodeId: string) {
		if (!sigmaInstance || !graphInstance) return;
		const pos = sigmaInstance.getNodeDisplayData(nodeId);
		if (pos) {
			sigmaInstance.getCamera().animate({ x: pos.x, y: pos.y, ratio: 0.3 }, { duration: 400 });
		}
	}
</script>

<div class="relative h-full w-full">
	<div bind:this={containerElement} class="h-full w-full rounded-lg bg-card border"></div>
	{#if isLayoutRunning}
		<div class="absolute inset-0 flex items-center justify-center rounded-lg bg-background/80">
			<div class="text-center">
				<div class="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
				<p class="mt-2 text-sm text-muted-foreground">
					{t('network.computing_layout')} {layoutProgress}%
				</p>
			</div>
		</div>
	{/if}
</div>

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
		focusMode?: boolean;
		onNodeClick?: (node: GlobalNetworkNode | null) => void;
		onNodeHover?: (node: GlobalNetworkNode | null) => void;
	}

	let {
		nodes = [],
		edges = [],
		selectedNodeId = null,
		nodeSizeBy = 'strength',
		entityTypeColors,
		focusMode = false,
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
	let isDestroyed = false; // Track if component is unmounted
	let initRetryCount = 0;
	const MAX_INIT_RETRIES = 3;

	// Cache layout positions to reuse when nodes reappear
	let positionCache: Map<string, { x: number; y: number }> = new Map();

	// Default colors per entity type
	const defaultColors: Record<EntityType, string> = {
		person: '#3b82f6',
		organization: '#8b5cf6',
		event: '#f97316',
		subject: '#22c55e',
		location: '#ec4899',
		topic: '#22c55e',
		article: '#3b82f6',
		author: '#3b82f6'
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

	// Create a stable key for the current node set (use Set for O(1) lookups)
	const nodesKey = $derived.by(() => {
		if (nodes.length === 0) return '';
		// Use a simple hash: length + sum of first chars of IDs
		let hash = nodes.length;
		for (let i = 0; i < Math.min(nodes.length, 20); i++) {
			hash = (hash * 31 + nodes[i].id.charCodeAt(0)) | 0;
		}
		return `${nodes.length}:${hash}`;
	});

	async function initGraph() {
		if (!browser || !containerElement || isDestroyed) return;
		if (nodes.length === 0) return;

		// If same nodes, just update attributes instead of rebuilding
		if (isInitialized && sigmaInstance && graphInstance && currentNodesKey === nodesKey) {
			updateGraphAttributes();
			return;
		}

		const container = containerElement;

		// Ensure container is in the DOM and has dimensions
		if (!container.isConnected) {
			if (initRetryCount < MAX_INIT_RETRIES) {
				initRetryCount++;
				setTimeout(() => initGraph(), 100 * initRetryCount);
			}
			return;
		}

		const rect = container.getBoundingClientRect();
		if (rect.width === 0 || rect.height === 0) {
			if (initRetryCount < MAX_INIT_RETRIES) {
				initRetryCount++;
				requestAnimationFrame(() => initGraph());
			}
			return;
		}

		// Reset retry count on successful dimension check
		initRetryCount = 0;

		// Cleanup existing instance properly
		if (sigmaInstance) {
			try {
				sigmaInstance.kill();
			} catch {
				// Ignore cleanup errors
			}
			sigmaInstance = null;
			graphInstance = null;
			// Small delay to let WebGL context be released
			await new Promise((resolve) => setTimeout(resolve, 50));
		}

		// Check again if destroyed during async operation
		if (isDestroyed) return;

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
			// Skip layout entirely if we have most positions cached
			const skipLayout = cachedCount > nodes.length * 0.8;
			const hasMostlyCachedPositions = cachedCount > nodes.length * 0.5;

			// Get theme colors BEFORE adding nodes/edges
			const isDark = document.documentElement.classList.contains('dark');
			const edgeColor = isDark ? 'rgba(200, 200, 200, 0.35)' : 'rgba(80, 80, 80, 0.4)';

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

			// Add edges with theme-aware colors
			for (const edge of edges) {
				if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
					try {
						graph.addEdge(edge.source, edge.target, {
							weight: edge.weight,
							size: 0.8 + edge.weightNorm * 3,
							color: edgeColor,
							edgeData: edge
						});
					} catch {
						// Edge may already exist (multigraph issue)
					}
				}
			}

			// Run layout - skip entirely if we have cached positions for most nodes
			const nodeCount = nodes.length;
			
			layoutProgress = 10;

			if (!skipLayout) {
				const baseIterations = Math.min(80, Math.max(30, 120 - nodeCount));
				const iterations = hasMostlyCachedPositions ? Math.min(10, baseIterations) : baseIterations;

				(forceAtlas2 as any).assign(graph, {
					iterations,
					settings: {
						gravity: 0.3,
						scalingRatio: nodeCount > 100 ? 80 : 40,
						strongGravityMode: false,
						slowDown: hasMostlyCachedPositions ? 15 : 3,
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
			}

			layoutProgress = 80;
			await tick();

			// Check if destroyed during layout
			if (isDestroyed || !containerElement?.isConnected) {
				isLayoutRunning = false;
				return;
			}

			// Verify container is still valid and has dimensions
			const containerRect = container.getBoundingClientRect();
			if (!container.isConnected || containerRect.width === 0 || containerRect.height === 0) {
				isLayoutRunning = false;
				return;
			}

			// Theme-aware label and edge colors
			const foregroundColor = isDark ? '#fafafa' : '#0a0a0a';
			const defaultEdgeColor = isDark ? 'rgba(180, 180, 180, 0.3)' : 'rgba(60, 60, 60, 0.35)';

			sigmaInstance = new Sigma(graph, container, {
				renderEdgeLabels: false,
				allowInvalidContainer: true,
				defaultEdgeColor: defaultEdgeColor,
				labelColor: { color: foregroundColor },
				labelFont: 'system-ui, sans-serif',
				labelSize: 12,
				labelWeight: '600',
				labelRenderedSizeThreshold: 5,
				zIndex: true,
				nodeReducer: (node, data) => {
					const isSelected = node === selectedNodeId;
					const isNeighbor = selectedNodeId && graph.hasEdge(node, selectedNodeId);

					// In focus mode, the ego network is already filtered at page level
					// Show all nodes at full visibility, highlight selected
					if (focusMode && selectedNodeId) {
						if (isSelected) {
							return { ...data, size: data.size * 1.4, zIndex: 2, highlighted: true };
						}
						// All other nodes (neighbors) at full visibility
						return { ...data, zIndex: 1 };
					}

					// Normal mode: dim non-connected nodes
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
					// In focus mode, show all edges prominently (ego network is pre-filtered)
					if (focusMode && selectedNodeId) {
						const [source, target] = graph.extremities(edge);
						if (source === selectedNodeId || target === selectedNodeId) {
							const highlightColor = isDark ? 'rgba(249, 115, 22, 0.8)' : 'rgba(234, 88, 12, 0.9)';
							return { ...data, color: highlightColor, size: data.size * 2.5 };
						}
						// Other edges in focus mode (between neighbors) shown normally
						return data;
					}

					// Normal mode: highlight edges to selected, hide others completely
					if (selectedNodeId) {
						const [source, target] = graph.extremities(edge);
						if (source === selectedNodeId || target === selectedNodeId) {
							const highlightColor = isDark ? 'rgba(249, 115, 22, 0.8)' : 'rgba(234, 88, 12, 0.9)';
							return { ...data, color: highlightColor, size: data.size * 2.5 };
						} else {
							// Hide non-connected edges completely to avoid hatched appearance
							return { ...data, hidden: true };
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

			currentNodesKey = nodesKey;
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

	// Re-render when selection or focus mode changes
	$effect(() => {
		const _ = selectedNodeId;
		const __ = focusMode;
		if (sigmaInstance && graphInstance) {
			sigmaInstance.refresh();
		}
	});

	// Rebuild graph when nodes change significantly
	$effect(() => {
		if (browser && containerElement && nodes.length > 0 && !isDestroyed) {
			// Access nodesKey to track it
			const currentKey = nodesKey;
			// Debounce rebuilds - longer delay to batch rapid filter changes
			const timeout = setTimeout(() => {
				if (!isDestroyed && currentKey !== currentNodesKey) {
					initGraph();
				} else if (!isDestroyed) {
					updateGraphAttributes();
				}
			}, 400);
			return () => clearTimeout(timeout);
		}
	});

	onMount(() => {
		isDestroyed = false;

		// Delay initial graph to ensure container is fully ready
		const initTimeout = setTimeout(() => {
			if (containerElement && nodes.length > 0 && !isDestroyed) {
				initGraph();
			}
		}, 50);

		return () => {
			isDestroyed = true;
			clearTimeout(initTimeout);
			if (sigmaInstance) {
				try {
					sigmaInstance.kill();
				} catch {
					// Ignore cleanup errors
				}
				sigmaInstance = null;
				graphInstance = null;
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

	/**
	 * Focus on a node and all its neighbors (ego network view)
	 * Calculates bounding box of node + neighbors and zooms to fit
	 */
	export function focusOnSelection(nodeId: string) {
		if (!sigmaInstance || !graphInstance) return;

		const graph = graphInstance;
		const sigma = sigmaInstance;

		// Get the selected node position
		const nodePos = sigma.getNodeDisplayData(nodeId);
		if (!nodePos) return;

		// Collect all positions: selected node + neighbors
		const positions: Array<{ x: number; y: number }> = [{ x: nodePos.x, y: nodePos.y }];

		// Get all neighbors
		const neighbors = graph.neighbors(nodeId);
		for (const neighborId of neighbors) {
			const neighborPos = sigma.getNodeDisplayData(neighborId);
			if (neighborPos) {
				positions.push({ x: neighborPos.x, y: neighborPos.y });
			}
		}

		// Calculate bounding box
		let minX = Infinity,
			minY = Infinity,
			maxX = -Infinity,
			maxY = -Infinity;

		for (const pos of positions) {
			minX = Math.min(minX, pos.x);
			minY = Math.min(minY, pos.y);
			maxX = Math.max(maxX, pos.x);
			maxY = Math.max(maxY, pos.y);
		}

		// Calculate center
		const centerX = (minX + maxX) / 2;
		const centerY = (minY + maxY) / 2;

		// Calculate ratio to fit all nodes with some padding
		const width = maxX - minX;
		const height = maxY - minY;
		const size = Math.max(width, height);

		// Determine zoom ratio - smaller ratio = more zoomed in
		// Add padding factor (0.6 means 60% of viewport used by content)
		let ratio = 0.15; // Default for single node or very tight cluster
		if (size > 0.01) {
			// Normalize based on graph size and add padding
			ratio = Math.min(0.8, Math.max(0.1, size * 1.5));
		}

		// Animate camera to focus on the ego network
		sigma.getCamera().animate(
			{
				x: centerX,
				y: centerY,
				ratio: ratio
			},
			{ duration: 400 }
		);
	}

	/**
	 * Check if a node exists in the current graph
	 */
	export function hasNode(nodeId: string): boolean {
		return graphInstance?.hasNode(nodeId) ?? false;
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

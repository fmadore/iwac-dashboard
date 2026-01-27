<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { browser } from '$app/environment';
	import type { GlobalNetworkNode, GlobalNetworkEdge, NodeSizeBy, EntityType } from '$lib/types/network.js';
	import { t } from '$lib/stores/translationStore.svelte.js';

	// Layout types
	export type LayoutType = 'force' | 'circular' | 'radial';

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
		layoutType?: LayoutType;
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
		layoutType = 'force',
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

	// Track hovered node for visual feedback
	let hoveredNodeId = $state<string | null>(null);

	// Tooltip state
	let tooltipVisible = $state(false);
	let tooltipX = $state(0);
	let tooltipY = $state(0);
	let tooltipNode = $state<GlobalNetworkNode | null>(null);
	let tooltipConnections = $state<Array<{ node: GlobalNetworkNode; weight: number }>>([]);

	// Fullscreen state
	let isFullscreen = $state(false);
	let wrapperElement: HTMLDivElement | null = $state(null);

	// Tooltip positioning with simple bounds checking
	const TOOLTIP_OFFSET = 15;

	// Compute tooltip style with bounds checking
	const tooltipStyle = $derived.by(() => {
		if (!containerElement) return '';

		const rect = containerElement.getBoundingClientRect();
		const containerWidth = rect.width;
		const containerHeight = rect.height;

		// Default: position to the right and above cursor
		let left = tooltipX + TOOLTIP_OFFSET;
		let top = tooltipY - TOOLTIP_OFFSET;
		let transformY = '-100%'; // Above cursor

		// If too close to right edge, flip to left of cursor
		if (left + 280 > containerWidth) {
			left = Math.max(10, tooltipX - TOOLTIP_OFFSET - 280);
		}

		// If too close to top, show below cursor instead
		if (top < 220) {
			top = tooltipY + TOOLTIP_OFFSET;
			transformY = '0';
		}

		// Clamp to container bounds
		left = Math.max(10, Math.min(left, containerWidth - 290));
		top = Math.max(10, Math.min(top, containerHeight - 10));

		return `left: ${left}px; top: ${top}px; transform: translateY(${transformY});`;
	});

	// Toggle fullscreen mode
	function toggleFullscreen() {
		if (!wrapperElement) return;

		if (!document.fullscreenElement) {
			wrapperElement.requestFullscreen().then(() => {
				isFullscreen = true;
			}).catch((err) => {
				console.error('Failed to enter fullscreen:', err);
			});
		} else {
			document.exitFullscreen().then(() => {
				isFullscreen = false;
			}).catch((err) => {
				console.error('Failed to exit fullscreen:', err);
			});
		}
	}

	// Listen for fullscreen changes (e.g., user presses Escape)
	$effect(() => {
		if (!browser) return;

		const handleFullscreenChange = () => {
			isFullscreen = !!document.fullscreenElement;
			// Refresh sigma when fullscreen changes to adjust to new dimensions
			if (sigmaInstance) {
				setTimeout(() => {
					sigmaInstance?.refresh();
				}, 100);
			}
		};

		document.addEventListener('fullscreenchange', handleFullscreenChange);
		return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
	});

	// Cache layout positions to reuse when nodes reappear
	let positionCache: Map<string, { x: number; y: number }> = new Map();

	// Get top connections for a node
	function getTopConnections(nodeId: string, limit: number = 5): Array<{ node: GlobalNetworkNode; weight: number }> {
		if (!nodeId) return [];

		const nodeMap = new Map(nodes.map(n => [n.id, n]));
		const connections: Array<{ node: GlobalNetworkNode; weight: number }> = [];

		for (const edge of edges) {
			let connectedId: string | null = null;
			if (edge.source === nodeId) {
				connectedId = edge.target;
			} else if (edge.target === nodeId) {
				connectedId = edge.source;
			}

			if (connectedId) {
				const connectedNode = nodeMap.get(connectedId);
				if (connectedNode) {
					connections.push({ node: connectedNode, weight: edge.weight });
				}
			}
		}

		// Sort by weight descending and take top N
		return connections
			.sort((a, b) => b.weight - a.weight)
			.slice(0, limit);
	}

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

	// Helper to lighten a color for border/halo effect
	function lightenColor(hex: string, percent: number): string {
		const num = parseInt(hex.replace('#', ''), 16);
		const amt = Math.round(2.55 * percent);
		const R = Math.min(255, (num >> 16) + amt);
		const G = Math.min(255, ((num >> 8) & 0x00ff) + amt);
		const B = Math.min(255, (num & 0x0000ff) + amt);
		return `#${((1 << 24) | (R << 16) | (G << 8) | B).toString(16).slice(1)}`;
	}

	// Helper to add alpha to hex color
	function hexToRgba(hex: string, alpha: number): string {
		const num = parseInt(hex.replace('#', ''), 16);
		const R = (num >> 16) & 0xff;
		const G = (num >> 8) & 0xff;
		const B = num & 0xff;
		return `rgba(${R}, ${G}, ${B}, ${alpha})`;
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

		// Normalize to 5-24 range (slightly larger for better visibility with borders)
		for (const id in sizes) {
			sizes[id] = 5 + (sizes[id] / maxValue) * 19;
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
			// Longer delay to ensure WebGL context is fully released
			await new Promise((resolve) => setTimeout(resolve, 150));
		}

		// Additional check - ensure container can create WebGL context
		const testCanvas = document.createElement('canvas');
		const testCtx = testCanvas.getContext('webgl2') || testCanvas.getContext('webgl');
		if (!testCtx) {
			console.error('WebGL not supported');
			isLayoutRunning = false;
			return;
		}

		// Check again if destroyed during async operation
		if (isDestroyed) return;

		isLayoutRunning = true;
		layoutProgress = 0;

		try {
			const [
				graphologyModule,
				{ default: Sigma },
				forceAtlas2Module,
				nodeBorderModule,
				edgeCurveModule
			] = await Promise.all([
				import('graphology'),
				import('sigma'),
				import('graphology-layout-forceatlas2'),
				import('@sigma/node-border'),
				import('@sigma/edge-curve')
			]);

			const Graph = graphologyModule.default || graphologyModule;
			const forceAtlas2 = forceAtlas2Module;
			const { createNodeBorderProgram } = nodeBorderModule;
			const EdgeCurveProgram = edgeCurveModule.default;

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
				const nodeColor = getNodeColor(node.type);
				graph.addNode(node.id, {
					label: node.label,
					x: cached?.x ?? Math.random() * 100,
					y: cached?.y ?? Math.random() * 100,
					size: nodeSizes[node.id] || 8,
					color: nodeColor,
					// Border attributes for @sigma/node-border
					borderColor: lightenColor(nodeColor, 30),
					borderSize: 0.15, // Relative to node size (15%)
					// Don't use 'type' as Sigma reserves it for rendering programs
					entityType: node.type,
					nodeData: node
				});
			}

			// Add edges with theme-aware colors and curvature
			for (const edge of edges) {
				if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
					try {
						graph.addEdge(edge.source, edge.target, {
							weight: edge.weight,
							size: 1 + edge.weightNorm * 4, // Slightly thicker edges
							color: edgeColor,
							// Label shows co-occurrence count (only visible when forceLabel is true)
							label: edge.weight > 1 ? `${edge.weight}` : '',
							// Curvature for edge-curve program (0 = straight, 0.25 = gentle curve)
							curvature: 0.2,
							edgeData: edge
						});
					} catch {
						// Edge may already exist (multigraph issue)
					}
				}
			}

			// Run layout based on layout type
			const nodeCount = nodes.length;

			layoutProgress = 10;

			// Apply layout based on type
			if (layoutType === 'circular') {
				// Circular layout - arrange nodes in a circle, grouped by entity type
				const entityTypes = [...new Set(nodes.map(n => n.type))];
				const nodesByType: Record<string, string[]> = {};

				graph.forEachNode((nodeId: string, attrs: any) => {
					const type = attrs.entityType || 'unknown';
					if (!nodesByType[type]) nodesByType[type] = [];
					nodesByType[type].push(nodeId);
				});

				// Arrange in a circle with type grouping
				let totalIndex = 0;
				const totalNodes = graph.order;
				const radius = Math.max(50, totalNodes * 2);

				for (const type of entityTypes) {
					const typeNodes = nodesByType[type] || [];
					for (const nodeId of typeNodes) {
						const angle = (totalIndex / totalNodes) * 2 * Math.PI - Math.PI / 2;
						graph.setNodeAttribute(nodeId, 'x', radius * Math.cos(angle));
						graph.setNodeAttribute(nodeId, 'y', radius * Math.sin(angle));
						totalIndex++;
					}
				}
			} else if (layoutType === 'radial' && selectedNodeId && graph.hasNode(selectedNodeId)) {
				// Radial layout - selected node in center, neighbors in concentric rings
				const centerNode = selectedNodeId;
				graph.setNodeAttribute(centerNode, 'x', 0);
				graph.setNodeAttribute(centerNode, 'y', 0);

				// Get neighbors at different distances
				const visited = new Set<string>([centerNode]);
				const rings: string[][] = [[]];

				// First ring: direct neighbors
				graph.forEachNeighbor(centerNode, (neighbor: string) => {
					if (!visited.has(neighbor)) {
						rings[0].push(neighbor);
						visited.add(neighbor);
					}
				});

				// Second ring: neighbors of neighbors
				rings.push([]);
				for (const nodeId of rings[0]) {
					graph.forEachNeighbor(nodeId, (neighbor: string) => {
						if (!visited.has(neighbor)) {
							rings[1].push(neighbor);
							visited.add(neighbor);
						}
					});
				}

				// Remaining nodes in outer ring
				rings.push([]);
				graph.forEachNode((nodeId: string) => {
					if (!visited.has(nodeId)) {
						rings[2].push(nodeId);
					}
				});

				// Position nodes in each ring
				const ringRadii = [60, 120, 180];
				for (let ringIndex = 0; ringIndex < rings.length; ringIndex++) {
					const ringNodes = rings[ringIndex];
					const radius = ringRadii[ringIndex] || 180 + ringIndex * 60;

					for (let i = 0; i < ringNodes.length; i++) {
						const angle = (i / ringNodes.length) * 2 * Math.PI - Math.PI / 2;
						graph.setNodeAttribute(ringNodes[i], 'x', radius * Math.cos(angle));
						graph.setNodeAttribute(ringNodes[i], 'y', radius * Math.sin(angle));
					}
				}
			} else if (!skipLayout) {
				// Force-directed layout (default)
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
			}

			// Cache the computed positions (for force layout)
			if (layoutType === 'force') {
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
			const defaultEdgeColor = isDark ? 'rgba(180, 180, 180, 0.35)' : 'rgba(80, 80, 80, 0.4)';

			// Custom hover halo/glow effect function
			const drawNodeHoverWithHalo = (
				context: CanvasRenderingContext2D,
				data: { x: number; y: number; size: number; label: string | null; color: string },
				settings: any
			) => {
				const { x, y, size, label, color } = data;

				// Parse the node color for the glow
				const glowColor = color || (isDark ? '#fbbf24' : '#f59e0b');

				// Draw multi-layer glow effect (outer to inner)
				const glowLayers = [
					{ radius: size + 12, opacity: 0.08 },
					{ radius: size + 8, opacity: 0.12 },
					{ radius: size + 5, opacity: 0.18 },
					{ radius: size + 3, opacity: 0.25 }
				];

				for (const layer of glowLayers) {
					context.beginPath();
					context.arc(x, y, layer.radius, 0, Math.PI * 2);
					context.fillStyle = hexToRgba(glowColor, layer.opacity);
					context.fill();
				}

				// Draw the label with background for better readability
				if (label) {
					const fontSize = settings.labelSize || 13;
					const fontWeight = settings.labelWeight || '600';
					const fontFamily = settings.labelFont || 'system-ui, -apple-system, sans-serif';

					context.font = `${fontWeight} ${fontSize}px ${fontFamily}`;
					const textWidth = context.measureText(label).width;

					// Label position (above the node)
					const labelX = x;
					const labelY = y - size - 8;

					// Draw label background
					const padding = 4;
					const bgColor = isDark ? 'rgba(10, 10, 10, 0.85)' : 'rgba(255, 255, 255, 0.9)';
					context.fillStyle = bgColor;
					context.beginPath();
					context.roundRect(
						labelX - textWidth / 2 - padding,
						labelY - fontSize / 2 - padding,
						textWidth + padding * 2,
						fontSize + padding * 2,
						4
					);
					context.fill();

					// Draw label border
					context.strokeStyle = hexToRgba(glowColor, 0.5);
					context.lineWidth = 1;
					context.stroke();

					// Draw label text
					context.fillStyle = foregroundColor;
					context.textAlign = 'center';
					context.textBaseline = 'middle';
					context.fillText(label, labelX, labelY);
				}
			};

			// Create custom node program with borders
			const NodeBorderProgramCustom = createNodeBorderProgram({
				borders: [
					{ size: { value: 0.15, mode: 'relative' }, color: { attribute: 'borderColor' } },
					{ size: { fill: true }, color: { attribute: 'color' } }
				]
			});

			sigmaInstance = new Sigma(graph, container, {
				// Use bordered nodes (node-image has rendering issues)
				defaultNodeType: 'bordered',
				nodeProgramClasses: {
					bordered: NodeBorderProgramCustom
				},
				defaultEdgeType: 'curve',
				edgeProgramClasses: {
					curve: EdgeCurveProgram
				},
				renderEdgeLabels: true,
				defaultEdgeColor: defaultEdgeColor,
				// Edge label styling
				edgeLabelFont: 'system-ui, -apple-system, sans-serif',
				edgeLabelSize: 11,
				edgeLabelWeight: '500',
				edgeLabelColor: { color: foregroundColor },
				// Custom hover effect with halo/glow
				defaultDrawNodeHover: drawNodeHoverWithHalo,
				// Label styling
				labelColor: { color: foregroundColor },
				labelFont: 'system-ui, -apple-system, sans-serif',
				labelSize: 13,
				labelWeight: '600',
				labelRenderedSizeThreshold: 6,
				// Enable z-index for proper layering
				zIndex: true,
				// Improved label rendering
				labelDensity: 0.12,
				labelGridCellSize: 100,
				// Node reducer for selection and hover effects
				nodeReducer: (node, data) => {
					const isSelected = node === selectedNodeId;
					const isHovered = node === hoveredNodeId;
					const isNeighbor = selectedNodeId && graph.hasEdge(node, selectedNodeId);
					const isHoveredNeighbor = hoveredNodeId && !selectedNodeId && graph.hasEdge(node, hoveredNodeId);

					// Hover effect (when no selection)
					if (isHovered && !selectedNodeId) {
						return {
							...data,
							size: data.size * 1.3,
							borderSize: 0.2,
							borderColor: lightenColor(data.color, 50),
							zIndex: 3,
							forceLabel: true
						};
					}

					// Highlight hovered neighbors
					if (isHoveredNeighbor && !selectedNodeId) {
						return {
							...data,
							size: data.size * 1.1,
							zIndex: 2,
							forceLabel: true
						};
					}

					// Dim non-hovered nodes when hovering
					if (hoveredNodeId && !selectedNodeId && !isHovered && !isHoveredNeighbor) {
						return {
							...data,
							color: hexToRgba(data.color, 0.3),
							borderColor: hexToRgba(data.borderColor || data.color, 0.2),
							zIndex: 0
						};
					}

					// In focus mode, the ego network is already filtered at page level
					if (focusMode && selectedNodeId) {
						if (isSelected) {
							return {
								...data,
								size: data.size * 1.5,
								borderSize: 0.25,
								borderColor: isDark ? '#fbbf24' : '#f59e0b',
								zIndex: 3,
								forceLabel: true
							};
						}
						return { ...data, zIndex: 1, forceLabel: true };
					}

					// Normal mode: dim non-connected nodes
					if (selectedNodeId) {
						if (isSelected) {
							return {
								...data,
								size: data.size * 1.5,
								borderSize: 0.25,
								borderColor: isDark ? '#fbbf24' : '#f59e0b',
								zIndex: 3,
								forceLabel: true
							};
						} else if (isNeighbor) {
							return {
								...data,
								size: data.size * 1.05,
								zIndex: 2,
								forceLabel: true
							};
						} else {
							return {
								...data,
								color: hexToRgba(data.color, 0.25),
								borderColor: hexToRgba(data.borderColor || data.color, 0.15),
								size: data.size * 0.75,
								zIndex: 0
							};
						}
					}

					return data;
				},
				// Edge reducer for selection and hover effects
				edgeReducer: (edge, data) => {
					const [source, target] = graph.extremities(edge);
					const isConnectedToHovered = hoveredNodeId && !selectedNodeId &&
						(source === hoveredNodeId || target === hoveredNodeId);
					const isConnectedToSelected = selectedNodeId &&
						(source === selectedNodeId || target === selectedNodeId);

					// Hover effect on edges - show label
					if (isConnectedToHovered) {
						const hoverEdgeColor = isDark ? 'rgba(251, 191, 36, 0.7)' : 'rgba(245, 158, 11, 0.8)';
						return { ...data, color: hoverEdgeColor, size: data.size * 2, forceLabel: true };
					}

					// Dim non-connected edges when hovering (no label)
					if (hoveredNodeId && !selectedNodeId && !isConnectedToHovered) {
						return { ...data, hidden: true };
					}

					// In focus mode, show all edges prominently with labels
					if (focusMode && selectedNodeId) {
						if (isConnectedToSelected) {
							const highlightColor = isDark ? 'rgba(251, 191, 36, 0.85)' : 'rgba(245, 158, 11, 0.9)';
							return { ...data, color: highlightColor, size: data.size * 2.5, forceLabel: true };
						}
						return { ...data, forceLabel: true }; // Show labels for all edges in focus mode
					}

					// Normal mode: highlight edges to selected with labels, hide others
					if (selectedNodeId) {
						if (isConnectedToSelected) {
							const highlightColor = isDark ? 'rgba(251, 191, 36, 0.85)' : 'rgba(245, 158, 11, 0.9)';
							return { ...data, color: highlightColor, size: data.size * 2.5, forceLabel: true };
						} else {
							return { ...data, hidden: true };
						}
					}

					// Default: hide edge labels to avoid clutter
					return { ...data, label: '' };
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
				hoveredNodeId = node;
				onNodeHover?.(nodeData);
				container.style.cursor = 'pointer';

				// Set tooltip data
				tooltipNode = nodeData;
				tooltipConnections = getTopConnections(node);
				tooltipVisible = true;

				// Refresh to apply hover effects
				sigmaInstance.refresh({ skipIndexation: true });
			});

			sigmaInstance.on('leaveNode', () => {
				hoveredNodeId = null;
				onNodeHover?.(null);
				container.style.cursor = 'default';

				// Hide tooltip
				tooltipVisible = false;
				tooltipNode = null;

				// Refresh to remove hover effects
				sigmaInstance.refresh({ skipIndexation: true });
			});

			// Track mouse position for tooltip
			container.addEventListener('mousemove', (e: MouseEvent) => {
				if (tooltipVisible) {
					const rect = container.getBoundingClientRect();
					tooltipX = e.clientX - rect.left;
					tooltipY = e.clientY - rect.top;
				}
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

		// Update node sizes, colors, and border colors
		for (const node of nodes) {
			if (graphInstance.hasNode(node.id)) {
				const nodeColor = getNodeColor(node.type);
				graphInstance.setNodeAttribute(node.id, 'size', nodeSizes[node.id] || 8);
				graphInstance.setNodeAttribute(node.id, 'color', nodeColor);
				graphInstance.setNodeAttribute(node.id, 'borderColor', lightenColor(nodeColor, 30));
			}
		}
		sigmaInstance.refresh();
	}

	// Re-render when selection, focus mode, or hover changes
	$effect(() => {
		const _ = selectedNodeId;
		const __ = focusMode;
		const ___ = hoveredNodeId;
		if (sigmaInstance && graphInstance) {
			sigmaInstance.refresh({ skipIndexation: true });
		}
	});

	// Track current layout type for change detection
	let currentLayoutType = $state<LayoutType>('force');

	// Rebuild graph when nodes change significantly or layout type changes
	$effect(() => {
		if (browser && containerElement && nodes.length > 0 && !isDestroyed) {
			// Access nodesKey and layoutType to track them
			const currentKey = nodesKey;
			const newLayoutType = layoutType;

			// Debounce rebuilds - longer delay to batch rapid filter changes
			const timeout = setTimeout(() => {
				if (!isDestroyed) {
					// Rebuild if nodes changed or layout type changed
					if (currentKey !== currentNodesKey || newLayoutType !== currentLayoutType) {
						currentLayoutType = newLayoutType;
						initGraph();
					} else {
						updateGraphAttributes();
					}
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

<div
	bind:this={wrapperElement}
	class="relative h-full w-full"
	class:fullscreen-wrapper={isFullscreen}
>
	<div bind:this={containerElement} class="h-full w-full rounded-lg bg-card border"></div>

	<!-- Fullscreen button -->
	<button
		onclick={toggleFullscreen}
		class="absolute top-2 right-2 z-40 flex h-[30px] w-[30px] items-center justify-center rounded-md border bg-background/80 text-muted-foreground backdrop-blur-sm transition-colors hover:bg-accent hover:text-accent-foreground"
		title={isFullscreen ? t('network.exit_fullscreen') : t('network.fullscreen')}
	>
		{#if isFullscreen}
			<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<polyline points="4 14 10 14 10 20"></polyline>
				<polyline points="20 10 14 10 14 4"></polyline>
				<line x1="14" y1="10" x2="21" y2="3"></line>
				<line x1="3" y1="21" x2="10" y2="14"></line>
			</svg>
		{:else}
			<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<polyline points="15 3 21 3 21 9"></polyline>
				<polyline points="9 21 3 21 3 15"></polyline>
				<line x1="21" y1="3" x2="14" y2="10"></line>
				<line x1="3" y1="21" x2="10" y2="14"></line>
			</svg>
		{/if}
	</button>

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

	<!-- Rich Tooltip -->
	{#if tooltipVisible && tooltipNode}
		{@const nodeColor = entityTypeColors?.[tooltipNode.type]?.color ?? getNodeColor(tooltipNode.type)}
		<div
			class="pointer-events-none absolute z-50 max-w-xs rounded-lg border bg-popover/95 p-3 text-popover-foreground shadow-lg backdrop-blur-sm"
			style={tooltipStyle}
		>
			<!-- Header -->
			<div class="mb-2 flex items-center gap-2">
				<div
					class="h-3 w-3 shrink-0 rounded-full"
					style="background-color: {nodeColor}"
				></div>
				<span class="font-semibold leading-tight">{tooltipNode.label}</span>
			</div>

			<!-- Type Badge -->
			<div
				class="mb-2 inline-block rounded px-1.5 py-0.5 text-xs font-medium"
				style="background-color: {nodeColor}20; color: {nodeColor}"
			>
				{entityTypeColors?.[tooltipNode.type]?.label ? t(entityTypeColors[tooltipNode.type].label) : tooltipNode.type}
			</div>

			<!-- Stats Grid -->
			<div class="mb-2 grid grid-cols-3 gap-2 text-center text-xs">
				<div class="rounded bg-muted px-1.5 py-1">
					<div class="font-bold">{tooltipNode.count}</div>
					<div class="text-muted-foreground">{t('network.articles')}</div>
				</div>
				<div class="rounded bg-muted px-1.5 py-1">
					<div class="font-bold">{tooltipNode.degree}</div>
					<div class="text-muted-foreground">{t('network.connections')}</div>
				</div>
				<div class="rounded bg-muted px-1.5 py-1">
					<div class="font-bold">{tooltipNode.strength}</div>
					<div class="text-muted-foreground">{t('network.strength')}</div>
				</div>
			</div>

			<!-- Top Connections -->
			{#if tooltipConnections.length > 0}
				<div class="border-t pt-2">
					<div class="mb-1 text-xs font-medium text-muted-foreground">{t('network.top_connections')}:</div>
					<div class="space-y-0.5">
						{#each tooltipConnections as conn (conn.node.id)}
							{@const connColor = entityTypeColors?.[conn.node.type]?.color ?? getNodeColor(conn.node.type)}
							<div class="flex items-center justify-between gap-2 text-xs">
								<div class="flex items-center gap-1.5 min-w-0">
									<div
										class="h-2 w-2 shrink-0 rounded-full"
										style="background-color: {connColor}"
									></div>
									<span class="truncate">{conn.node.label}</span>
								</div>
								<span class="shrink-0 text-muted-foreground">×{conn.weight}</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.fullscreen-wrapper {
		background-color: var(--background);
		padding: 1rem;
	}

	.fullscreen-wrapper :global(.rounded-lg) {
		border-radius: 0.5rem;
	}
</style>

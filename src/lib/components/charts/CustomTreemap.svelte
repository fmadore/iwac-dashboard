<script lang="ts">
	import { onDestroy } from 'svelte';
	import { scaleOrdinal } from 'd3-scale';
	import { select } from 'd3-selection';
	import { zoom, zoomIdentity } from 'd3-zoom';
	import { hierarchy, treemap, treemapBinary } from 'd3-hierarchy';
	import type { TreemapData, TreemapNode, TreemapConfig } from '$lib/types/treemap.js';

	// Props
	interface TreemapProps {
		data: TreemapData;
		width?: number;
		height?: number;
		config?: Partial<TreemapConfig>;
		onNodeClick?: (node: TreemapNode) => void;
		onNodeHover?: (node: TreemapNode | null) => void;
		selectedNode?: TreemapNode | null;
	}

	let {
		data,
		width = 800,
		height = 600,
		config = {},
		onNodeClick,
		onNodeHover,
		selectedNode = $bindable()
	}: TreemapProps = $props();

	// Default configuration using design system
	const defaultConfig: TreemapConfig = {
		padding: {
			inner: 2,
			outer: 4,
			top: 20,
			right: 2,
			bottom: 2,
			left: 2
		},
		tile: treemapBinary,
		round: true,
		colors: {
			scheme: [
				'var(--chart-1)',
				'var(--chart-2)', 
				'var(--chart-3)',
				'var(--chart-4)',
				'var(--chart-5)',
				'var(--primary)',
				'var(--secondary)',
				'var(--accent)'
			],
			background: 'var(--card)',
			border: 'var(--border)',
			text: 'var(--card-foreground)',
			textSecondary: 'var(--muted-foreground)'
		},
		animation: {
			duration: 750,
			ease: 'ease-in-out'
		},
		text: {
			minWidth: 60,
			minHeight: 30,
			fontSize: {
				title: 14,
				subtitle: 11,
				small: 9
			}
		},
		interaction: {
			hover: true,
			click: true,
			tooltip: true
		},
		zoom: {
			enabled: true,
			scaleExtent: [1, 10],
			resetOnDoubleClick: true
		}
	};

	// Merge config with defaults
	const mergedConfig = $derived(() => ({
		...defaultConfig,
		...config,
		padding: { ...defaultConfig.padding, ...config.padding },
		colors: { ...defaultConfig.colors, ...config.colors },
		animation: { ...defaultConfig.animation, ...config.animation },
		text: { 
			...defaultConfig.text, 
			...config.text,
			fontSize: { ...defaultConfig.text.fontSize, ...config.text?.fontSize }
		},
		interaction: { ...defaultConfig.interaction, ...config.interaction },
		zoom: { ...defaultConfig.zoom, ...config.zoom }
	}));

	// State
	let containerElement: HTMLDivElement;
	let svgElement: SVGSVGElement;
	let hoveredNode = $state<TreemapNode | null>(null);
	let tooltipData = $state<{ node: TreemapNode; x: number; y: number } | null>(null);
	let currentRoot = $state<TreemapNode | null>(null);
	let breadcrumbs = $state<TreemapNode[]>([]);
	let zoomBehavior: any = null;

	// Custom tiling function for zoom (based on Observable example)
	function tile(node: any, x0: number, y0: number, x1: number, y1: number) {
		treemapBinary(node, 0, 0, width, height);
		for (const child of node.children || []) {
			child.x0 = x0 + child.x0 / width * (x1 - x0);
			child.x1 = x0 + child.x1 / width * (x1 - x0);
			child.y0 = y0 + child.y0 / height * (y1 - y0);
			child.y1 = y0 + child.y1 / height * (y1 - y0);
		}
	}

	// Computed values
	const treemapLayout = $derived(() => {
		const layout = treemap<TreemapData>()
			.size([width, height])
			.tile(tile)
			.round(mergedConfig().round)
			.paddingInner(mergedConfig().padding.inner)
			.paddingOuter(mergedConfig().padding.outer)
			.paddingTop(mergedConfig().padding.top)
			.paddingRight(mergedConfig().padding.right)
			.paddingBottom(mergedConfig().padding.bottom)
			.paddingLeft(mergedConfig().padding.left);

		return layout;
	});

	const hierarchyData = $derived(() => {
		if (!data) return null;
		
		const root = hierarchy(data)
			.sum(d => d.value || 0)
			.sort((a, b) => (b.value || 0) - (a.value || 0));

		const layoutRoot = treemapLayout()(root);
		
		// Initialize currentRoot and breadcrumbs if not set
		if (!currentRoot && layoutRoot) {
			currentRoot = layoutRoot;
			breadcrumbs = [layoutRoot];
		}
		
		return layoutRoot;
	});

	const nodes = $derived(() => {
		if (!currentRoot) return [];
		
		// Show children of current root, or if no children, show the current root itself
		if (currentRoot.children && currentRoot.children.length > 0) {
			// Apply treemap layout to current root for proper positioning
			const localTreemap = treemap<TreemapData>()
				.size([width, height])
				.tile(tile)
				.round(mergedConfig().round)
				.paddingInner(mergedConfig().padding.inner)
				.paddingOuter(mergedConfig().padding.outer)
				.paddingTop(mergedConfig().padding.top)
				.paddingRight(mergedConfig().padding.right)
				.paddingBottom(mergedConfig().padding.bottom)
				.paddingLeft(mergedConfig().padding.left);
			
			// Create a copy for local layout
			const localRoot = hierarchy(currentRoot.data)
				.sum(d => d.value || 0)
				.sort((a, b) => (b.value || 0) - (a.value || 0));
			
			localTreemap(localRoot);
			return localRoot.children || [];
		} else {
			// Leaf node - show empty or current node
			return [];
		}
	});

	// Helper function to resolve CSS custom properties to actual color values
	function resolveCSSCustomProperty(value: string): string {
		if (value.startsWith('var(') && typeof window !== 'undefined' && document.documentElement) {
			const propName = value.slice(4, -1); // Remove 'var(' and ')'
			const computedStyle = getComputedStyle(document.documentElement);
			const resolvedValue = computedStyle.getPropertyValue(propName).trim();
			return resolvedValue || '#666';
		}
		return value;
	}

	// Color scale using design system
	const colorScale = $derived(() => {
		if (!hierarchyData()) return () => '#666';
		
		const rootNodes = hierarchyData()!.children || [];
		const colorScheme = mergedConfig().colors.scheme;
		
		// Resolve CSS custom properties to actual color values
		const resolvedColors = colorScheme.map(color => resolveCSSCustomProperty(color));
		
		// Create a scale mapping root-level categories to colors
		const categories = rootNodes.map(d => d.data.name);
		return scaleOrdinal(resolvedColors).domain(categories);
	});

	// Event handlers - PROPER DRILL-DOWN FUNCTIONALITY
	function handleNodeClick(node: TreemapNode, event: MouseEvent) {
		if (!mergedConfig().interaction.click) return;
		
		event.stopPropagation();
		
		// DRILL DOWN: If node has children, zoom into it
		if (node.children && node.children.length > 0) {
			drillDown(node);
		} else {
			// Leaf node - show selection
			selectedNode = selectedNode?.data.name === node.data.name ? null : node;
			onNodeClick?.(node);
		}
	}

	function drillDown(node: TreemapNode) {
		if (!hierarchyData()) return;
		
		// Update current root to show this node's children
		currentRoot = node;
		
		// Update breadcrumbs
		const path: TreemapNode[] = [];
		let current = node;
		while (current && current !== hierarchyData()) {
			path.unshift(current);
			current = current.parent || null;
		}
		// Add the top-level root if we're not already there
		if (hierarchyData() && !path.includes(hierarchyData()!)) {
			path.unshift(hierarchyData()!);
		}
		breadcrumbs = path;
		
		// Re-render with the new root
		renderTreemap();
	}

	function navigateToBreadcrumb(targetNode: TreemapNode) {
		if (!hierarchyData()) return;
		
		// Set the target as the new root
		currentRoot = targetNode;
		
		// Update breadcrumbs
		const path: TreemapNode[] = [];
		let current = targetNode;
		while (current && current !== hierarchyData()) {
			path.unshift(current);
			current = current.parent || null;
		}
		if (hierarchyData() && !path.includes(hierarchyData()!)) {
			path.unshift(hierarchyData()!);
		}
		breadcrumbs = path;
		
		// Re-render
		renderTreemap();
	}

	function zoomToRoot() {
		if (!hierarchyData()) return;
		
		// Reset to the original root
		currentRoot = hierarchyData()!;
		breadcrumbs = [hierarchyData()!];
		
		// Re-render
		renderTreemap();
	}

	function handleNodeMouseEnter(node: TreemapNode, event: MouseEvent) {
		if (!mergedConfig().interaction.hover) return;
		
		hoveredNode = node;
		onNodeHover?.(node);
		
		if (mergedConfig().interaction.tooltip) {
			const rect = containerElement.getBoundingClientRect();
			tooltipData = {
				node,
				x: event.clientX - rect.left,
				y: event.clientY - rect.top
			};
		}
	}

	function handleNodeMouseLeave() {
		if (!mergedConfig().interaction.hover) return;
		
		hoveredNode = null;
		onNodeHover?.(null);
		tooltipData = null;
	}

	function handleNodeMouseMove(event: MouseEvent) {
		if (!mergedConfig().interaction.tooltip || !tooltipData) return;
		
		const rect = containerElement.getBoundingClientRect();
		tooltipData = {
			...tooltipData,
			x: event.clientX - rect.left,
			y: event.clientY - rect.top
		};
	}

	function getNodeColor(node: TreemapNode): string {
		// Find the root-level ancestor to determine color
		let rootAncestor = node;
		while (rootAncestor.parent && rootAncestor.parent !== hierarchyData()) {
			rootAncestor = rootAncestor.parent;
		}
		
		const baseColor = colorScale()(rootAncestor.data.name);
		
		// Adjust opacity for nested levels
		const depthOpacity = node.depth > 1 ? 0.7 : 1;
		
		// Parse the color and adjust opacity
		if (baseColor.startsWith('oklch(')) {
			// Handle OKLCH colors by adjusting the alpha channel
			const match = baseColor.match(/oklch\(([^)]+)\)/);
			if (match) {
				const values = match[1].split(' ');
				if (values.length >= 3) {
					return `oklch(${values[0]} ${values[1]} ${values[2]} / ${depthOpacity})`;
				}
			}
		} else if (baseColor.startsWith('hsl(')) {
			// Handle HSL colors
			const match = baseColor.match(/hsl\(([^)]+)\)/);
			if (match) {
				const values = match[1].split(',').map(v => v.trim());
				if (values.length >= 3) {
					return `hsla(${values[0]}, ${values[1]}, ${values[2]}, ${depthOpacity})`;
				}
			}
		} else if (baseColor.startsWith('rgb(')) {
			// Handle RGB colors
			const match = baseColor.match(/rgb\(([^)]+)\)/);
			if (match) {
				const values = match[1].split(',').map(v => v.trim());
				if (values.length >= 3) {
					return `rgba(${values[0]}, ${values[1]}, ${values[2]}, ${depthOpacity})`;
				}
			}
		}
		
		return baseColor;
	}

	function shouldShowText(node: TreemapNode): boolean {
		const nodeWidth = (node.x1 || 0) - (node.x0 || 0);
		const nodeHeight = (node.y1 || 0) - (node.y0 || 0);
		return nodeWidth >= mergedConfig().text.minWidth && nodeHeight >= mergedConfig().text.minHeight;
	}

	function getTextSize(node: TreemapNode): { title: number; subtitle: number } {
		const nodeWidth = (node.x1 || 0) - (node.x0 || 0);
		const config = mergedConfig().text.fontSize;
		
		if (nodeWidth < 100) {
			return { title: config.small, subtitle: config.small - 1 };
		} else if (nodeWidth < 200) {
			return { title: config.subtitle, subtitle: config.small };
		}
		return { title: config.title, subtitle: config.subtitle };
	}

	function formatValue(value: number): string {
		if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
		if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
		return value.toString();
	}

	// Separate render function for cleaner drill-down
	function renderTreemap() {
		if (!svgElement || !currentRoot) return;

		const svg = select(svgElement);
		const config = mergedConfig();
		
		// Clear previous content
		svg.selectAll('*').remove();

		// Create main container
		const container = svg.append('g').attr('class', 'treemap-container');

		// Bind data and create rectangles for current level
		const currentNodes = nodes();

		const rects = container.selectAll<SVGRectElement, TreemapNode>('rect')
			.data(currentNodes)
			.enter()
			.append('rect')
			.attr('x', (d: TreemapNode) => d.x0 || 0)
			.attr('y', (d: TreemapNode) => d.y0 || 0)
			.attr('width', (d: TreemapNode) => (d.x1 || 0) - (d.x0 || 0))
			.attr('height', (d: TreemapNode) => (d.y1 || 0) - (d.y0 || 0))
			.attr('fill', (d: TreemapNode) => getNodeColor(d))
			.attr('stroke', resolveCSSCustomProperty('var(--border)'))
			.attr('stroke-width', 1)
			.attr('class', 'treemap-node')
			.style('cursor', (d: TreemapNode) => {
				return (d.children && d.children.length > 0) ? 'pointer' : 'default';
			})
			.on('click', (event: MouseEvent, d: TreemapNode) => handleNodeClick(d, event))
			.on('mouseenter', (event: MouseEvent, d: TreemapNode) => handleNodeMouseEnter(d, event))
			.on('mouseleave', handleNodeMouseLeave)
			.on('mousemove', handleNodeMouseMove);

		// Add text labels
		const texts = container.selectAll<SVGGElement, TreemapNode>('.node-text')
			.data(currentNodes.filter(shouldShowText))
			.enter()
			.append('g')
			.attr('class', 'node-text')
			.attr('transform', (d: TreemapNode) => `translate(${((d.x0 || 0) + (d.x1 || 0)) / 2}, ${((d.y0 || 0) + (d.y1 || 0)) / 2})`)
			.style('pointer-events', 'none')
			.style('text-anchor', 'middle')
			.style('dominant-baseline', 'central');

		// Add title text
		texts.append('text')
			.attr('dy', '-0.3em')
			.style('font-size', (d: TreemapNode) => `${getTextSize(d).title}px`)
			.style('font-weight', '600')
			.style('fill', resolveCSSCustomProperty('var(--card-foreground)'))
			.style('text-shadow', '0 1px 2px rgba(0,0,0,0.1)')
			.text((d: TreemapNode) => d.data.name);

		// Add value text
		texts.append('text')
			.attr('dy', '1.2em')
			.style('font-size', (d: TreemapNode) => `${getTextSize(d).subtitle}px`)
			.style('font-weight', '500')
			.style('fill', resolveCSSCustomProperty('var(--muted-foreground)'))
			.text((d: TreemapNode) => formatValue(d.value || 0));

		// Add percentage for current level
		if (currentRoot) {
			texts.append('text')
				.attr('dy', '2.3em')
				.style('font-size', (d: TreemapNode) => `${getTextSize(d).subtitle - 1}px`)
				.style('fill', resolveCSSCustomProperty('var(--muted-foreground)'))
				.style('text-shadow', '0 1px 2px rgba(0,0,0,0.1)')
				.text((d: TreemapNode) => {
					const total = currentRoot?.value || 1;
					const percentage = ((d.value || 0) / total * 100).toFixed(1);
					return `${percentage}%`;
				});
		}

		// Add animations
		if (config.animation.duration > 0) {
			rects
				.style('opacity', 0)
				.transition()
				.duration(config.animation.duration)
				.style('opacity', 1);

			texts
				.style('opacity', 0)
				.transition()
				.duration(config.animation.duration)
				.delay(config.animation.duration / 2)
				.style('opacity', 1);
		}
	}

	// Reactive updates - simplified to just call renderTreemap
	$effect(() => {
		if (!svgElement || !hierarchyData()) return;
		renderTreemap();
	});

	// Handle interactive state changes
	$effect(() => {
		if (!svgElement) return;
		
		const svg = select(svgElement);
		
		// Update all rectangles based on current hover/selection state
		svg.selectAll<SVGRectElement, TreemapNode>('rect')
			.style('filter', (d: TreemapNode) => {
				if (selectedNode?.data.name === d.data.name) {
					return 'brightness(0.75) saturate(1.5)';
				}
				if (hoveredNode?.data.name === d.data.name) {
					return 'brightness(1.1) saturate(1.2)';
				}
				return 'none';
			})
			.style('transform', (d: TreemapNode) => {
				if (hoveredNode?.data.name === d.data.name) {
					return 'scale(1.01)';
				}
				return 'scale(1)';
			});
	});

	// Cleanup
	onDestroy(() => {
		tooltipData = null;
		hoveredNode = null;
	});
</script>

<div 
	bind:this={containerElement}
	class="relative bg-card border border-border rounded-lg overflow-hidden shadow-sm"
	style="width: {width}px; height: {height}px;"
>
	<!-- Breadcrumb Navigation -->
	{#if breadcrumbs.length > 1}
		<div class="absolute top-2 left-2 z-10 flex items-center gap-1 text-sm bg-card/90 backdrop-blur-sm px-2 py-1 rounded-md border border-border/50">
			{#each breadcrumbs as crumb, index}
				{#if index > 0}
					<span class="text-muted-foreground">/</span>
				{/if}
				<button
					class="text-primary hover:text-primary/80 font-medium {index === breadcrumbs.length - 1 ? 'text-foreground cursor-default' : 'cursor-pointer'}"
					class:pointer-events-none={index === breadcrumbs.length - 1}
					on:click={() => navigateToBreadcrumb(crumb)}
				>
					{crumb.data.name}
				</button>
			{/each}
		</div>
	{/if}

	<svg 
		bind:this={svgElement}
		{width} 
		{height}
		class="w-full h-full"
	>
		<!-- Content will be rendered by D3 -->
	</svg>

	<!-- Tooltip -->
	{#if tooltipData && mergedConfig().interaction.tooltip}
		<div 
			class="absolute z-50 bg-popover border border-border rounded-md px-3 py-2 shadow-lg text-sm pointer-events-none transition-all duration-200"
			style="left: {tooltipData.x + 10}px; top: {tooltipData.y - 10}px; transform: translateY(-100%);"
		>
			<div class="font-medium text-popover-foreground">{tooltipData.node.data.name}</div>
			<div class="text-muted-foreground">{formatValue(tooltipData.node.value || 0)} items</div>
			{#if tooltipData.node.depth === 1 && hierarchyData()}
				<div class="text-xs text-muted-foreground">
					{(((tooltipData.node.value || 0) / (hierarchyData()!.value || 1)) * 100).toFixed(1)}% of total
				</div>
			{/if}
			{#if tooltipData.node.children && tooltipData.node.children.length > 0}
				<div class="text-xs text-muted-foreground mt-1">
					{tooltipData.node.children.length} subcategories
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	:global(.node-text text) {
		font-family: system-ui, -apple-system, sans-serif;
	}

	:global(.treemap-node) {
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		transform-origin: center;
	}

	:global(.treemap-node:hover) {
		filter: brightness(1.1) saturate(1.2);
		transform: scale(1.01);
	}
</style>
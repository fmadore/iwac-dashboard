<script lang="ts">
	import { onDestroy } from 'svelte';
	import { schemeSet2, schemeTableau10 } from 'd3-scale-chromatic';
	import { select } from 'd3-selection';
	import { zoom, zoomIdentity } from 'd3-zoom';
	import { hierarchy, treemap, treemapBinary } from 'd3-hierarchy';
	import type { TreemapData, TreemapNode, TreemapConfig } from '$lib/types/treemap.js';

	// Props
	interface TreemapProps {
		data: TreemapData;
		width?: number;
		height?: number;
		responsive?: boolean;
		config?: Partial<TreemapConfig>;
		onNodeClick?: (node: TreemapNode) => void;
		onNodeHover?: (node: TreemapNode | null) => void;
		selectedNode?: TreemapNode | null;
	}

	let {
		data,
		width = 800,
		height = 600,
		responsive = false,
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
				// Use D3's Set2 scheme - great for distinct categories
				...schemeSet2,
				// Add more colors from other schemes if needed
				...schemeTableau10.slice(0, 3),
				// Fallback to design system colors
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

	const COUNTRY_COLOR_MAP: Record<string, string> = {
		'cote-d-ivoire': 'var(--country-color-cote-divoire)',
		'burkina-faso': 'var(--country-color-burkina-faso)',
		'benin': 'var(--country-color-benin)',
		'togo': 'var(--country-color-togo)',
		'niger': 'var(--country-color-niger)',
		'nigeria': 'var(--country-color-nigeria)'
	};

	const FALLBACK_COUNTRY_COLOR = 'var(--country-color-default)';

	const slugifyCountry = (value: string | undefined | null): string => {
		if (!value) return '';
		const source = value.normalize ? value.normalize('NFKD') : value;
		const normalized = source
			.replace(/[\u0300-\u036f]/g, '')
			.replace(/\uFFFD/g, '')
			.replace(/[’'`]/g, '')
			.toLowerCase();
		return normalized
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/^-+|-+$/g, '');
	};

	const getCountryCssVar = (name: string): string => {
		const slug = slugifyCountry(name);
		return COUNTRY_COLOR_MAP[slug] ?? FALLBACK_COUNTRY_COLOR;
	};

	// State
	let containerElement: HTMLDivElement;
	let svgElement: SVGSVGElement;
	let hoveredNode = $state<TreemapNode | null>(null);
	let tooltipData = $state<{ node: TreemapNode; x: number; y: number } | null>(null);
	let currentRoot = $state<TreemapNode | null>(null);
	let breadcrumbs = $state<TreemapNode[]>([]);
	let zoomBehavior: any = null;
	let containerWidth = $state<number>(width);
	let containerHeight = $state<number>(height);
	
	// Reactive dimensions - use container size if responsive, otherwise use props
	let actualWidth = $derived(responsive ? containerWidth : width);
	let actualHeight = $derived(responsive ? containerHeight : height);

	// Custom tiling function for zoom (based on Observable example)
	function tile(node: any, x0: number, y0: number, x1: number, y1: number) {
		treemapBinary(node, 0, 0, actualWidth, actualHeight);
		for (const child of node.children || []) {
			child.x0 = x0 + child.x0 / actualWidth * (x1 - x0);
			child.x1 = x0 + child.x1 / actualWidth * (x1 - x0);
			child.y0 = y0 + child.y0 / actualHeight * (y1 - y0);
			child.y1 = y0 + child.y1 / actualHeight * (y1 - y0);
		}
	}

	// Computed values
	const treemapLayout = $derived(() => {
		const layout = treemap<TreemapData>()
			.size([actualWidth, actualHeight])
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

	const valueAccessor = (node: TreemapData): number => {
		// Ignore pre-aggregated values on parent nodes to avoid double counting
		return node.children?.length ? 0 : node.value ?? 0;
	};

	const hierarchyData = $derived.by(() => {
		if (!data) return null;
		
		// Create a deep copy with metadata to avoid mutating state in $derived
		const enrichData = (node: TreemapData, countryName?: string, countrySlug?: string): TreemapData & { __countryName?: string; __countrySlug?: string } => {
			const isCountryLevel = !node.children && node.name && !countryName;
			const newCountryName = isCountryLevel ? node.name : countryName;
			const newCountrySlug = isCountryLevel ? slugifyCountry(node.name ?? '') : countrySlug;
			
			return {
				...node,
				__countryName: newCountryName,
				__countrySlug: newCountrySlug,
				children: node.children?.map(child => enrichData(child, newCountryName, newCountrySlug))
			};
		};
		
		const enrichedData = enrichData(data);
		
		const root = hierarchy(enrichedData)
			.sum(valueAccessor)
			.sort((a, b) => (b.value || 0) - (a.value || 0));

		return treemapLayout()(root);
	});

	// Initialize currentRoot and breadcrumbs when hierarchyData is ready
	$effect(() => {
		const rootData = hierarchyData;
		if (!currentRoot && rootData) {
			currentRoot = rootData;
			breadcrumbs = [rootData];
		}
	});

	const nodes = $derived(() => {
		if (!currentRoot) return [];
		
		// Show children of current root, or if no children, show the current root itself
		if (currentRoot.children && currentRoot.children.length > 0) {
			// Apply treemap layout to current root for proper positioning
			const localTreemap = treemap<TreemapData>()
				.size([actualWidth, actualHeight])
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
				.sum(valueAccessor)
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

	const fallbackPalette = $derived(() => {
		const scheme = mergedConfig().colors.scheme ?? [];
		return scheme.length > 0 ? scheme : [FALLBACK_COUNTRY_COLOR];
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
		if (!hierarchyData) return;
		
		// Update current root to show this node's children
		currentRoot = node;
		
		// Update breadcrumbs
		const path: TreemapNode[] = [];
		let current: TreemapNode | null = node;
		while (current && current !== hierarchyData) {
			path.unshift(current);
			current = current.parent || null;
		}
		// Add the top-level root if we're not already there
		if (hierarchyData && !path.includes(hierarchyData)) {
			path.unshift(hierarchyData);
		}
		breadcrumbs = path;
		
		// Re-render with the new root
		renderTreemap();
	}

	function navigateToBreadcrumb(targetNode: TreemapNode) {
		if (!hierarchyData) return;
		
		// Set the target as the new root
		currentRoot = targetNode;
		
		// Update breadcrumbs
		const path: TreemapNode[] = [];
		let current: TreemapNode | null = targetNode;
		while (current && current !== hierarchyData) {
			path.unshift(current);
			current = current.parent || null;
		}
		if (hierarchyData && !path.includes(hierarchyData)) {
			path.unshift(hierarchyData);
		}
		breadcrumbs = path;
		
		// Re-render
		renderTreemap();
	}

	function zoomToRoot() {
		if (!hierarchyData) return;
		
		// Reset to the original root
		currentRoot = hierarchyData;
		breadcrumbs = [hierarchyData];
		
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

	function resolveCountryColor(countryName: string): string {
		if (!countryName) {
			return resolveCSSCustomProperty(FALLBACK_COUNTRY_COLOR);
		}
		const cssToken = getCountryCssVar(countryName);
		if (cssToken !== FALLBACK_COUNTRY_COLOR) {
			return resolveCSSCustomProperty(cssToken);
		}
		const palette = fallbackPalette();
		const slug = slugifyCountry(countryName);
		let hash = 7;
		for (let i = 0; i < slug.length; i += 1) {
			hash = (hash * 31 + slug.charCodeAt(i)) >>> 0;
		}
		const fallbackToken = palette[slug ? hash % palette.length : 0];
		return resolveCSSCustomProperty(fallbackToken);
	}

	function getNodeColor(node: TreemapNode): string {
		const data = node.data as TreemapData & { __countryName?: string };
		const countryName = data.__countryName ?? data.name ?? '';
		return resolveCountryColor(countryName);
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

		// Use proper D3 selection without type constraints for flexibility
		const rects = container.selectAll('rect')
			.data(currentNodes)
			.enter()
			.append('rect')
			.attr('x', (d: any) => d.x0 || 0)
			.attr('y', (d: any) => d.y0 || 0)
			.attr('width', (d: any) => (d.x1 || 0) - (d.x0 || 0))
			.attr('height', (d: any) => (d.y1 || 0) - (d.y0 || 0))
			.attr('fill', (d: any) => getNodeColor(d))
			.attr('stroke', resolveCSSCustomProperty('var(--border)'))
			.attr('stroke-width', 1)
			.attr('class', 'treemap-node')
			.style('cursor', (d: any) => {
				return (d.children && d.children.length > 0) ? 'pointer' : 'default';
			})
			.on('click', function(event: any, d: any) { 
				handleNodeClick(d, event as MouseEvent); 
			})
			.on('mouseenter', function(event: any, d: any) { 
				handleNodeMouseEnter(d, event as MouseEvent); 
			})
			.on('mouseleave', handleNodeMouseLeave)
			.on('mousemove', function(event: any) {
				handleNodeMouseMove(event as MouseEvent);
			});

		// Add text labels
		const filteredNodes = currentNodes.filter((node: any) => shouldShowText(node));
		const texts = container.selectAll('.node-text')
			.data(filteredNodes)
			.enter()
			.append('g')
			.attr('class', 'node-text')
			.attr('transform', (d: any) => `translate(${((d.x0 || 0) + (d.x1 || 0)) / 2}, ${((d.y0 || 0) + (d.y1 || 0)) / 2})`)
			.style('pointer-events', 'none')
			.style('text-anchor', 'middle')
			.style('dominant-baseline', 'central');

		// Add title text
		texts.append('text')
			.attr('dy', '-0.3em')
			.style('font-size', (d: any) => `${getTextSize(d).title}px`)
			.style('font-weight', '600')
			.style('fill', resolveCSSCustomProperty('var(--card-foreground)'))
			.style('text-shadow', '0 1px 2px rgba(0,0,0,0.1)')
			.text((d: any) => d.data.name);

		// Add value text
		texts.append('text')
			.attr('dy', '1.2em')
			.style('font-size', (d: any) => `${getTextSize(d).subtitle}px`)
			.style('font-weight', '500')
			.style('fill', resolveCSSCustomProperty('var(--muted-foreground)'))
			.text((d: any) => formatValue(d.value || 0));

		// Add percentage for current level
		if (currentRoot) {
			texts.append('text')
				.attr('dy', '2.3em')
				.style('font-size', (d: any) => `${getTextSize(d).subtitle - 1}px`)
				.style('fill', resolveCSSCustomProperty('var(--muted-foreground)'))
				.style('text-shadow', '0 1px 2px rgba(0,0,0,0.1)')
				.text((d: any) => {
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
		if (!svgElement || !hierarchyData) return;
		renderTreemap();
	});

	// Handle interactive state changes
	$effect(() => {
		if (!svgElement) return;
		
		const svg = select(svgElement);
		
		// Update all rectangles based on current hover/selection state
		svg.selectAll('rect')
			.style('filter', function(d: any) {
				if (selectedNode?.data.name === d.data.name) {
					return 'brightness(0.75) saturate(1.5)';
				}
				if (hoveredNode?.data.name === d.data.name) {
					return 'brightness(1.1) saturate(1.2)';
				}
				return 'none';
			})
			.style('transform', function(d: any) {
				if (hoveredNode?.data.name === d.data.name) {
					return 'scale(1.01)';
				}
				return 'scale(1)';
			});
	});

	// ResizeObserver for responsive behavior
	$effect(() => {
		if (!responsive || !containerElement) return;

		const resizeObserver = new ResizeObserver((entries) => {
			for (const entry of entries) {
				const { width: newWidth, height: newHeight } = entry.contentRect;
				// Only update if dimensions actually changed to avoid unnecessary re-renders
				if (newWidth !== containerWidth || newHeight !== containerHeight) {
					containerWidth = newWidth;
					containerHeight = newHeight;
				}
			}
		});

		resizeObserver.observe(containerElement);

		return () => {
			resizeObserver.disconnect();
		};
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
	class:w-full={responsive}
	class:h-full={responsive}
	style={responsive ? '' : `width: ${actualWidth}px; height: ${actualHeight}px;`}
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
					onclick={() => navigateToBreadcrumb(crumb)}
				>
					{crumb.data.name}
				</button>
			{/each}
		</div>
	{/if}

	<svg 
		bind:this={svgElement}
		width={actualWidth} 
		height={actualHeight}
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
			{#if tooltipData.node.depth === 1 && hierarchyData}
				<div class="text-xs text-muted-foreground">
					{(((tooltipData.node.value || 0) / (hierarchyData.value || 1)) * 100).toFixed(1)}% of total
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

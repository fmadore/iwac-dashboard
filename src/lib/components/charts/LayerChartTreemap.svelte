<script lang="ts">
	import { hierarchy } from 'd3-hierarchy';
	import { cubicOut } from 'svelte/easing';
	import { fade } from 'svelte/transition';
	import {
		Bounds,
		Chart,
		ChartClipPath,
		Group,
		Rect,
		RectClipPath,
		Svg,
		Text,
		Tooltip,
		Treemap
	} from 'layerchart';
	import type { TreemapData, TreemapNode, TreemapConfig } from '$lib/types/treemap.js';

	// Props - compatible interface with CustomTreemap
	interface Props {
		data: TreemapData;
		responsive?: boolean;
		config?: Partial<TreemapConfig>;
		onNodeClick?: (node: TreemapNode) => void;
		onNodeHover?: (node: TreemapNode | null) => void;
		selectedNode?: TreemapNode | null;
	}

	let {
		data,
		responsive = false,
		config = {},
		onNodeClick,
		onNodeHover,
		selectedNode = $bindable()
	}: Props = $props();

	// Country color mapping (same as CustomTreemap)
	const COUNTRY_COLOR_MAP: Record<string, string> = {
		'cote-d-ivoire': 'var(--country-color-cote-divoire)',
		'burkina-faso': 'var(--country-color-burkina-faso)',
		benin: 'var(--country-color-benin)',
		togo: 'var(--country-color-togo)',
		niger: 'var(--country-color-niger)',
		nigeria: 'var(--country-color-nigeria)'
	};
	const FALLBACK_COUNTRY_COLOR = 'var(--country-color-default)';

	const slugifyCountry = (value: string | undefined | null): string => {
		if (!value) return '';
		const source = value.normalize ? value.normalize('NFKD') : value;
		const normalized = source
			.replace(/[\u0300-\u036f]/g, '')
			.replace(/\uFFFD/g, '')
			.replace(/[''`]/g, '')
			.toLowerCase();
		return normalized.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
	};

	const getCountryCssVar = (name: string): string => {
		const slug = slugifyCountry(name);
		return COUNTRY_COLOR_MAP[slug] ?? FALLBACK_COUNTRY_COLOR;
	};

	// Animation configuration
	const animationDuration = $derived.by(() => config.animation?.duration ?? 800);

	// Treemap hierarchy
	const complexDataHierarchy = $derived.by(() => {
		if (!data) return null;

		// Enrich data with country metadata for color lookup
		const enrichData = (
			node: TreemapData,
			depth: number = 0,
			countryName?: string
		): TreemapData & { __countryName?: string } => {
			const isCountryLevel = depth === 1;
			const newCountryName = isCountryLevel ? node.name : countryName;

			return {
				...node,
				__countryName: newCountryName,
				children: node.children?.map((child) => enrichData(child, depth + 1, newCountryName))
			};
		};

		const enrichedData = enrichData(data);

		return hierarchy(enrichedData)
			.sum((d) => (d.children?.length ? 0 : (d.value ?? 0)))
			.sort((a, b) => (b.value || 0) - (a.value || 0));
	});

	// Currently selected/zoomed node for drill-down
	let selectedZoomable = $state<TreemapNode | null>(null);

	// Initialize selectedZoomable when hierarchy is ready
	$effect(() => {
		if (complexDataHierarchy && !selectedZoomable) {
			selectedZoomable = complexDataHierarchy as TreemapNode;
		}
	});

	// Get node color based on country
	function getNodeColor(node: any): string {
		const data = node.data as TreemapData & { __countryName?: string };
		const countryName = data.__countryName ?? data.name ?? '';
		const cssVar = getCountryCssVar(countryName);
		return cssVar;
	}

	// Check if a node is visible at current zoom level
	function isNodeVisible(node: any, currentZoom: any): boolean {
		if (!currentZoom) return true;

		// Node is visible if it's a descendant of current zoom or the zoom itself
		let current = node;
		while (current) {
			if (current.data.name === currentZoom.data.name && current.depth === currentZoom.depth) {
				return true;
			}
			current = current.parent;
		}
		return false;
	}

	// Format number for display
	function formatValue(value: number): string {
		if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
		if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
		return value.toLocaleString();
	}

	// Generate a unique key for a node based on its full ancestry path
	function getNodeKey(node: any): string {
		const path = node
			.ancestors()
			.reverse()
			.map((n: any) => n.data.name)
			.join('/');
		return path;
	}
</script>

<div
	class="layerchart-treemap relative overflow-hidden rounded-lg border border-border bg-card shadow-sm"
	class:h-full={responsive}
	class:w-full={responsive}
>
	{#if complexDataHierarchy && selectedZoomable}
		<!-- Breadcrumb Navigation -->
		<div
			class="absolute top-2 left-2 z-10 flex items-center gap-1 rounded-md border border-border/50 bg-card/90 px-2 py-1 text-sm backdrop-blur-sm"
		>
			{#each selectedZoomable.ancestors().reverse() as item, index (index)}
				{#if index > 0}
					<span class="text-muted-foreground">/</span>
				{/if}
				<button
					class="font-medium text-primary hover:text-primary/80 {item === selectedZoomable
						? 'cursor-default text-foreground'
						: 'cursor-pointer'}"
					class:pointer-events-none={item === selectedZoomable}
					onclick={() => (selectedZoomable = item as TreemapNode)}
				>
					{index === 0 ? 'Islam West Africa Collection' : item.data.name}
				</button>
			{/each}
		</div>

		<!-- Treemap Chart -->
		<div class="h-150 p-4">
			<Chart tooltip={{ mode: 'manual' }}>
				{#snippet children({ context })}
					<Svg>
						<Bounds
							domain={selectedZoomable}
							motion={{ type: 'tween', duration: animationDuration, easing: cubicOut }}
						>
							{#snippet children({ xScale, yScale })}
								<ChartClipPath>
									<Treemap hierarchy={complexDataHierarchy} tile="binary">
										{#snippet children({ nodes })}
											{#each nodes as node (getNodeKey(node))}
												<Group
													x={xScale(node.x0)}
													y={yScale(node.y0)}
													onclick={() => {
														if (!node.children) return;
														onNodeClick?.(node as TreemapNode);
														selectedZoomable = node as TreemapNode;
													}}
													onpointerenter={(e) => {
														onNodeHover?.(node as TreemapNode);
														context.tooltip.show(e, node);
													}}
													onpointermove={(e) => context.tooltip.show(e, node)}
													onpointerleave={() => {
														onNodeHover?.(null);
														context.tooltip.hide();
													}}
												>
													{@const nodeWidth = xScale(node.x1) - xScale(node.x0)}
													{@const nodeHeight = yScale(node.y1) - yScale(node.y0)}
													<RectClipPath width={nodeWidth} height={nodeHeight}>
														{@const nodeColor = getNodeColor(node)}
														{#if isNodeVisible( node, nodes.find((n) => n.data.name === selectedZoomable?.data.name && n.depth === selectedZoomable?.depth) )}
															<g transition:fade={{ duration: 600 }}>
																<Rect
																	width={nodeWidth}
																	height={nodeHeight}
																	stroke="var(--border)"
																	stroke-width={1}
																	fill={nodeColor}
																	rx={5}
																	class="treemap-node cursor-pointer transition-all duration-300 hover:brightness-110 hover:saturate-125"
																/>
																{#if nodeWidth > 60 && nodeHeight > 30}
																	<Text
																		value={node.data.name}
																		class="pointer-events-none fill-current text-[10px] font-medium"
																		verticalAnchor="start"
																		x={4}
																		y={4}
																	/>
																	<Text
																		value={formatValue(node.value ?? 0)}
																		class="pointer-events-none fill-current text-[8px] font-normal opacity-70"
																		verticalAnchor="start"
																		x={4}
																		y={18}
																	/>
																{/if}
															</g>
														{/if}
													</RectClipPath>
												</Group>
											{/each}
										{/snippet}
									</Treemap>
								</ChartClipPath>
							{/snippet}
						</Bounds>
					</Svg>

					<Tooltip.Root
						{context}
						classes={{
							content: 'rounded-md border border-border bg-popover px-3 py-2 text-sm shadow-lg'
						}}
					>
						{#snippet children({ data })}
							{#if data}
								{@const node = data as any}
								<div class="font-medium text-popover-foreground">{node.data?.name}</div>
								<div class="text-muted-foreground">{formatValue(node.value ?? 0)} items</div>
								{#if node.children && node.children.length > 0}
									<div class="mt-1 text-xs text-muted-foreground">
										{node.children.length} subcategories · Click to drill down
									</div>
								{/if}
							{/if}
						{/snippet}
					</Tooltip.Root>
				{/snippet}
			</Chart>
		</div>
	{:else}
		<div class="flex h-150 w-full items-center justify-center">
			<div
				class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent"
			></div>
		</div>
	{/if}
</div>

<style>
	.layerchart-treemap :global(.treemap-node) {
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		transform-origin: center;
	}

	.layerchart-treemap :global(.treemap-node:hover) {
		filter: brightness(1.1) saturate(1.2);
	}
</style>

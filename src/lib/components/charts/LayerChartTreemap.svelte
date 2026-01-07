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
		Tooltip
	} from 'layerchart';
	import { Treemap } from 'layerchart';
	import type { TreemapData, TreemapNode, TreemapConfig } from '$lib/types/treemap.js';
	import LayerChartTooltip, { type TooltipItem } from './LayerChartTooltip.svelte';

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
	let selectedNested = $state<TreemapNode | null>(null);

	// Initialize selectedNested when hierarchy is ready
	$effect(() => {
		if (complexDataHierarchy && !selectedNested) {
			selectedNested = complexDataHierarchy as TreemapNode;
		}
	});

	// Get node color based on country
	function getNodeColor(node: any): string {
		const data = node.data as TreemapData & { __countryName?: string };
		const countryName = data.__countryName ?? data.name ?? '';
		const cssVar = getCountryCssVar(countryName);
		return cssVar;
	}

	// Format number for display
	function formatValue(value: number): string {
		if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
		if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
		return value.toLocaleString();
	}

	function treemapTooltipItems(node: any): TooltipItem[] {
		if (!node) return [];
		const items: TooltipItem[] = [];
		items.push({ name: '', value: `${formatValue(node.value ?? 0)} items` });
		if (node.children && node.children.length > 0) {
			items.push({ name: '', value: `${node.children.length} subcategories · Click to drill down` });
		}
		return items;
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
	{#if complexDataHierarchy && selectedNested}
		<!-- Breadcrumb Navigation -->
		<div
			class="flex items-center gap-1 rounded-md border-b border-border bg-card/90 px-3 py-2 text-sm"
		>
			{#each selectedNested.ancestors().reverse() as item, index (index)}
				{#if index > 0}
					<span class="text-muted-foreground">/</span>
				{/if}
				<button
					class="rounded-sm px-2 py-1 font-medium transition-colors {item === selectedNested
						? 'cursor-default bg-muted text-foreground'
						: 'cursor-pointer text-primary hover:bg-muted/50 hover:text-primary/80'}"
					class:pointer-events-none={item === selectedNested}
					onclick={() => (selectedNested = item as TreemapNode)}
				>
					<div class="text-left">
						<div class="text-sm">
							{index === 0 ? 'Islam West Africa Collection' : item.data.name}
						</div>
						<div class="text-xs text-muted-foreground">
							{formatValue(item.value ?? 0)}
						</div>
					</div>
				</button>
			{/each}
		</div>

		<!-- Treemap Chart -->
		<div class="h-[600px] p-4">
			<Chart>
				{#snippet children({ context })}
					<Svg>
						<Bounds
							domain={selectedNested}
							motion={{ type: 'tween', duration: animationDuration, easing: cubicOut }}
						>
							{#snippet children({ xScale, yScale })}
								<ChartClipPath>
									<Treemap hierarchy={complexDataHierarchy} tile="squarify">
										{#snippet children({ nodes })}
											{#each nodes as node (getNodeKey(node))}
												<Group
													x={xScale(node.x0)}
													y={yScale(node.y0)}
													onclick={() => {
														if (node.children) {
															onNodeClick?.(node as TreemapNode);
															selectedNested = node as TreemapNode;
														}
													}}
													onpointermove={(e) => context.tooltip.show(e, node)}
													onpointerleave={context.tooltip.hide}
												>
													{@const nodeWidth = xScale(node.x1) - xScale(node.x0)}
													{@const nodeHeight = yScale(node.y1) - yScale(node.y0)}
													{@const nodeColor = getNodeColor(node)}
													<g transition:fade={{ duration: 600 }}>
														<Rect
															width={nodeWidth}
															height={nodeHeight}
															stroke="var(--border)"
															stroke-width={1}
															fill={nodeColor}
															fillOpacity={node.children ? 0.5 : 1}
															rx={5}
															class="treemap-node cursor-pointer"
														/>
														<RectClipPath width={nodeWidth} height={nodeHeight}>
															<text
																x={4}
																y={16 * 0.6 + 4}
																class="pointer-events-none fill-white text-[10px] font-medium drop-shadow-sm"
															>
																<tspan>{node.data.name}</tspan>
																{#if node.children}
																	<tspan class="text-[8px] font-light opacity-80">
																		{' '}{formatValue(node.value ?? 0)}
																	</tspan>
																{/if}
															</text>
															{#if !node.children}
																<Text
																	value={formatValue(node.value ?? 0)}
																	class="pointer-events-none fill-white/80 text-[8px] font-normal drop-shadow-sm"
																	verticalAnchor="start"
																	x={4}
																	y={16}
																/>
															{/if}
														</RectClipPath>
													</g>
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
							content: 'border-0 bg-transparent p-0 shadow-none'
						}}
					>
						{#snippet children({ data })}
							{#if data}
								{@const node = data as any}
								<LayerChartTooltip
									label={node.data?.name}
									items={treemapTooltipItems(node)}
									indicator="dot"
									hideIndicator
								/>
							{/if}
						{/snippet}
					</Tooltip.Root>
				{/snippet}
			</Chart>
		</div>
	{:else}
		<div class="flex h-[600px] w-full items-center justify-center">
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

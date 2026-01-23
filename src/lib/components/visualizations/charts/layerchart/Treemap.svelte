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
	import { t } from '$lib/stores/translationStore.svelte.js';
	import type { TreemapData, TreemapNode, TreemapConfig } from '$lib/types/treemap.js';
	import ChartTooltip, { type TooltipItem } from './Tooltip.svelte';

	// Props - compatible interface with CustomTreemap
	interface Props {
		data: TreemapData;
		responsive?: boolean;
		config?: Partial<TreemapConfig>;
		/** Externally-managed drilldown selection (NestedTreemap pattern). */
		selectedNested?: TreemapNode | null;
		/** Whether to render the internal breadcrumb UI. */
		showBreadcrumb?: boolean;
		/** Pass-through layout options (LayerChart Treemap props). */
		tile?: any;
		maintainAspectRatio?: boolean;
		paddingOuter?: number;
		paddingInner?: number;
		paddingTop?: number;
		paddingBottom?: number;
		paddingLeft?: number;
		paddingRight?: number;
		onNodeClick?: (node: TreemapNode) => void;
		onNodeHover?: (node: TreemapNode | null) => void;
		selectedNode?: TreemapNode | null;
	}

	let {
		data,
		responsive = false,
		config = {},
		selectedNested = $bindable(),
		showBreadcrumb = true,
		tile,
		maintainAspectRatio,
		paddingOuter,
		paddingInner,
		paddingTop,
		paddingBottom,
		paddingLeft,
		paddingRight,
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

	// Treemap layout configuration (compatible with LayerChart NestedTreemap example)
	// Default padding creates nested visual effect - paddingTop for labels, paddingInner for separation
	const tileValue = $derived.by(() => tile ?? config.tile ?? 'squarify');
	const paddingOuterValue = $derived.by(() => paddingOuter ?? config.padding?.outer ?? 4);
	const paddingInnerValue = $derived.by(() => paddingInner ?? config.padding?.inner ?? 2);
	const paddingTopValue = $derived.by(() => paddingTop ?? config.padding?.top ?? 20);
	const paddingBottomValue = $derived.by(() => paddingBottom ?? config.padding?.bottom ?? 2);
	const paddingLeftValue = $derived.by(() => paddingLeft ?? config.padding?.left ?? 2);
	const paddingRightValue = $derived.by(() => paddingRight ?? config.padding?.right ?? 2);

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

	const activeDomain = $derived.by(() => {
		if (selectedNested) return selectedNested;
		if (complexDataHierarchy) return complexDataHierarchy as unknown as TreemapNode;
		return null;
	});

	$effect(() => {
		if (!complexDataHierarchy) return;
		const root = complexDataHierarchy as unknown as TreemapNode;
		if (!selectedNested) {
			selectedNested = root;
			return;
		}
		const selectedRoot = selectedNested.ancestors().at(-1) as TreemapNode | undefined;
		if (!selectedRoot || selectedRoot.data?.name !== root.data?.name) {
			selectedNested = root;
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
		items.push({ name: t('chart.documents'), value: formatValue(node.value ?? 0) });
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
	{#if complexDataHierarchy && activeDomain}
		{#if showBreadcrumb}
			<!-- Breadcrumb Navigation -->
			<div
				class="flex items-center gap-1 rounded-md border-b border-border bg-card/90 px-3 py-2 text-sm"
			>
				{#each activeDomain.ancestors().reverse() as item, index (index)}
					{#if index > 0}
						<span class="text-muted-foreground">/</span>
					{/if}
					<button
						class="rounded-sm px-2 py-1 font-medium transition-colors {item === activeDomain
							? 'cursor-default bg-muted text-foreground'
							: 'cursor-pointer text-primary hover:bg-muted/50 hover:text-primary/80'}"
						class:pointer-events-none={item === activeDomain}
						onclick={() => (selectedNested = item as TreemapNode)}
					>
						<div class="text-left">
							<div class="text-sm">
								{index === 0 ? t('app.subtitle') : item.data.name}
							</div>
							<div class="text-xs text-muted-foreground">
								{formatValue(item.value ?? 0)}
							</div>
						</div>
					</button>
				{/each}
			</div>
		{/if}

		<!-- Treemap Chart -->
		<div class="h-150 p-4">
			<Chart>
				{#snippet children({ context })}
					<Svg>
						<Bounds
							domain={activeDomain}
							motion={{ type: 'tween', duration: animationDuration, easing: cubicOut }}
						>
							{#snippet children({ xScale, yScale })}
								<ChartClipPath>
									<Treemap
										hierarchy={complexDataHierarchy}
										tile={tileValue}
										{maintainAspectRatio}
										paddingOuter={paddingOuterValue}
										paddingInner={paddingInnerValue}
										paddingTop={paddingTopValue}
										paddingBottom={paddingBottomValue}
										paddingLeft={paddingLeftValue}
										paddingRight={paddingRightValue}
									>
										{#snippet children({ nodes })}
											{@const activeKey = activeDomain ? getNodeKey(activeDomain) : ''}
											{@const visibleNodes = nodes.filter((n: any) => {
												if (!activeDomain) return false;
												// Show all nodes except the root itself for nested visualization
												if (!n.parent) return false;
												// Check if this node is a descendant of the active domain
												const ancestors = n.ancestors();
												return ancestors.some((a: any) => getNodeKey(a) === activeKey);
											})}
											{#each visibleNodes as node (getNodeKey(node))}
												<Group
													x={xScale(node.x0)}
													y={yScale(node.y0)}
													onclick={() => {
													onNodeClick?.(node as TreemapNode);
													if (node.children) selectedNested = node as TreemapNode;
													}}
													onpointermove={(e) => {
														onNodeHover?.(node as TreemapNode);
														context.tooltip.show(e, node);
													}}
													onpointerleave={() => {
														onNodeHover?.(null);
														context.tooltip.hide();
													}}
												>
													{@const nodeWidth = xScale(node.x1) - xScale(node.x0)}
													{@const nodeHeight = yScale(node.y1) - yScale(node.y0)}
													{@const nodeColor = getNodeColor(node)}
													{@const nodeDepth = node.depth}
													{@const isParent = !!node.children}
													{@const isCountry = nodeDepth === 1}
													{@const isDocType = nodeDepth === 2}
													<g transition:fade={{ duration: 600 }}>
														<Rect
															width={nodeWidth}
															height={nodeHeight}
															stroke={isParent ? 'var(--foreground)' : 'var(--border)'}
															stroke-width={isCountry ? 2 : 1}
															fill={nodeColor}
															fillOpacity={isParent ? 0.3 : 0.9}
															rx={isCountry ? 8 : isDocType ? 4 : 2}
															class="treemap-node cursor-pointer"
														/>
														{#if isParent}
															<!-- Parent label with background for visibility -->
															<RectClipPath width={nodeWidth} height={paddingTopValue}>
																<rect
																	width={nodeWidth}
																	height={paddingTopValue}
																	fill={nodeColor}
																	fill-opacity="0.8"
																/>
																<text
																	x={4}
																	y={isCountry ? 14 : 12}
																	class="pointer-events-none fill-white drop-shadow-md"
																	class:text-xs={isCountry}
																	class:font-bold={isCountry}
																	class:text-[10px]={isDocType}
																	class:font-semibold={isDocType}
																>
																	<tspan>{node.data.name}</tspan>
																	<tspan class="font-normal opacity-80" dx={4}>
																		{formatValue(node.value ?? 0)}
																	</tspan>
																</text>
															</RectClipPath>
														{:else}
															<!-- Leaf node label -->
															<RectClipPath width={nodeWidth} height={nodeHeight}>
																<text
																	x={4}
																	y={12}
																	class="pointer-events-none fill-white text-[9px] font-medium drop-shadow-sm"
																>
																	{node.data.name}
																</text>
																<Text
																	value={formatValue(node.value ?? 0)}
																	class="pointer-events-none fill-white/90 text-[8px] font-normal drop-shadow-sm"
																	verticalAnchor="start"
																	x={4}
																	y={12}
																/>
															</RectClipPath>
														{/if}
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
						variant="none"
						classes={{
							content: 'border-0 bg-transparent p-0 shadow-none'
						}}
					>
						{#snippet children({ data })}
							{#if data}
								{@const node = data as any}
								<ChartTooltip
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

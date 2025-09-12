<script lang="ts">
	import { Card } from '$lib/components/ui/card/index.js';
	import { itemsStore } from '$lib/stores/itemsStore.js';
	import { t } from '$lib/stores/translationStore.js';
	import { Chart, Svg, Treemap } from 'layerchart';

	type HierarchyNode = {
		name: string;
		value: number;
		children?: HierarchyNode[];
	};

	let selectedNode = $state<HierarchyNode | null>(null);
	let hoveredNode = $state<any>(null);

	const treemapData = $derived(getTreemapData($itemsStore.items));

	function getTreemapData(items: any[]): HierarchyNode {
		const countryMap = new Map();
		
		items.forEach(item => {
			if (!item.country) return;
			
			if (!countryMap.has(item.country)) {
				countryMap.set(item.country, {
					name: item.country,
					value: 0,
					children: new Map()
				});
			}
			
			const country = countryMap.get(item.country);
			country.value++;
			
			if (item.type) {
				if (!country.children.has(item.type)) {
					country.children.set(item.type, {
						name: item.type,
						value: 0
					});
				}
				country.children.get(item.type).value++;
			}
		});
		
		// Transform to hierarchical structure for Treemap
		const root: HierarchyNode = {
			name: 'Countries',
			value: 0, // Will be calculated by LayerChart
			children: Array.from(countryMap.values()).map(country => ({
				...country,
				children: Array.from(country.children.values())
			})).sort((a, b) => b.value - a.value)
		};
		
		return root;
	}

	function getNodeColor(node: any): string {
		if (node.depth === 0) return 'hsl(var(--muted))'; // Root
		if (node.depth === 1) {
			// Country level - use different shades of primary
			const index = node.parent?.children?.indexOf(node) || 0;
			const hue = 210 + (index * 25) % 180; // Vary hue for different countries
			return `hsl(${hue}, 70%, 45%)`;
		}
		// Type level - lighter shade of parent country
		return `hsl(var(--muted-foreground))`;
	}

	function getTotalValue(): number {
		return treemapData.children?.reduce((sum, country) => sum + country.value, 0) || 1;
	}
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{$t('nav.countries')}</h2>
		<p class="text-muted-foreground">Distribution of documents by country</p>
	</div>

	<Card class="p-6">
		<h3 class="text-xl font-semibold mb-6">Country Distribution</h3>
		
		<div class="h-96 w-full rounded-lg border bg-card overflow-hidden">
			<Chart data={treemapData} padding={{ top: 4, bottom: 4, left: 4, right: 4 }}>
				<Svg>
					<Treemap let:nodes>
						{#each nodes as node}
							{#if node.depth > 0}
								<rect
									x={node.x0}
									y={node.y0}
									width={node.x1 - node.x0}
									height={node.y1 - node.y0}
									fill={getNodeColor(node)}
									stroke="hsl(var(--background))"
									stroke-width={node.depth === 1 ? "3" : "1"}
									class="cursor-pointer transition-all duration-200 hover:brightness-110"
									class:ring-2={selectedNode?.name === node.data.name}
									class:ring-ring={selectedNode?.name === node.data.name}
									role="button"
									tabindex="0"
									onclick={() => selectedNode = node.data}
									onkeydown={(e) => e.key === 'Enter' && (selectedNode = node.data)}
									onmouseenter={() => hoveredNode = node}
									onmouseleave={() => hoveredNode = null}
								/>
								{#if (node.x1 - node.x0) > 80 && (node.y1 - node.y0) > 40}
									<text
										x={node.x0 + (node.x1 - node.x0) / 2}
										y={node.y0 + (node.y1 - node.y0) / 2 - 8}
										text-anchor="middle"
										dominant-baseline="central"
										class="text-xs font-semibold fill-white pointer-events-none drop-shadow-sm"
										style="font-size: {Math.min(14, Math.max(10, (node.x1 - node.x0) / 8))}px"
									>
										{node.data.name}
									</text>
									<text
										x={node.x0 + (node.x1 - node.x0) / 2}
										y={node.y0 + (node.y1 - node.y0) / 2 + 8}
										text-anchor="middle"
										dominant-baseline="central"
										class="text-xs fill-white/90 pointer-events-none drop-shadow-sm"
										style="font-size: {Math.min(11, Math.max(8, (node.x1 - node.x0) / 12))}px"
									>
										{node.data.value} items
									</text>
									{#if node.depth === 1}
										<text
											x={node.x0 + (node.x1 - node.x0) / 2}
											y={node.y0 + (node.y1 - node.y0) / 2 + 22}
											text-anchor="middle"
											dominant-baseline="central"
											class="text-xs fill-white/75 pointer-events-none drop-shadow-sm"
											style="font-size: {Math.min(10, Math.max(7, (node.x1 - node.x0) / 15))}px"
										>
											{((node.data.value / getTotalValue()) * 100).toFixed(1)}%
										</text>
									{/if}
								{/if}
							{/if}
						{/each}
					</Treemap>
				</Svg>
			</Chart>
		</div>

		<!-- Enhanced Information Panel -->
		{#if selectedNode}
			<div class="mt-6 p-4 bg-gradient-to-r from-primary/5 to-primary/10 border-l-4 border-primary rounded-lg">
				<div class="flex items-center justify-between mb-2">
					<h4 class="font-semibold text-lg text-primary">{selectedNode.name}</h4>
					<button
						class="text-sm text-muted-foreground hover:text-foreground"
						onclick={() => selectedNode = null}
					>
						✕
					</button>
				</div>
				<div class="space-y-2 text-sm">
					<div class="flex justify-between">
						<span class="text-muted-foreground">Total items:</span>
						<span class="font-medium">{selectedNode.value}</span>
					</div>
					{#if selectedNode.children && treemapData.children}
						<div class="flex justify-between">
							<span class="text-muted-foreground">Percentage of total:</span>
							<span class="font-medium">{((selectedNode.value / getTotalValue()) * 100).toFixed(1)}%</span>
						</div>
						<div class="flex justify-between">
							<span class="text-muted-foreground">Document types:</span>
							<span class="font-medium">{selectedNode.children.length}</span>
						</div>
					{/if}
				</div>
				{#if selectedNode.children}
					<div class="mt-4">
						<h5 class="font-medium text-sm mb-2 text-muted-foreground">Document Types:</h5>
						<div class="grid grid-cols-2 gap-2 text-xs">
							{#each selectedNode.children.slice(0, 6) as child}
								<div class="flex justify-between bg-background/50 rounded px-2 py-1">
									<span>{child.name}</span>
									<span class="font-medium">{child.value}</span>
								</div>
							{/each}
							{#if selectedNode.children.length > 6}
								<div class="col-span-2 text-center text-muted-foreground py-1">
									...and {selectedNode.children.length - 6} more
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>
		{:else}
			<div class="mt-6 p-4 bg-muted/30 rounded-lg text-center">
				<p class="text-sm text-muted-foreground">Click on a country or document type to see details</p>
			</div>
		{/if}

		<!-- Tooltip for hover -->
		{#if hoveredNode}
			<div class="fixed z-50 bg-popover border border-border rounded-md px-3 py-2 shadow-lg text-sm pointer-events-none"
				 style="left: {hoveredNode.x0 + 10}px; top: {hoveredNode.y0 - 10}px;">
				<div class="font-medium">{hoveredNode.data.name}</div>
				<div class="text-muted-foreground">{hoveredNode.data.value} items</div>
				{#if hoveredNode.depth === 1}
					<div class="text-xs text-muted-foreground">
						{((hoveredNode.data.value / getTotalValue()) * 100).toFixed(1)}% of total
					</div>
				{/if}
			</div>
		{/if}
	</Card>
</div>

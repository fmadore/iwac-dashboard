<script lang="ts">
	import { Card } from '$lib/components/ui/card/index.js';
	import { itemsStore } from '$lib/stores/itemsStore.svelte.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import CustomTreemap from '$lib/components/charts/CustomTreemap.svelte';
	import { base } from '$app/paths';
	import type { TreemapData, TreemapNode } from '$lib/types/index.js';

	let selectedNode = $state<TreemapNode | null>(null);
	let treemapData = $state<TreemapData | null>(null);
	let isLoading = $state(true);
	let loadingError = $state<string | null>(null);

	// Load pre-computed treemap data
	$effect(() => {
		const loadData = async () => {
			try {
				isLoading = true;
				loadingError = null;
				
				const response = await fetch(`${base}/data/treemap-countries.json`);
				if (response.ok) {
					const jsonData = await response.json();
					treemapData = jsonData;
					console.log('✅ Loaded treemap data');
				} else {
					throw new Error(`Failed to fetch treemap data: ${response.status} ${response.statusText}`);
				}
			} catch (error) {
				console.warn('Failed to load pre-computed treemap data, falling back to client-side processing:', error);
				loadingError = error instanceof Error ? error.message : 'Unknown error';
				
				// Fallback to computing from itemsStore if pre-computed data not available
				if (itemsStore.items && itemsStore.items.length > 0) {
					const fallbackData = getTreemapData(itemsStore.items);
					treemapData = fallbackData;
					console.log('📊 Using fallback client-side treemap computation');
				} else {
					console.warn('No items available for fallback computation');
				}
			} finally {
				isLoading = false;
			}
		};

		loadData();
	});

	function getTreemapData(items: any[]): TreemapData {
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
		const root: TreemapData = {
			name: 'Countries',
			value: 0, // Will be calculated by LayerChart
			children: Array.from(countryMap.values()).map(country => ({
				...country,
				children: Array.from(country.children.values())
			})).sort((a, b) => (b.value || 0) - (a.value || 0))
		};
		
		return root;
	}

	function getTotalValue(): number {
		if (!treemapData) return 1;
		
		// Calculate total from the root data
		function calculateTotal(node: TreemapData): number {
			if (node.children) {
				return node.children.reduce((sum, child) => sum + calculateTotal(child), 0);
			}
			return node.value || 0;
		}
		
		return calculateTotal(treemapData);
	}

	// Event handlers for the custom treemap
	function handleNodeClick(node: TreemapNode) {
		selectedNode = selectedNode?.data.name === node.data.name ? null : node;
	}

	function handleNodeHover(node: TreemapNode | null) {
		// Handle hover if needed
	}
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{t('nav.countries')}</h2>
		<p class="text-muted-foreground">Distribution of documents by country</p>
	</div>

	<Card class="p-6">
		<h3 class="text-xl font-semibold mb-6">Country Distribution</h3>
		
		{#if isLoading}
			<div class="h-[600px] w-full rounded-lg border bg-card flex items-center justify-center">
				<div class="text-center">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
					<p class="text-muted-foreground">Loading treemap data...</p>
				</div>
			</div>
		{:else if loadingError}
			<div class="h-[600px] w-full rounded-lg border bg-card flex items-center justify-center">
				<div class="text-center">
					<p class="text-destructive mb-2">⚠️ Failed to load treemap data</p>
					<p class="text-sm text-muted-foreground">{loadingError}</p>
					<p class="text-xs text-muted-foreground mt-2">Using fallback client-side processing</p>
				</div>
			</div>
		{:else if treemapData}
			<div class="w-full h-[600px]">
				<CustomTreemap 
					data={treemapData}
					responsive={true}
					bind:selectedNode
					onNodeClick={handleNodeClick}
					onNodeHover={handleNodeHover}
					config={{
						padding: {
							inner: 3,
							outer: 6,
							top: 25,
							right: 3,
							bottom: 3,
							left: 3
						},
						animation: {
							duration: 400,
							ease: 'ease-in-out'
						}
					}}
				/>
			</div>
		{:else}
			<div class="h-[600px] w-full rounded-lg border bg-card flex items-center justify-center">
				<div class="text-center">
					<p class="text-muted-foreground">No treemap data available</p>
				</div>
			</div>
		{/if}

		<!-- Enhanced Information Panel -->
		{#if selectedNode}
			<div class="mt-6 p-4 bg-gradient-to-r from-primary/5 to-primary/10 border-l-4 border-primary rounded-lg">
				<div class="flex items-center justify-between mb-2">
					<h4 class="font-semibold text-lg text-primary">{selectedNode.data.name}</h4>
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
						<span class="font-medium">{selectedNode.value || 0}</span>
					</div>
					{#if selectedNode.data.children && selectedNode.data.children.length > 0}
						<div class="flex justify-between">
							<span class="text-muted-foreground">Percentage of total:</span>
							<span class="font-medium">{(((selectedNode.value || 0) / getTotalValue()) * 100).toFixed(1)}%</span>
						</div>
						<div class="flex justify-between">
							<span class="text-muted-foreground">Document types:</span>
							<span class="font-medium">{selectedNode.data.children.length}</span>
						</div>
					{/if}
				</div>
				{#if selectedNode.data.children}
					<div class="mt-4">
						<h5 class="font-medium text-sm mb-2 text-muted-foreground">Document Types:</h5>
						<div class="grid grid-cols-2 gap-2 text-xs">
							{#each selectedNode.data.children.slice(0, 6) as child}
								<div class="flex justify-between bg-background/50 rounded px-2 py-1">
									<span>{child.name}</span>
									<span class="font-medium">{child.value || 0}</span>
								</div>
							{/each}
							{#if selectedNode.data.children.length > 6}
								<div class="col-span-2 text-center text-muted-foreground py-1">
									...and {selectedNode.data.children.length - 6} more
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

	</Card>
</div>

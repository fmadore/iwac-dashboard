<script lang="ts">
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Slider } from '$lib/components/ui/slider/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import {
		NetworkMapView,
		NetworkNodePanel,
		NetworkLegend
	} from '$lib/components/visualizations/network/index.js';
	import { StatsCard } from '$lib/components/dashboard/index.js';
	import type { SpatialNetworkData, NetworkNode, NodeSizeBy } from '$lib/types/network.js';
	import { Maximize2 } from '@lucide/svelte';

	// Data state
	let networkData = $state<SpatialNetworkData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// View state
	let nodeSizeBy = $state<NodeSizeBy>('count');
	let minEdgeWeight = $state(1);
	let selectedNode = $state<NetworkNode | null>(null);
	let hoveredNode = $state<NetworkNode | null>(null);

	// Component ref
	let mapComponent: NetworkMapView | null = $state(null);

	// Derived stats
	const maxEdgeWeight = $derived(
		networkData?.edges.reduce((max, e) => Math.max(max, e.weight), 1) ?? 10
	);

	const filteredEdgeCount = $derived(
		networkData?.edges.filter((e) => e.weight >= minEdgeWeight).length ?? 0
	);

	const nodeSizeOptions: { value: NodeSizeBy; label: string }[] = [
		{ value: 'count', label: 'network.size_by_count' },
		{ value: 'degree', label: 'network.size_by_degree' },
		{ value: 'strength', label: 'network.size_by_strength' }
	];

	async function loadData() {
		try {
			loading = true;
			error = null;

			const response = await fetch(`${base}/data/networks/spatial.json`);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			networkData = await response.json();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load network data';
			console.error('Failed to load network data:', e);
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		loadData();
	});

	// Event handlers
	function handleNodeClick(node: NetworkNode | null) {
		selectedNode = node;
	}

	function handleNodeHover(node: NetworkNode | null) {
		hoveredNode = node;
	}

	function handleClosePanel() {
		selectedNode = null;
	}

	function handleSelectNodeFromPanel(node: NetworkNode) {
		selectedNode = node;
		if (mapComponent) {
			mapComponent.focusNode(node.id);
		}
	}

	function handleResetView() {
		if (mapComponent) {
			mapComponent.resetView();
		}
	}

	function handleNodeSizeChange(value: string | undefined) {
		if (value) {
			nodeSizeBy = value as NodeSizeBy;
		}
	}

	function handleSliderChange(value: number) {
		minEdgeWeight = value;
	}
</script>

<svelte:head>
	<title>{t('network_map.title')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 py-6">
	<!-- Page Header -->
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight text-foreground">{t('network_map.title')}</h1>
		<p class="text-muted-foreground">{t('network_map.description')}</p>
	</div>

	{#if loading}
		<div class="space-y-4">
			<div class="grid gap-4 md:grid-cols-4">
				{#each Array(4) as _, i (i)}
					<Skeleton class="h-24" />
				{/each}
			</div>
			<Skeleton class="h-150" />
		</div>
	{:else if error}
		<Card.Root class="p-6">
			<div class="py-12 text-center">
				<h3 class="mb-2 text-xl font-semibold text-destructive">{t('common.error')}</h3>
				<p class="text-muted-foreground">{error}</p>
				<p class="mt-4 text-sm text-muted-foreground">
					{t('network.run_script_hint')}
				</p>
			</div>
		</Card.Root>
	{:else if networkData}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-4">
			<StatsCard title={t('network.total_locations')} value={networkData.meta.totalNodes} />
			<StatsCard title={t('network.total_connections')} value={filteredEdgeCount} />
			<StatsCard
				title={t('network.articles_with_connections')}
				value={networkData.meta.articlesWithMultipleLocations}
			/>
			<StatsCard
				title={t('network.geocoding_rate')}
				value={`${networkData.meta.geocodingSuccessRate}%`}
			/>
		</div>

		<!-- Controls -->
		<Card.Root>
			<Card.Content class="py-4">
				<div class="flex flex-wrap items-center gap-4">
					<!-- Node Size Selector -->
					<div class="flex items-center gap-2">
						<Label class="text-sm font-medium">{t('network.node_size')}:</Label>
						<Select.Root type="single" value={nodeSizeBy} onValueChange={handleNodeSizeChange}>
							<Select.Trigger class="w-40">
								{t(nodeSizeOptions.find((o) => o.value === nodeSizeBy)?.label || '')}
							</Select.Trigger>
							<Select.Content>
								{#each nodeSizeOptions as option (option.value)}
									<Select.Item value={option.value}>{t(option.label)}</Select.Item>
								{/each}
							</Select.Content>
						</Select.Root>
					</div>

					<!-- Edge Weight Filter -->
					<div class="flex items-center gap-2">
						<Label class="text-sm font-medium">{t('network.min_edge_weight')}:</Label>
						<div class="flex w-35 items-center gap-2">
							<Slider
								type="single"
								value={minEdgeWeight}
								min={1}
								max={maxEdgeWeight}
								step={1}
								onValueChange={handleSliderChange}
								class="flex-1"
							/>
							<span class="w-8 text-right text-sm text-muted-foreground">{minEdgeWeight}</span>
						</div>
					</div>

					<!-- Reset View -->
					<div class="ml-auto">
						<Button variant="outline" size="sm" onclick={handleResetView}>
							<Maximize2 class="mr-1 h-4 w-4" />
							{t('network.reset_view')}
						</Button>
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Main Visualization -->
		<Card.Root class="relative overflow-hidden">
			<div class="h-150">
				<NetworkMapView
					bind:this={mapComponent}
					nodes={networkData.nodes}
					edges={networkData.edges}
					selectedNodeId={selectedNode?.id}
					{nodeSizeBy}
					{minEdgeWeight}
					bounds={networkData.bounds}
					onNodeClick={handleNodeClick}
					onNodeHover={handleNodeHover}
				/>

				<!-- Legend -->
				<NetworkLegend
					{nodeSizeBy}
					nodeCount={networkData.nodes.length}
					edgeCount={filteredEdgeCount}
				/>

				<!-- Node Detail Panel -->
				<NetworkNodePanel
					node={selectedNode}
					edges={networkData.edges}
					allNodes={networkData.nodes}
					onClose={handleClosePanel}
					onSelectNode={handleSelectNodeFromPanel}
				/>
			</div>
		</Card.Root>

		<!-- Instructions -->
		<Card.Root>
			<Card.Content class="py-4">
				<p class="text-sm text-muted-foreground">
					<strong>{t('network.tip')}:</strong>
					{t('network_map.instructions')}
				</p>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

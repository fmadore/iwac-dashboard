<script lang="ts">
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Slider } from '$lib/components/ui/slider/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { NetworkGraph, NetworkEntitySearch } from '$lib/components/visualizations/network/index.js';
	import { StatsCard } from '$lib/components/dashboard/index.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import type {
		GlobalNetworkData,
		GlobalNetworkNode,
		GlobalNetworkEdge,
		EntityType,
		NodeSizeBy
	} from '$lib/types/network.js';
	import {
		ZoomIn,
		ZoomOut,
		Maximize2,
		Users,
		Building2,
		Calendar,
		Tag,
		MapPin,
		Focus,
		X,
		Hash,
		FileText
	} from '@lucide/svelte';

	// URL sync
	const urlSync = useUrlSync();

	// Data state
	let networkData = $state<GlobalNetworkData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// View state
	let nodeSizeBy = $state<NodeSizeBy>('strength');
	let minEdgeWeight = $state(5); // Higher default for less clutter
	let maxNodes = $state(100); // Show more nodes now that we filter by type
	let selectedNode = $state<GlobalNetworkNode | null>(null);
	let autoFocusOnSelect = $state(true); // Auto-zoom to selection
	let focusMode = $state(false); // When true, show ego network only

	// Entity type filters - all enabled by default
	let enabledTypes = $state<Set<EntityType>>(
		new Set(['person', 'organization', 'event', 'subject', 'location'])
	);

	// Component ref
	let graphComponent: ReturnType<typeof NetworkGraph> | null = $state(null);

	// Derive URL params for entity selection
	const urlEntityId = $derived(urlSync.filters.entity);
	const urlFocusMode = $derived(urlSync.filters.focus === 'true');

	// Entity type config with colors and icons
	const entityTypeConfig: Record<EntityType, { label: string; color: string; icon: typeof Users }> =
		{
			person: { label: 'network.type_person', color: '#3b82f6', icon: Users },
			organization: { label: 'network.type_organization', color: '#8b5cf6', icon: Building2 },
			event: { label: 'network.type_event', color: '#f97316', icon: Calendar },
			subject: { label: 'network.type_subject', color: '#22c55e', icon: Tag },
			location: { label: 'network.type_location', color: '#ec4899', icon: MapPin },
			topic: { label: 'topic_network.topics', color: '#22c55e', icon: Hash },
			article: { label: 'topic_network.articles', color: '#3b82f6', icon: FileText }
		};

	// Filter nodes by enabled types
	const filteredNodes = $derived.by(() => {
		if (!networkData) return [];
		return networkData.nodes
			.filter((n) => enabledTypes.has(n.type))
			.sort((a, b) => a.labelPriority - b.labelPriority || b.strength - a.strength)
			.slice(0, maxNodes);
	});

	const filteredNodeIds = $derived(new Set(filteredNodes.map((n) => n.id)));

	// Filter edges - both endpoints must be visible
	const filteredEdges = $derived.by(() => {
		if (!networkData) return [];
		return networkData.edges.filter(
			(e) =>
				e.weight >= minEdgeWeight && filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
		);
	});

	// Ego network for focus mode - shows ALL edges connected to selected node (ignoring weight filter)
	const egoNetworkData = $derived.by(() => {
		if (!focusMode || !selectedNode || !networkData) return null;

		const selectedId = selectedNode.id;

		// Get ALL edges connected to selected node from raw data (ignore weight filter)
		const egoEdges = networkData.edges.filter(
			(e) => e.source === selectedId || e.target === selectedId
		);

		// Get all neighbor IDs from these edges
		const neighborIds = new Set<string>();
		neighborIds.add(selectedId);
		for (const edge of egoEdges) {
			neighborIds.add(edge.source);
			neighborIds.add(edge.target);
		}

		// Get neighbor nodes that exist and match enabled types
		const egoNodes = networkData.nodes.filter(
			(n) => neighborIds.has(n.id) && enabledTypes.has(n.type)
		);

		// Filter edges to only include those where both endpoints are in egoNodes
		const egoNodeIds = new Set(egoNodes.map((n) => n.id));
		const validEgoEdges = egoEdges.filter(
			(e) => egoNodeIds.has(e.source) && egoNodeIds.has(e.target)
		);

		return { nodes: egoNodes, edges: validEgoEdges };
	});

	// Display nodes/edges - use ego network in focus mode, filtered otherwise
	const displayNodes = $derived(focusMode && egoNetworkData ? egoNetworkData.nodes : filteredNodes);
	const displayEdges = $derived(focusMode && egoNetworkData ? egoNetworkData.edges : filteredEdges);

	// Stats
	const maxEdgeWeight = $derived(networkData?.meta.weightMax ?? 50);
	const filteredEdgeCount = $derived(displayEdges.length);

	// Count nodes by type for legend
	const nodeCountsByType = $derived.by(() => {
		const counts: Record<EntityType, number> = {
			person: 0,
			organization: 0,
			event: 0,
			subject: 0,
			location: 0,
			topic: 0,
			article: 0
		};
		for (const node of filteredNodes) {
			counts[node.type]++;
		}
		return counts;
	});

	const nodeSizeOptions: { value: NodeSizeBy; label: string }[] = [
		{ value: 'count', label: 'network.size_by_count' },
		{ value: 'degree', label: 'network.size_by_degree' },
		{ value: 'strength', label: 'network.size_by_strength' }
	];

	async function loadData() {
		try {
			loading = true;
			error = null;

			const response = await fetch(`${base}/data/networks/global.json`);
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

	// Sync URL → state on load (restore entity selection from URL)
	$effect(() => {
		if (networkData && urlEntityId && !selectedNode) {
			const node = networkData.nodes.find((n) => n.id === urlEntityId);
			if (node) {
				selectedNode = node;
				focusMode = urlFocusMode;
				// Focus on the node after graph is ready
				if (graphComponent) {
					requestAnimationFrame(() => {
						graphComponent?.focusOnSelection(node.id);
					});
				}
			}
		}
	});

	// Event handlers
	function handleNodeClick(node: GlobalNetworkNode | null) {
		selectedNode = node;
		focusMode = false; // Exit focus mode when clicking a new node or stage

		// Update URL
		if (node) {
			urlSync.setFilter('entity', node.id);
		} else {
			urlSync.clearFilter('entity');
		}
		urlSync.clearFilter('focus');

		// Auto-focus on the selected node and its neighbors
		if (node && autoFocusOnSelect && graphComponent) {
			// Small delay to let selection state propagate
			requestAnimationFrame(() => {
				graphComponent?.focusOnSelection(node.id);
			});
		}
	}

	function handleSearchSelect(node: GlobalNetworkNode | null) {
		selectedNode = node;
		focusMode = false;

		// Update URL
		if (node) {
			urlSync.setFilter('entity', node.id);
		} else {
			urlSync.clearFilter('entity');
		}
		urlSync.clearFilter('focus');

		if (node && graphComponent) {
			// Always focus when selecting from search
			requestAnimationFrame(() => {
				graphComponent?.focusOnSelection(node.id);
			});
		}
	}

	function handleClosePanel() {
		selectedNode = null;
		focusMode = false;
		urlSync.clearFilter('entity');
		urlSync.clearFilter('focus');
	}

	function handleFocusSelected() {
		if (selectedNode && graphComponent) {
			focusMode = true;
			urlSync.setFilter('focus', 'true');
			graphComponent.focusOnSelection(selectedNode.id);
		}
	}

	function handleExitFocusMode() {
		focusMode = false;
		urlSync.clearFilter('focus');
	}

	function handleZoomIn() {
		graphComponent?.zoomIn();
	}

	function handleZoomOut() {
		graphComponent?.zoomOut();
	}

	function handleResetCamera() {
		graphComponent?.resetCamera();
	}

	function handleNodeSizeChange(value: string | undefined) {
		if (value) {
			nodeSizeBy = value as NodeSizeBy;
		}
	}

	function handleSliderChange(value: number) {
		minEdgeWeight = value;
	}

	function handleMaxNodesChange(value: number) {
		maxNodes = value;
	}

	function toggleEntityType(type: EntityType) {
		const newSet = new Set(enabledTypes);
		if (newSet.has(type)) {
			// Don't allow disabling all types
			if (newSet.size > 1) {
				newSet.delete(type);
			}
		} else {
			newSet.add(type);
		}
		enabledTypes = newSet;
	}
</script>

<svelte:head>
	<title>{t('network.title')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 py-6">
	<!-- Page Header -->
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight text-foreground">{t('network.title')}</h1>
		<p class="text-muted-foreground">{t('network.description')}</p>
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
			<StatsCard title={t('network.total_entities')} value={networkData.meta.totalNodes} />
			<StatsCard title={t('network.visible_nodes')} value={displayNodes.length} />
			<StatsCard title={t('network.visible_edges')} value={filteredEdgeCount} />
			<StatsCard title={t('network.max_weight')} value={networkData.meta.weightMax} />
		</div>

		<!-- Entity Type Filters -->
		<Card.Root>
			<Card.Content class="py-4">
				<div class="space-y-3">
					<Label class="text-sm font-medium">{t('network.entity_types')}:</Label>
					<div class="flex flex-wrap gap-2">
						{#each Object.entries(entityTypeConfig) as [type, config] (type)}
							{@const Icon = config.icon}
							{@const isEnabled = enabledTypes.has(type as EntityType)}
							{@const count = nodeCountsByType[type as EntityType]}
							<button
								class="flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs sm:text-sm sm:px-3 sm:py-1.5 sm:gap-2 transition-all"
								class:opacity-40={!isEnabled}
								style:background-color={isEnabled ? `${config.color}20` : 'transparent'}
								style:border-color={config.color}
								onclick={() => toggleEntityType(type as EntityType)}
							>
								<span style="color: {config.color}"><Icon class="h-3.5 w-3.5 sm:h-4 sm:w-4" /></span>
								<span class="hidden xs:inline">{t(config.label)}</span>
								<Badge variant="secondary" class="h-4 px-1 text-[10px] sm:ml-1 sm:h-5 sm:px-1.5 sm:text-xs">{count}</Badge>
							</button>
						{/each}
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Search and Controls -->
		<Card.Root>
			<Card.Content class="py-4">
				<div class="space-y-4">
					<!-- Search Bar - Full Width on Mobile -->
					<div class="flex flex-col gap-3 sm:flex-row sm:items-center">
						<div class="w-full sm:w-72 lg:w-80">
							<NetworkEntitySearch
								nodes={filteredNodes}
								selectedNode={selectedNode}
								onSelect={handleSearchSelect}
							/>
						</div>
						<!-- Focus button when node is selected -->
						{#if selectedNode}
							<Button
								variant="outline"
								size="sm"
								onclick={handleFocusSelected}
								class="shrink-0"
							>
								<Focus class="h-4 w-4 mr-2" />
								{t('network.focus_selection')}
							</Button>
						{/if}
						<!-- Zoom Controls - Move to right on larger screens -->
						<div class="flex items-center gap-1 sm:ml-auto">
							<Button
								variant="outline"
								size="icon"
								onclick={handleZoomIn}
								title={t('network.zoom_in')}
							>
								<ZoomIn class="h-4 w-4" />
							</Button>
							<Button
								variant="outline"
								size="icon"
								onclick={handleZoomOut}
								title={t('network.zoom_out')}
							>
								<ZoomOut class="h-4 w-4" />
							</Button>
							<Button
								variant="outline"
								size="icon"
								onclick={handleResetCamera}
								title={t('network.reset_view')}
							>
								<Maximize2 class="h-4 w-4" />
							</Button>
						</div>
					</div>

					<!-- Filter Controls - Responsive Grid -->
					<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
						<!-- Node Size Selector -->
						<div class="flex items-center gap-2">
							<Label class="text-sm font-medium whitespace-nowrap">{t('network.node_size')}:</Label>
							<Select.Root type="single" value={nodeSizeBy} onValueChange={handleNodeSizeChange}>
								<Select.Trigger class="flex-1 min-w-0">
									{t(nodeSizeOptions.find((o) => o.value === nodeSizeBy)?.label || '')}
								</Select.Trigger>
								<Select.Content>
									{#each nodeSizeOptions as option (option.value)}
										<Select.Item value={option.value}>{t(option.label)}</Select.Item>
									{/each}
								</Select.Content>
							</Select.Root>
						</div>

						<!-- Max Nodes Filter -->
						<div class="flex items-center gap-2">
							<Label class="text-sm font-medium whitespace-nowrap">{t('network.max_nodes')}:</Label>
							<div class="flex flex-1 items-center gap-2">
								<Slider
									type="single"
									value={maxNodes}
									min={20}
									max={300}
									step={20}
									onValueChange={handleMaxNodesChange}
									class="flex-1"
								/>
								<span class="w-10 text-right text-sm text-muted-foreground">{maxNodes}</span>
							</div>
						</div>

						<!-- Edge Weight Filter -->
						<div class="flex items-center gap-2">
							<Label class="text-sm font-medium whitespace-nowrap">{t('network.min_edge_weight')}:</Label>
							<div class="flex flex-1 items-center gap-2">
								<Slider
									type="single"
									value={minEdgeWeight}
									min={2}
									max={Math.min(maxEdgeWeight, 50)}
									step={1}
									onValueChange={handleSliderChange}
									class="flex-1"
								/>
								<span class="w-8 text-right text-sm text-muted-foreground">{minEdgeWeight}</span>
							</div>
						</div>
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Main Visualization -->
		<Card.Root class="relative overflow-hidden">
			<div class="h-150">
				<NetworkGraph
					bind:this={graphComponent}
					nodes={displayNodes}
					edges={displayEdges}
					selectedNodeId={selectedNode?.id}
					{nodeSizeBy}
					entityTypeColors={entityTypeConfig}
					{focusMode}
					onNodeClick={handleNodeClick}
				/>

				<!-- Focus Mode Indicator -->
				{#if focusMode && selectedNode}
					<div class="absolute top-4 left-4 z-20">
						<Badge variant="secondary" class="flex items-center gap-2 px-3 py-1.5">
							<Focus class="h-3.5 w-3.5" />
							<span>{t('network.focus_mode')}</span>
							<button
								class="ml-1 rounded-full p-0.5 hover:bg-muted"
								onclick={handleExitFocusMode}
								title={t('network.exit_focus')}
							>
								<X class="h-3 w-3" />
							</button>
						</Badge>
					</div>
				{/if}

				<!-- Legend - Hidden on mobile when entity panel is visible -->
				<div
					class="absolute left-4 z-10 flex flex-col gap-2 rounded-lg border bg-card/95 p-3 text-sm shadow-sm backdrop-blur-sm
					       {selectedNode ? 'hidden sm:flex sm:bottom-4' : 'bottom-4'}"
				>
					<div class="font-medium">{t('network.legend')}</div>
					{#each Object.entries(entityTypeConfig) as [type, config] (type)}
						{#if enabledTypes.has(type as EntityType)}
							{@const Icon = config.icon}
							<div class="flex items-center gap-2">
								<div class="h-3 w-3 rounded-full" style:background-color={config.color}></div>
								<span style="color: {config.color}"><Icon class="h-3.5 w-3.5" /></span>
								<span class="text-muted-foreground">{t(config.label)}</span>
							</div>
						{/if}
					{/each}
					<div class="mt-1 border-t pt-2 text-xs text-muted-foreground">
						{t('network.nodes')}: {displayNodes.length} • {t('network.edges')}: {filteredEdgeCount}
						{#if focusMode}
							<div class="mt-1 text-primary">{t('network.showing_all_connections')}</div>
						{/if}
					</div>
				</div>

				<!-- Selected Node Panel - Responsive positioning -->
				{#if selectedNode}
					{@const nodeColor = entityTypeConfig[selectedNode.type].color}
					{@const NodeIcon = entityTypeConfig[selectedNode.type].icon}
					<div
						class="absolute z-20 rounded-lg border bg-card/95 shadow-lg backdrop-blur-sm
						       bottom-4 left-4 right-4 p-3
						       sm:bottom-auto sm:top-4 sm:right-4 sm:left-auto sm:w-64 sm:p-4
						       lg:w-72"
					>
						<div class="flex items-start justify-between gap-2">
							<div class="min-w-0 flex-1">
								<div class="flex items-center gap-2">
									<span style="color: {nodeColor}">
										<NodeIcon class="h-4 w-4 shrink-0" />
									</span>
									<h3 class="truncate font-semibold text-sm sm:text-base">{selectedNode.label}</h3>
								</div>
								<Badge variant="outline" class="mt-1 text-xs">
									{t(entityTypeConfig[selectedNode.type].label)}
								</Badge>
							</div>
							<div class="flex items-center gap-1">
								<Button
									variant={focusMode ? 'default' : 'ghost'}
									size="sm"
									class="h-7 w-7 p-0"
									onclick={focusMode ? handleExitFocusMode : handleFocusSelected}
									title={focusMode ? t('network.exit_focus') : t('network.focus_selection')}
								>
									<Focus class="h-4 w-4" />
								</Button>
								<Button variant="ghost" size="sm" class="h-7 w-7 p-0" onclick={handleClosePanel}>
									<X class="h-4 w-4" />
								</Button>
							</div>
						</div>
						<div class="mt-3 grid grid-cols-3 gap-1.5 sm:gap-2 text-center">
							<div class="rounded bg-muted p-1.5 sm:p-2">
								<div class="text-base sm:text-lg font-bold">{selectedNode.count}</div>
								<div class="text-[10px] sm:text-xs text-muted-foreground">{t('network.articles')}</div>
							</div>
							<div class="rounded bg-muted p-1.5 sm:p-2">
								<div class="text-base sm:text-lg font-bold">{selectedNode.degree}</div>
								<div class="text-[10px] sm:text-xs text-muted-foreground">{t('network.connections')}</div>
							</div>
							<div class="rounded bg-muted p-1.5 sm:p-2">
								<div class="text-base sm:text-lg font-bold">{selectedNode.strength}</div>
								<div class="text-[10px] sm:text-xs text-muted-foreground">{t('network.strength')}</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		</Card.Root>

		<!-- Instructions -->
		<Card.Root>
			<Card.Content class="py-4">
				<p class="text-sm text-muted-foreground">
					<strong>{t('network.tip')}:</strong>
					{t('network.instructions')}
				</p>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

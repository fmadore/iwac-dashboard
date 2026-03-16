<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Slider } from '$lib/components/ui/slider/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import {
		NetworkGraph,
		NetworkEntitySearch,
		type LayoutType
	} from '$lib/components/visualizations/network/index.js';
	import { EgoNetworkPanel } from '$lib/components/visualizations/knowledge-graph/index.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import type {
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
		BookMarked,
		Waypoints,
		CircleDot,
		Network,
		GitBranch,
		Link2,
		Info
	} from '@lucide/svelte';

	let { data: pageData } = $props();

	// URL sync
	const urlSync = useUrlSync();

	// Raw KG data
	const rawGraph = $derived(pageData.graph);
	const ontology = $derived(pageData.ontology);
	const kgStats = $derived(pageData.stats);

	// Raw data types from JSON
	interface RawKGNode {
		id: string;
		type: string;
		label: string;
		properties?: { frequency?: number; url?: string };
		degree?: number;
		strength?: number;
		labelPriority?: number;
	}

	interface RawKGEdge {
		source: string;
		target: string;
		type?: string;
		weight?: number;
		weightNorm?: number;
	}

	// KG node type → EntityType mapping
	const typeMapping: Record<string, EntityType> = {
		Person: 'person',
		Organization: 'organization',
		Place: 'location',
		Event: 'event',
		Subject: 'subject',
		Authority: 'authority'
	};

	// Transform KG data to GlobalNetworkNode/Edge format
	const allNodes = $derived.by<GlobalNetworkNode[]>(() => {
		if (!rawGraph?.nodes) return [];
		return rawGraph.nodes.map(
			(n: RawKGNode): GlobalNetworkNode => ({
				id: n.id,
				type: typeMapping[n.type] || ('subject' as EntityType),
				label: n.label,
				count: n.properties?.frequency || 0,
				degree: n.degree || 0,
				strength: n.strength || 0,
				labelPriority: n.labelPriority || 9999,
				o_id: n.properties?.url
			})
		);
	});

	const allEdges = $derived.by<GlobalNetworkEdge[]>(() => {
		if (!rawGraph?.edges) return [];
		return rawGraph.edges.map(
			(e: RawKGEdge): GlobalNetworkEdge => ({
				source: e.source,
				target: e.target,
				type: e.type || 'unknown',
				weight: e.weight || 1,
				weightNorm: e.weightNorm || 0,
				articleIds: []
			})
		);
	});

	// View state
	let nodeSizeBy = $state<NodeSizeBy>('strength');
	let minEdgeWeight = $state(5);
	let maxNodes = $state(200);
	let selectedNode = $state<GlobalNetworkNode | null>(null);
	let focusMode = $state(false);
	let layoutType = $state<LayoutType>('force');

	// Entity type filters
	const mainEntityTypes: EntityType[] = [
		'person',
		'organization',
		'event',
		'subject',
		'location',
		'authority'
	];
	let enabledNodeTypes = $state<Set<EntityType>>(new Set(mainEntityTypes));

	// Edge type filters
	const edgeTypes = [
		'part_of',
		'located_in',
		'related_to',
		'has_part',
		'succeeded_by',
		'co_occurs_with',
		'co_authored_with'
	];
	let enabledEdgeTypes = $state<Set<string>>(new Set(edgeTypes));

	// Edge layer toggle (explicit vs inferred)
	let showExplicit = $state(true);
	let showInferred = $state(true);

	const explicitEdgeTypes = new Set([
		'part_of',
		'has_part',
		'related_to',
		'succeeded_by',
		'located_in'
	]);
	const inferredEdgeTypes = new Set(['co_occurs_with', 'co_authored_with']);

	// Component ref
	let graphComponent: ReturnType<typeof NetworkGraph> | null = $state(null);

	// URL state
	const urlEntityId = $derived(urlSync.filters.entity);

	// Entity type config
	const entityTypeConfig: Record<string, { label: string; color: string; icon: typeof Users }> = {
		person: { label: 'network.type_person', color: '#3b82f6', icon: Users },
		organization: { label: 'network.type_organization', color: '#8b5cf6', icon: Building2 },
		event: { label: 'network.type_event', color: '#f97316', icon: Calendar },
		subject: { label: 'network.type_subject', color: '#22c55e', icon: Tag },
		location: { label: 'network.type_location', color: '#ec4899', icon: MapPin },
		authority: { label: 'kg.type_authority', color: '#78716c', icon: BookMarked }
	};

	// Edge type colors
	const edgeTypeColors: Record<string, string> = {
		part_of: '#a855f7',
		has_part: '#c084fc',
		related_to: '#f59e0b',
		succeeded_by: '#ef4444',
		located_in: '#06b6d4',
		co_occurs_with: '#6b7280',
		co_authored_with: '#10b981'
	};

	const edgeTypeConfig: Record<
		string,
		{ label: string; layer: 'explicit' | 'inferred'; icon: typeof GitBranch }
	> = {
		part_of: { label: 'kg.edge_part_of', layer: 'explicit', icon: GitBranch },
		has_part: { label: 'kg.edge_has_part', layer: 'explicit', icon: GitBranch },
		related_to: { label: 'kg.edge_related_to', layer: 'explicit', icon: Link2 },
		succeeded_by: { label: 'kg.edge_succeeded_by', layer: 'explicit', icon: GitBranch },
		located_in: { label: 'kg.edge_located_in', layer: 'explicit', icon: MapPin },
		co_occurs_with: { label: 'kg.edge_co_occurs', layer: 'inferred', icon: Link2 },
		co_authored_with: { label: 'kg.edge_co_authored', layer: 'inferred', icon: Users }
	};

	// Filter nodes by enabled types
	const filteredNodes = $derived.by(() => {
		return allNodes
			.filter((n) => enabledNodeTypes.has(n.type))
			.sort((a, b) => a.labelPriority - b.labelPriority || b.strength - a.strength)
			.slice(0, maxNodes);
	});

	const filteredNodeIds = $derived(new Set(filteredNodes.map((n) => n.id)));

	// Filter edges by type, layer, weight, and visible endpoints
	const filteredEdges = $derived.by(() => {
		return allEdges.filter((e) => {
			// Edge type filter
			if (!enabledEdgeTypes.has(e.type)) return false;

			// Layer filter
			if (explicitEdgeTypes.has(e.type) && !showExplicit) return false;
			if (inferredEdgeTypes.has(e.type) && !showInferred) return false;

			// Weight filter (only for co-occurrence edges)
			if (e.type === 'co_occurs_with' && e.weight < minEdgeWeight) return false;

			// Both endpoints visible
			return filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target);
		});
	});

	// Ego network for focus mode
	const egoNetworkData = $derived.by(() => {
		if (!focusMode || !selectedNode) return null;

		const selectedId = selectedNode.id;

		const egoEdges = allEdges.filter((e) => {
			if (e.source !== selectedId && e.target !== selectedId) return false;
			if (!enabledEdgeTypes.has(e.type)) return false;
			if (explicitEdgeTypes.has(e.type) && !showExplicit) return false;
			if (inferredEdgeTypes.has(e.type) && !showInferred) return false;
			return true;
		});

		const neighborIds = new Set<string>();
		neighborIds.add(selectedId);
		for (const edge of egoEdges) {
			neighborIds.add(edge.source);
			neighborIds.add(edge.target);
		}

		const egoNodes = allNodes.filter(
			(n) => neighborIds.has(n.id) && enabledNodeTypes.has(n.type)
		);
		const egoNodeIds = new Set(egoNodes.map((n) => n.id));
		const validEgoEdges = egoEdges.filter(
			(e) => egoNodeIds.has(e.source) && egoNodeIds.has(e.target)
		);

		return { nodes: egoNodes, edges: validEgoEdges };
	});

	// Display data
	const displayNodes = $derived(
		focusMode && egoNetworkData ? egoNetworkData.nodes : filteredNodes
	);
	const displayEdges = $derived(
		focusMode && egoNetworkData ? egoNetworkData.edges : filteredEdges
	);

	// Stats
	const nodeCountsByType = $derived.by(() => {
		const counts: Record<string, number> = {};
		for (const type of mainEntityTypes) counts[type] = 0;
		for (const node of filteredNodes) counts[node.type]++;
		return counts;
	});

	const edgeCountsByType = $derived.by(() => {
		const counts: Record<string, number> = {};
		for (const type of edgeTypes) counts[type] = 0;
		for (const edge of displayEdges) counts[edge.type]++;
		return counts;
	});

	// Node size options
	const nodeSizeOptions: { value: NodeSizeBy; label: string }[] = [
		{ value: 'count', label: 'network.size_by_count' },
		{ value: 'degree', label: 'network.size_by_degree' },
		{ value: 'strength', label: 'network.size_by_strength' }
	];

	const layoutOptions: { value: LayoutType; label: string; icon: typeof Network }[] = [
		{ value: 'force', label: 'network.layout_force', icon: Waypoints },
		{ value: 'circular', label: 'network.layout_circular', icon: CircleDot },
		{ value: 'radial', label: 'network.layout_radial', icon: Network }
	];

	// Restore from URL
	$effect(() => {
		if (allNodes.length > 0 && urlEntityId && !selectedNode) {
			const node = allNodes.find((n) => n.id === urlEntityId);
			if (node) {
				selectedNode = node;
				if (graphComponent) {
					requestAnimationFrame(() => {
						graphComponent?.focusOnSelection(node.id);
					});
				}
			}
		}
	});

	// Handlers
	function handleNodeClick(node: GlobalNetworkNode | null) {
		selectedNode = node;
		focusMode = false;

		if (node) {
			urlSync.setFilter('entity', node.id);
		} else {
			urlSync.clearFilter('entity');
		}

		if (node && graphComponent) {
			requestAnimationFrame(() => {
				graphComponent?.focusOnSelection(node.id);
			});
		}
	}

	function handleSearchSelect(node: GlobalNetworkNode | null) {
		selectedNode = node;
		focusMode = false;

		if (node) {
			urlSync.setFilter('entity', node.id);
		} else {
			urlSync.clearFilter('entity');
		}

		if (node && graphComponent) {
			requestAnimationFrame(() => {
				graphComponent?.focusOnSelection(node.id);
			});
		}
	}

	function handleEgoNodeClick(node: GlobalNetworkNode) {
		selectedNode = node;
		focusMode = true;

		urlSync.setFilter('entity', node.id);

		if (graphComponent) {
			requestAnimationFrame(() => {
				graphComponent?.focusOnSelection(node.id);
			});
		}
	}

	function handleClosePanel() {
		selectedNode = null;
		focusMode = false;
		urlSync.clearFilter('entity');
	}

	function handleFocusSelected() {
		if (selectedNode && graphComponent) {
			focusMode = true;
			graphComponent.focusOnSelection(selectedNode.id);
		}
	}

	function handleExitFocusMode() {
		focusMode = false;
	}

	function toggleEntityType(type: EntityType) {
		const newSet = new Set(enabledNodeTypes);
		if (newSet.has(type)) {
			if (newSet.size > 1) newSet.delete(type);
		} else {
			newSet.add(type);
		}
		enabledNodeTypes = newSet;
	}

	function toggleEdgeType(type: string) {
		const newSet = new Set(enabledEdgeTypes);
		if (newSet.has(type)) {
			if (newSet.size > 1) newSet.delete(type);
		} else {
			newSet.add(type);
		}
		enabledEdgeTypes = newSet;
	}

	function toggleExplicitLayer() {
		if (showExplicit && !showInferred) return; // keep at least one
		showExplicit = !showExplicit;
	}

	function toggleInferredLayer() {
		if (showInferred && !showExplicit) return;
		showInferred = !showInferred;
	}

	function handleNodeSizeChange(value: string | undefined) {
		if (value) nodeSizeBy = value as NodeSizeBy;
	}

	function handleLayoutChange(value: string | undefined) {
		if (value) layoutType = value as LayoutType;
	}
</script>

<svelte:head>
	<title>{t('kg.title')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-4 py-4">
	<!-- Compact Header -->
	<div class="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
		<div>
			<h1 class="text-2xl font-bold tracking-tight text-foreground">{t('kg.title')}</h1>
			<p class="text-sm text-muted-foreground">{t('kg.description')}</p>
		</div>
		{#if kgStats}
			<div class="flex gap-4 text-sm text-muted-foreground">
				<span><strong class="text-foreground">{(kgStats.summary?.totalNodes ?? 0).toLocaleString()}</strong> {t('kg.total_entities').toLowerCase()}</span>
				<span><strong class="text-foreground">{(kgStats.summary?.explicitEdges ?? 0).toLocaleString()}</strong> {t('kg.explicit_edges').toLowerCase()}</span>
				<span><strong class="text-foreground">{(kgStats.summary?.inferredEdges ?? 0).toLocaleString()}</strong> {t('kg.inferred_edges').toLowerCase()}</span>
			</div>
		{/if}
	</div>

	{#if !rawGraph}
		<Card.Root class="p-6">
			<div class="py-12 text-center">
				<h3 class="mb-2 text-xl font-semibold text-destructive">{t('common.error')}</h3>
				<p class="text-muted-foreground">{t('kg.run_script_hint')}</p>
			</div>
		</Card.Root>
	{:else}
		<!-- Controls -->
		<Card.Root>
			<Card.Content class="py-3">
				<!-- Row 1: Entity types with help -->
				<div class="flex flex-wrap items-start gap-x-6 gap-y-2">
					<div class="space-y-1">
						<div class="flex items-center gap-1.5">
							<Label class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{t('network.entity_types')}</Label>
							<span class="group relative">
								<Info class="h-3 w-3 text-muted-foreground/50 cursor-help" />
								<span class="pointer-events-none absolute bottom-full left-1/2 z-50 mb-1 w-72 -translate-x-1/2 rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground opacity-0 shadow-md transition-opacity group-hover:opacity-100">
									{t('kg.nodes_help')}
								</span>
							</span>
						</div>
						<div class="flex flex-wrap items-center gap-1.5">
							{#each mainEntityTypes as type (type)}
								{@const config = entityTypeConfig[type]}
								{@const Icon = config.icon}
								{@const isEnabled = enabledNodeTypes.has(type)}
								{@const count = nodeCountsByType[type] || 0}
								<button
									class="flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs transition-all"
									class:opacity-40={!isEnabled}
									style:background-color={isEnabled ? `${config.color}15` : 'transparent'}
									style:border-color={config.color}
									onclick={() => toggleEntityType(type)}
									title={t(config.label)}
								>
									<span style:color={config.color}><Icon class="h-3 w-3" /></span>
									<span class="hidden sm:inline">{t(config.label)}</span>
									<span class="text-muted-foreground">{count}</span>
								</button>
							{/each}
						</div>
					</div>

					<div class="hidden h-10 w-px self-stretch bg-border sm:block"></div>

					<!-- Edge layers -->
					<div class="space-y-1">
						<div class="flex items-center gap-1.5">
							<Label class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{t('kg.edge_layers')}</Label>
							<span class="group relative">
								<Info class="h-3 w-3 text-muted-foreground/50 cursor-help" />
								<span class="pointer-events-none absolute bottom-full left-1/2 z-50 mb-1 w-72 -translate-x-1/2 rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground opacity-0 shadow-md transition-opacity group-hover:opacity-100">
									{t('kg.explicit_help')}
								</span>
							</span>
						</div>
						<div class="flex items-center gap-1.5">
							<button
								class="flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs transition-all"
								class:opacity-40={!showExplicit}
								style:background-color={showExplicit ? '#a855f715' : 'transparent'}
								style:border-color="#a855f7"
								onclick={toggleExplicitLayer}
								title={t('kg.explicit_help')}
							>
								<span style:color="#a855f7"><GitBranch class="h-3 w-3" /></span>
								<span>{t('kg.layer_explicit')}</span>
								<span class="text-muted-foreground">{kgStats?.summary?.explicitEdges ?? 0}</span>
							</button>
							<button
								class="flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs transition-all"
								class:opacity-40={!showInferred}
								style:background-color={showInferred ? '#6b728015' : 'transparent'}
								style:border-color="#6b7280"
								onclick={toggleInferredLayer}
								title={t('kg.inferred_help')}
							>
								<span style:color="#6b7280"><Link2 class="h-3 w-3" /></span>
								<span>{t('kg.layer_inferred')}</span>
								<span class="text-muted-foreground">{kgStats?.summary?.inferredEdges ?? 0}</span>
							</button>
						</div>
					</div>

					<div class="hidden h-10 w-px self-stretch bg-border sm:block"></div>

					<!-- Edge type toggles -->
					<div class="space-y-1">
						<Label class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{t('kg.edge_types')}</Label>
						<div class="flex flex-wrap items-center gap-1">
							{#each edgeTypes as type (type)}
								{@const config = edgeTypeConfig[type]}
								{@const isEnabled = enabledEdgeTypes.has(type)}
								{@const count = edgeCountsByType[type] || 0}
								{@const layerActive =
									config.layer === 'explicit' ? showExplicit : showInferred}
								<button
									class="flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[11px] transition-all"
									class:opacity-20={!layerActive}
									class:opacity-40={layerActive && !isEnabled}
									style:background-color={isEnabled && layerActive
										? `${edgeTypeColors[type]}15`
										: 'transparent'}
									style:border-color={edgeTypeColors[type]}
									onclick={() => toggleEdgeType(type)}
									disabled={!layerActive}
									title={t(config.label)}
								>
									<div
										class="h-1.5 w-1.5 rounded-full"
										style:background-color={edgeTypeColors[type]}
									></div>
									<span>{t(config.label)}</span>
									<span class="text-muted-foreground">{count}</span>
								</button>
							{/each}
						</div>
					</div>
				</div>

				<!-- Row 2: Search + controls -->
				<div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 border-t pt-2">
					<div class="w-56">
						<NetworkEntitySearch
							nodes={filteredNodes}
							{selectedNode}
							onSelect={handleSearchSelect}
						/>
					</div>

					<div class="flex items-center gap-2">
						<Label class="whitespace-nowrap text-xs text-muted-foreground">{t('network.max_nodes')}:</Label>
						<Slider
							type="single"
							value={maxNodes}
							min={50}
							max={500}
							step={50}
							onValueChange={(v) => (maxNodes = v)}
							class="w-24"
						/>
						<span class="w-8 text-right text-xs text-muted-foreground">{maxNodes}</span>
					</div>

					<div class="flex items-center gap-2">
						<Label class="whitespace-nowrap text-xs text-muted-foreground">{t('network.min_edge_weight')}:</Label>
						<Slider
							type="single"
							value={minEdgeWeight}
							min={1}
							max={50}
							step={1}
							onValueChange={(v) => (minEdgeWeight = v)}
							class="w-24"
						/>
						<span class="w-6 text-right text-xs text-muted-foreground">{minEdgeWeight}</span>
					</div>

					<div class="flex items-center gap-2">
						<Label class="whitespace-nowrap text-xs text-muted-foreground">{t('network.layout')}:</Label>
						<Select.Root type="single" value={layoutType} onValueChange={handleLayoutChange}>
							<Select.Trigger class="h-7 w-36 text-xs">
								{@const current = layoutOptions.find((o) => o.value === layoutType)}
								{#if current}
									<span class="flex items-center gap-1.5">
										<current.icon class="h-3 w-3" />
										{t(current.label)}
									</span>
								{/if}
							</Select.Trigger>
							<Select.Content>
								{#each layoutOptions as option (option.value)}
									<Select.Item value={option.value}>
										<span class="flex items-center gap-1.5">
											<option.icon class="h-3 w-3" />
											{t(option.label)}
										</span>
									</Select.Item>
								{/each}
							</Select.Content>
						</Select.Root>
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Graph Card — full width, tall, with floating panels -->
		<Card.Root class="relative overflow-hidden">
			<div class="h-[calc(100vh-240px)] min-h-[500px]">
				<NetworkGraph
					bind:this={graphComponent}
					nodes={displayNodes}
					edges={displayEdges}
					selectedNodeId={selectedNode?.id}
					{nodeSizeBy}
					{layoutType}
					entityTypeColors={entityTypeConfig}
					{focusMode}
					showFullscreenButton={false}
					onNodeClick={handleNodeClick}
				/>

				<!-- Zoom Toolbar (top-right) -->
				<div class="absolute right-2 top-2 z-40 flex items-center gap-1">
					<Button
						variant="outline"
						size="icon"
						class="h-[30px] w-[30px] bg-background/80 backdrop-blur-sm"
						onclick={() => graphComponent?.zoomIn()}
						title={t('network.zoom_in')}
					>
						<ZoomIn class="h-4 w-4" />
					</Button>
					<Button
						variant="outline"
						size="icon"
						class="h-[30px] w-[30px] bg-background/80 backdrop-blur-sm"
						onclick={() => graphComponent?.zoomOut()}
						title={t('network.zoom_out')}
					>
						<ZoomOut class="h-4 w-4" />
					</Button>
					<Button
						variant="outline"
						size="icon"
						class="h-[30px] w-[30px] bg-background/80 backdrop-blur-sm"
						onclick={() => graphComponent?.resetCamera()}
						title={t('network.reset_view')}
					>
						<Maximize2 class="h-4 w-4" />
					</Button>

					{#if selectedNode}
						<div class="mx-1 h-5 w-px bg-border"></div>
						<Button
							variant={focusMode ? 'default' : 'outline'}
							size="icon"
							class="h-[30px] w-[30px] {focusMode
								? ''
								: 'bg-background/80 backdrop-blur-sm'}"
							onclick={focusMode ? handleExitFocusMode : handleFocusSelected}
							title={focusMode
								? t('network.exit_focus')
								: t('network.focus_selection')}
						>
							<Focus class="h-4 w-4" />
						</Button>
						<Button
							variant="outline"
							size="icon"
							class="h-[30px] w-[30px] bg-background/80 backdrop-blur-sm"
							onclick={handleClosePanel}
							title={t('common.close')}
						>
							<X class="h-4 w-4" />
						</Button>
					{/if}
				</div>

				<!-- Focus mode badge -->
				{#if focusMode && selectedNode}
					<div class="absolute bottom-4 right-4 z-10">
						<Badge variant="secondary" class="text-xs">
							<Focus class="mr-1 h-3 w-3" />
							{t('network.focus_mode')}
						</Badge>
					</div>
				{/if}

				<!-- Node Legend (bottom-left) -->
				<div
					class="absolute bottom-4 left-4 z-10 flex flex-col gap-1 rounded-lg border bg-card/95 p-2.5 text-xs shadow-sm backdrop-blur-sm"
					class:hidden={!!selectedNode && typeof window !== 'undefined' && window.innerWidth < 640}
				>
					{#each mainEntityTypes as type (type)}
						{#if enabledNodeTypes.has(type) && (nodeCountsByType[type] || 0) > 0}
							{@const config = entityTypeConfig[type]}
							{@const Icon = config.icon}
							<div class="flex items-center gap-1.5">
								<div
									class="h-2 w-2 rounded-full"
									style:background-color={config.color}
								></div>
								<span style:color={config.color}><Icon class="h-3 w-3" /></span>
								<span class="text-muted-foreground">{t(config.label)}</span>
							</div>
						{/if}
					{/each}
					<div class="border-t pt-1 text-[10px] text-muted-foreground">
						{displayNodes.length} {t('network.nodes').toLowerCase()} &bull; {displayEdges.length} {t('network.edges').toLowerCase()}
					</div>
				</div>

				<!-- Floating Ego Network Panel (top-right, inside graph) -->
				{#if selectedNode}
					{@const nodeConfig = entityTypeConfig[selectedNode.type]}
					{@const NodeIcon = nodeConfig?.icon || Tag}
					<div
						class="absolute bottom-4 left-4 right-4 z-20 max-h-[calc(100%-60px)] overflow-y-auto rounded-xl border bg-card/95 shadow-lg backdrop-blur-sm sm:bottom-auto sm:left-auto sm:right-4 sm:top-12 sm:w-80"
					>
						<!-- Panel Header -->
						<div class="sticky top-0 z-10 border-b bg-card/95 p-3 backdrop-blur-sm">
							<div class="flex items-start justify-between gap-2">
								<div class="flex items-center gap-2 min-w-0">
									<div
										class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full"
										style:background-color="{nodeConfig?.color || '#888'}20"
									>
										<span style:color={nodeConfig?.color || '#888'}>
											<NodeIcon class="h-3.5 w-3.5" />
										</span>
									</div>
									<div class="min-w-0">
										<div class="truncate text-sm font-semibold">{selectedNode.label}</div>
										<span
											class="inline-flex items-center rounded-full border px-1.5 py-px text-[10px] font-medium"
											style="border-color: {nodeConfig?.color}; color: {nodeConfig?.color}"
										>
											{t(nodeConfig?.label || '')}
										</span>
									</div>
								</div>
								<Button
									variant="ghost"
									size="icon"
									class="h-6 w-6 shrink-0"
									onclick={handleClosePanel}
								>
									<X class="h-3.5 w-3.5" />
								</Button>
							</div>
							<!-- Compact stats -->
							<div class="mt-2 flex gap-3 text-center text-[10px]">
								<div>
									<div class="text-sm font-bold">{selectedNode.count || 0}</div>
									<div class="text-muted-foreground">{t('network.articles')}</div>
								</div>
								<div class="h-6 w-px bg-border"></div>
								<div>
									<div class="text-sm font-bold">{selectedNode.degree}</div>
									<div class="text-muted-foreground">{t('network.connections')}</div>
								</div>
								<div class="h-6 w-px bg-border"></div>
								<div>
									<div class="text-sm font-bold">{selectedNode.strength}</div>
									<div class="text-muted-foreground">{t('network.strength')}</div>
								</div>
							</div>
						</div>
						<!-- Ego Network Content -->
						<div class="p-3">
							<EgoNetworkPanel
								{selectedNode}
								allNodes={allNodes}
								allEdges={allEdges}
								entityTypeColors={entityTypeConfig}
								{edgeTypeColors}
								onNodeClick={handleEgoNodeClick}
							/>
						</div>
					</div>
				{/if}
			</div>
		</Card.Root>
	{/if}
</div>

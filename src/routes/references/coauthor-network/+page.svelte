<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Slider } from '$lib/components/ui/slider/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { NetworkGraph, NetworkEntitySearch } from '$lib/components/visualizations/network/index.js';
	import { StatsCard } from '$lib/components/dashboard/index.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import type { NodeSizeBy, GlobalNetworkNode, GlobalNetworkEdge, EntityType } from '$lib/types/network.js';
	import {
		ZoomIn,
		ZoomOut,
		Maximize2,
		Users,
		Building2,
		Calendar,
		Tag,
		MapPin,
		Hash,
		FileText,
		Focus,
		X,
		ExternalLink
	} from '@lucide/svelte';

	// Build islam.zmo.de URL based on current language
	function getItemUrl(oId: string): string {
		const lang = languageStore.current;
		const path = lang === 'fr' ? 'afrique_ouest' : 'westafrica';
		return `https://islam.zmo.de/s/${path}/item/${oId}`;
	}

	// Type definitions for co-author network (compatible with GlobalNetworkNode)
	interface CoauthorNetworkNode extends GlobalNetworkNode {
		type: 'author';
	}

	interface CoauthorNetworkEdge extends GlobalNetworkEdge {
		type: 'coauthor';
	}

	interface CoauthorNetworkMeta {
		generatedAt: string;
		totalNodes: number;
		totalEdges: number;
		weightMinActual: number;
		weightMax: number;
		degree: { min: number; max: number; mean: number };
		strength: { min: number; max: number; mean: number };
	}

	interface CoauthorNetworkData {
		nodes: CoauthorNetworkNode[];
		edges: CoauthorNetworkEdge[];
		meta: CoauthorNetworkMeta;
	}

	// URL sync
	const urlSync = useUrlSync();

	// Get preloaded data from +page.ts
	let { data: pageData } = $props<{
		data: {
			networkData: CoauthorNetworkData | null;
			error: string | null;
		};
	}>();

	const networkData = $derived(pageData.networkData);
	const error = $derived(pageData.error);

	// View state
	let nodeSizeBy = $state<NodeSizeBy>('strength');
	let minEdgeWeight = $state(2); // Min co-authorships to show
	let maxNodes = $state(150);
	let selectedNode = $state<CoauthorNetworkNode | null>(null);
	let autoFocusOnSelect = $state(true);
	let focusMode = $state(false);

	// Component ref
	let graphComponent: ReturnType<typeof NetworkGraph> | null = $state(null);

	// Derive URL params for entity selection
	const urlEntityId = $derived(urlSync.filters.entity);
	const urlFocusMode = $derived(urlSync.filters.focus === 'true');

	// Entity type config (need all types for NetworkGraph compatibility)
	const entityTypeConfig: Record<EntityType, { label: string; color: string; icon: typeof Users }> = {
		author: { label: 'coauthor.author', color: '#3b82f6', icon: Users },
		person: { label: 'network.type_person', color: '#3b82f6', icon: Users },
		organization: { label: 'network.type_organization', color: '#8b5cf6', icon: Building2 },
		event: { label: 'network.type_event', color: '#f97316', icon: Calendar },
		subject: { label: 'network.type_subject', color: '#22c55e', icon: Tag },
		location: { label: 'network.type_location', color: '#ec4899', icon: MapPin },
		topic: { label: 'topic_network.topics', color: '#22c55e', icon: Hash },
		article: { label: 'topic_network.articles', color: '#3b82f6', icon: FileText }
	};

	// Filter nodes
	const filteredNodes = $derived.by(() => {
		if (!networkData) return [];
		return networkData.nodes
			.sort((a: CoauthorNetworkNode, b: CoauthorNetworkNode) => a.labelPriority - b.labelPriority || b.strength - a.strength)
			.slice(0, maxNodes);
	});

	const filteredNodeIds = $derived(new Set(filteredNodes.map((n: CoauthorNetworkNode) => n.id)));

	// Filter edges - both endpoints must be visible
	const filteredEdges = $derived.by(() => {
		if (!networkData) return [];
		return networkData.edges.filter(
			(e: CoauthorNetworkEdge) =>
				e.weight >= minEdgeWeight && filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
		);
	});

	// Ego network for focus mode
	const egoNetworkData = $derived.by(() => {
		if (!focusMode || !selectedNode || !networkData) return null;

		const selectedId = selectedNode.id;

		// Get ALL edges connected to selected node
		const egoEdges = networkData.edges.filter(
			(e: CoauthorNetworkEdge) => e.source === selectedId || e.target === selectedId
		);

		// Get all neighbor IDs
		const neighborIds = new Set<string>();
		neighborIds.add(selectedId);
		for (const edge of egoEdges) {
			neighborIds.add(edge.source);
			neighborIds.add(edge.target);
		}

		// Get neighbor nodes
		const egoNodes = networkData.nodes.filter((n: CoauthorNetworkNode) => neighborIds.has(n.id));

		// Filter edges to only include those where both endpoints are in egoNodes
		const egoNodeIds = new Set(egoNodes.map((n: CoauthorNetworkNode) => n.id));
		const validEgoEdges = egoEdges.filter(
			(e: CoauthorNetworkEdge) => egoNodeIds.has(e.source) && egoNodeIds.has(e.target)
		);

		return { nodes: egoNodes, edges: validEgoEdges };
	});

	// Display nodes/edges
	const displayNodes = $derived(focusMode && egoNetworkData ? egoNetworkData.nodes : filteredNodes);
	const displayEdges = $derived(focusMode && egoNetworkData ? egoNetworkData.edges : filteredEdges);

	// Stats
	const maxEdgeWeight = $derived(networkData?.meta.weightMax ?? 20);
	const filteredEdgeCount = $derived(displayEdges.length);

	const nodeSizeOptions: { value: NodeSizeBy; label: string }[] = [
		{ value: 'count', label: 'coauthor.size_by_publications' },
		{ value: 'degree', label: 'coauthor.size_by_coauthors' },
		{ value: 'strength', label: 'coauthor.size_by_collaborations' }
	];

	// Sync URL -> state on load
	$effect(() => {
		if (networkData && urlEntityId && !selectedNode) {
			const node = networkData.nodes.find((n: CoauthorNetworkNode) => n.id === urlEntityId);
			if (node) {
				selectedNode = node;
				focusMode = urlFocusMode;
				if (graphComponent) {
					requestAnimationFrame(() => {
						graphComponent?.focusOnSelection(node.id);
					});
				}
			}
		}
	});

	// Event handlers
	function handleNodeClick(node: CoauthorNetworkNode | null) {
		selectedNode = node;
		focusMode = false;

		if (node) {
			urlSync.setFilter('entity', node.id);
		} else {
			urlSync.clearFilter('entity');
		}
		urlSync.clearFilter('focus');

		if (node && autoFocusOnSelect && graphComponent) {
			requestAnimationFrame(() => {
				graphComponent?.focusOnSelection(node.id);
			});
		}
	}

	function handleSearchSelect(node: CoauthorNetworkNode | null) {
		selectedNode = node;
		focusMode = false;

		if (node) {
			urlSync.setFilter('entity', node.id);
		} else {
			urlSync.clearFilter('entity');
		}
		urlSync.clearFilter('focus');

		if (node && graphComponent) {
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
</script>

<svelte:head>
	<title>{t('nav.coauthor_network')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 py-6">
	<!-- Page Header -->
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight text-foreground">{t('coauthor.title')}</h1>
		<p class="text-muted-foreground">{t('coauthor.description')}</p>
	</div>

	{#if !networkData && !error}
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
					{t('coauthor.run_script_hint')}
				</p>
			</div>
		</Card.Root>
	{:else if networkData}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-4">
			<StatsCard title={t('coauthor.total_authors')} value={networkData.meta.totalNodes} />
			<StatsCard title={t('coauthor.total_collaborations')} value={networkData.meta.totalEdges} />
			<StatsCard title={t('coauthor.visible_authors')} value={displayNodes.length} />
			<StatsCard title={t('coauthor.visible_connections')} value={filteredEdgeCount} />
		</div>

		<!-- Search and Controls -->
		<Card.Root>
			<Card.Content class="py-4">
				<div class="space-y-4">
					<!-- Search Bar -->
					<div class="flex flex-col gap-3 sm:flex-row sm:items-center">
						<div class="w-full sm:w-72 lg:w-80">
							<NetworkEntitySearch
								nodes={filteredNodes as GlobalNetworkNode[]}
								selectedNode={selectedNode as GlobalNetworkNode | null}
								onSelect={(node) => handleSearchSelect(node as CoauthorNetworkNode | null)}
							/>
						</div>
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
						<!-- Zoom Controls -->
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

					<!-- Filter Controls -->
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

						<!-- Max Authors Filter -->
						<div class="flex items-center gap-2">
							<Label class="text-sm font-medium whitespace-nowrap">{t('coauthor.max_authors')}:</Label>
							<div class="flex flex-1 items-center gap-2">
								<Slider
									type="single"
									value={maxNodes}
									min={50}
									max={500}
									step={50}
									onValueChange={handleMaxNodesChange}
									class="flex-1"
								/>
								<span class="w-10 text-right text-sm text-muted-foreground">{maxNodes}</span>
							</div>
						</div>

						<!-- Min Co-authorships Filter -->
						<div class="flex items-center gap-2">
							<Label class="text-sm font-medium whitespace-nowrap">{t('coauthor.min_coauthorships')}:</Label>
							<div class="flex flex-1 items-center gap-2">
								<Slider
									type="single"
									value={minEdgeWeight}
									min={1}
									max={Math.min(maxEdgeWeight, 20)}
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
					nodes={displayNodes as GlobalNetworkNode[]}
					edges={displayEdges as GlobalNetworkEdge[]}
					selectedNodeId={selectedNode?.id}
					{nodeSizeBy}
					entityTypeColors={entityTypeConfig}
					{focusMode}
					onNodeClick={(node) => handleNodeClick(node as CoauthorNetworkNode | null)}
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

				<!-- Legend -->
				<div
					class="absolute left-4 z-10 flex flex-col gap-2 rounded-lg border bg-card/95 p-3 text-sm shadow-sm backdrop-blur-sm
					       {selectedNode ? 'hidden sm:flex sm:bottom-4' : 'bottom-4'}"
				>
					<div class="font-medium">{t('network.legend')}</div>
					<div class="flex items-center gap-2">
						<div class="h-3 w-3 rounded-full" style:background-color="#3b82f6"></div>
						<Users class="h-3.5 w-3.5" style="color: #3b82f6" />
						<span class="text-muted-foreground">{t('coauthor.authors')}</span>
					</div>
					<div class="mt-1 border-t pt-2 text-xs text-muted-foreground">
						{t('network.nodes')}: {displayNodes.length} | {t('network.edges')}: {filteredEdgeCount}
						{#if focusMode}
							<div class="mt-1 text-primary">{t('network.showing_all_connections')}</div>
						{/if}
					</div>
				</div>

				<!-- Selected Node Panel -->
				{#if selectedNode}
					<div
						class="absolute z-20 rounded-lg border bg-card/95 shadow-lg backdrop-blur-sm
						       bottom-4 left-4 right-4 p-3
						       sm:bottom-auto sm:top-4 sm:right-4 sm:left-auto sm:w-64 sm:p-4
						       lg:w-72"
					>
						<div class="flex items-start justify-between gap-2">
							<div class="min-w-0 flex-1">
								<div class="flex items-center gap-2">
									<span style="color: #3b82f6">
										<Users class="h-4 w-4 shrink-0" />
									</span>
									<h3 class="truncate font-semibold text-sm sm:text-base">{selectedNode.label}</h3>
								</div>
								<Badge variant="outline" class="mt-1 text-xs">
									{t('coauthor.author')}
								</Badge>
							</div>
							<div class="flex items-center gap-1">
								{#if selectedNode.o_id}
									<a
										href={getItemUrl(selectedNode.o_id)}
										target="_blank"
										rel="noopener noreferrer"
										class="inline-flex h-7 w-7 items-center justify-center rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
										title={t('common.view_on_iwac')}
									>
										<ExternalLink class="h-4 w-4" />
									</a>
								{/if}
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
								<div class="text-[10px] sm:text-xs text-muted-foreground">{t('coauthor.publications')}</div>
							</div>
							<div class="rounded bg-muted p-1.5 sm:p-2">
								<div class="text-base sm:text-lg font-bold">{selectedNode.degree}</div>
								<div class="text-[10px] sm:text-xs text-muted-foreground">{t('coauthor.coauthors')}</div>
							</div>
							<div class="rounded bg-muted p-1.5 sm:p-2">
								<div class="text-base sm:text-lg font-bold">{selectedNode.strength}</div>
								<div class="text-[10px] sm:text-xs text-muted-foreground">{t('coauthor.joint_pubs')}</div>
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
					{t('coauthor.instructions')}
				</p>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

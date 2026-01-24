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
	import {
		NetworkGraph,
		TopicSidebar,
		ArticleDetailPanel
	} from '$lib/components/visualizations/network/index.js';
	import { StatsCard } from '$lib/components/dashboard/index.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import type {
		TopicNetworkData,
		TopicNetworkNode,
		TopicNetworkTopicNode,
		TopicNetworkArticleNode
	} from '$lib/types/topicNetwork.js';
	import { isTopicNode, isArticleNode } from '$lib/types/topicNetwork.js';
	import {
		ZoomIn,
		ZoomOut,
		Maximize2,
		Hash,
		FileText,
		Focus,
		X
	} from '@lucide/svelte';

	// URL sync
	const urlSync = useUrlSync();

	// Data state
	let networkData = $state<TopicNetworkData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// View state
	let minEdgeWeight = $state(0.3);
	let selectedTopicFilter = $state<string | null>(null);
	let selectedNode = $state<TopicNetworkNode | null>(null);
	let focusMode = $state(false);

	// Component refs
	let graphComponent: ReturnType<typeof NetworkGraph> | null = $state(null);

	// URL params
	const urlTopicFilter = $derived(urlSync.filters.topic);
	const urlEntityId = $derived(urlSync.filters.entity);

	// Entity type config for topic network (includes all EntityType values for type compatibility)
	const entityTypeConfig = {
		topic: { label: 'topic_network.topics', color: '#22c55e', icon: Hash },
		article: { label: 'topic_network.articles', color: '#3b82f6', icon: FileText },
		// Below are placeholder values for unused entity types (required for type compatibility)
		person: { label: 'network.type_person', color: '#3b82f6', icon: FileText },
		organization: { label: 'network.type_organization', color: '#8b5cf6', icon: FileText },
		event: { label: 'network.type_event', color: '#f97316', icon: FileText },
		subject: { label: 'network.type_subject', color: '#22c55e', icon: FileText },
		location: { label: 'network.type_location', color: '#ec4899', icon: FileText },
		author: { label: 'coauthor.author', color: '#3b82f6', icon: FileText }
	};

	// Extract topics from network data
	const topics = $derived.by(() => {
		if (!networkData) return [];
		return networkData.nodes.filter(isTopicNode).sort((a, b) => b.count - a.count);
	});

	// Filter nodes based on selected topic filter and edge weight
	const filteredNodes = $derived.by(() => {
		if (!networkData) return [];

		// If a topic is selected, show only that topic and its connected articles
		if (selectedTopicFilter) {
			const topicNode = networkData.nodes.find((n) => n.id === selectedTopicFilter);
			if (!topicNode) return [];

			// Get article IDs connected to this topic above threshold
			const connectedArticleIds = new Set(
				networkData.edges
					.filter((e) => e.source === selectedTopicFilter && e.weight >= minEdgeWeight)
					.map((e) => e.target)
			);

			return networkData.nodes.filter(
				(n) => n.id === selectedTopicFilter || connectedArticleIds.has(n.id)
			);
		}

		// Show all nodes (topics always, articles filtered by weight)
		const connectedArticleIds = new Set(
			networkData.edges.filter((e) => e.weight >= minEdgeWeight).map((e) => e.target)
		);

		return networkData.nodes.filter((n) => isTopicNode(n) || connectedArticleIds.has(n.id));
	});

	const filteredNodeIds = $derived(new Set(filteredNodes.map((n) => n.id)));

	// Filter edges based on weight threshold and visible nodes
	const filteredEdges = $derived.by(() => {
		if (!networkData) return [];
		return networkData.edges.filter(
			(e) =>
				e.weight >= minEdgeWeight && filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
		);
	});

	// Ego network for focus mode
	const egoNetworkData = $derived.by(() => {
		if (!focusMode || !selectedNode || !networkData) return null;

		const selectedId = selectedNode.id;
		const egoEdges = networkData.edges.filter(
			(e) => e.source === selectedId || e.target === selectedId
		);

		const neighborIds = new Set<string>();
		neighborIds.add(selectedId);
		for (const edge of egoEdges) {
			neighborIds.add(edge.source);
			neighborIds.add(edge.target);
		}

		const egoNodes = networkData.nodes.filter((n) => neighborIds.has(n.id));
		const egoNodeIds = new Set(egoNodes.map((n) => n.id));
		const validEgoEdges = egoEdges.filter(
			(e) => egoNodeIds.has(e.source) && egoNodeIds.has(e.target)
		);

		return { nodes: egoNodes, edges: validEgoEdges };
	});

	// Display nodes/edges - use ego network in focus mode
	const displayNodes = $derived(focusMode && egoNetworkData ? egoNetworkData.nodes : filteredNodes);
	const displayEdges = $derived(focusMode && egoNetworkData ? egoNetworkData.edges : filteredEdges);

	// Stats
	const topicCount = $derived(displayNodes.filter(isTopicNode).length);
	const articleCount = $derived(displayNodes.filter(isArticleNode).length);

	// Node size calculation - topics larger based on count, articles smaller
	const nodeSizes = $derived.by(() => {
		const sizes: Record<string, number> = {};
		let maxTopicCount = 1;

		for (const node of displayNodes) {
			if (isTopicNode(node) && node.count > maxTopicCount) {
				maxTopicCount = node.count;
			}
		}

		for (const node of displayNodes) {
			if (isTopicNode(node)) {
				// Topics: larger nodes (15-30)
				sizes[node.id] = 15 + (node.count / maxTopicCount) * 15;
			} else {
				// Articles: smaller fixed size
				sizes[node.id] = 6;
			}
		}

		return sizes;
	});

	// Convert to GlobalNetworkNode format for NetworkGraph compatibility
	const graphNodes = $derived.by(() => {
		return displayNodes.map((node) => ({
			id: node.id,
			type: node.type as 'topic' | 'article',
			label: node.label,
			count: isTopicNode(node) ? node.count : 1,
			degree: node.degree,
			strength: node.strength,
			labelPriority: node.labelPriority
		}));
	});

	const graphEdges = $derived.by(() => {
		return displayEdges.map((edge) => ({
			source: edge.source,
			target: edge.target,
			type: 'topic-article',
			weight: edge.weight,
			weightNorm: edge.weightNorm,
			articleIds: []
		}));
	});

	// Topic filter options
	const topicFilterOptions = $derived.by(() => {
		return [
			{ value: '', label: t('topic_network.all_topics') },
			...topics.map((topic) => ({
				value: topic.id,
				label: `${topic.keywords[0] || topic.label} (${topic.count})`
			}))
		];
	});

	async function loadData() {
		try {
			loading = true;
			error = null;

			const response = await fetch(`${base}/data/networks/topic-network.json`);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			networkData = await response.json();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load network data';
			console.error('Failed to load topic network data:', e);
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		loadData();
	});

	// Sync URL → state on load
	$effect(() => {
		if (networkData && urlTopicFilter && !selectedTopicFilter) {
			selectedTopicFilter = urlTopicFilter;
		}
		if (networkData && urlEntityId && !selectedNode) {
			const node = networkData.nodes.find((n) => n.id === urlEntityId);
			if (node) {
				selectedNode = node;
			}
		}
	});

	function handleTopicFilterChange(value: string | undefined) {
		selectedTopicFilter = value || null;
		if (value) {
			urlSync.setFilter('topic', value);
		} else {
			urlSync.clearFilter('topic');
		}
	}

	function handleSidebarTopicSelect(topic: TopicNetworkTopicNode | null) {
		if (topic) {
			selectedTopicFilter = topic.id;
			urlSync.setFilter('topic', topic.id);
		} else {
			selectedTopicFilter = null;
			urlSync.clearFilter('topic');
		}
	}

	function handleNodeClick(node: any) {
		if (!node) {
			selectedNode = null;
			urlSync.clearFilter('entity');
			return;
		}

		// Find the original node in our data
		const originalNode = networkData?.nodes.find((n) => n.id === node.id);
		if (originalNode) {
			selectedNode = originalNode;
			urlSync.setFilter('entity', originalNode.id);
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

	function handleZoomIn() {
		graphComponent?.zoomIn();
	}

	function handleZoomOut() {
		graphComponent?.zoomOut();
	}

	function handleResetCamera() {
		graphComponent?.resetCamera();
	}

	function handleSliderChange(value: number) {
		minEdgeWeight = value;
	}
</script>

<svelte:head>
	<title>{t('topic_network.title')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 py-6">
	<!-- Page Header -->
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight text-foreground">{t('topic_network.title')}</h1>
		<p class="text-muted-foreground">{t('topic_network.description')}</p>
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
					{t('topic_network.run_script_hint')}
				</p>
			</div>
		</Card.Root>
	{:else if networkData}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-4">
			<StatsCard title={t('topic_network.topics')} value={topicCount} />
			<StatsCard title={t('topic_network.articles')} value={articleCount} />
			<StatsCard
				title={t('topic_network.avg_probability')}
				value={`${(networkData.meta.avgTopicProb * 100).toFixed(1)}%`}
			/>
			<StatsCard title={t('topic_network.connections')} value={displayEdges.length} />
		</div>

		<!-- Controls -->
		<Card.Root>
			<Card.Content class="py-4">
				<div class="flex flex-col gap-4 sm:flex-row sm:items-center">
					<!-- Topic Filter -->
					<div class="flex items-center gap-2">
						<Label class="whitespace-nowrap text-sm font-medium"
							>{t('topic_network.filter_by_topic')}:</Label
						>
						<Select.Root
							type="single"
							value={selectedTopicFilter || ''}
							onValueChange={handleTopicFilterChange}
						>
							<Select.Trigger class="w-56">
								{selectedTopicFilter
									? topicFilterOptions.find((o) => o.value === selectedTopicFilter)?.label
									: t('topic_network.all_topics')}
							</Select.Trigger>
							<Select.Content class="max-h-80">
								{#each topicFilterOptions as option (option.value)}
									<Select.Item value={option.value}>{option.label}</Select.Item>
								{/each}
							</Select.Content>
						</Select.Root>
					</div>

					<!-- Probability Threshold -->
					<div class="flex items-center gap-2">
						<Label class="whitespace-nowrap text-sm font-medium"
							>{t('topic_network.link_threshold')}:</Label
						>
						<div class="flex flex-1 items-center gap-2">
							<Slider
								type="single"
								value={minEdgeWeight}
								min={0.1}
								max={0.9}
								step={0.1}
								onValueChange={handleSliderChange}
								class="w-32"
							/>
							<span class="w-12 text-right text-sm text-muted-foreground"
								>{(minEdgeWeight * 100).toFixed(0)}%</span
							>
						</div>
					</div>

					<!-- Focus button when node is selected -->
					{#if selectedNode}
						<Button variant="outline" size="sm" onclick={handleFocusSelected} class="shrink-0">
							<Focus class="mr-2 h-4 w-4" />
							{t('network.focus_selection')}
						</Button>
					{/if}

					<!-- Zoom Controls -->
					<div class="flex items-center gap-1 sm:ml-auto">
						<Button variant="outline" size="icon" onclick={handleZoomIn} title={t('network.zoom_in')}>
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
			</Card.Content>
		</Card.Root>

		<!-- Main Layout: Sidebar + Graph + Detail Panel -->
		<div class="grid gap-4 lg:grid-cols-[280px,1fr]">
			<!-- Topic Sidebar -->
			<Card.Root class="hidden h-150 overflow-hidden lg:block">
				<TopicSidebar
					{topics}
					selectedTopicId={selectedTopicFilter}
					onTopicSelect={handleSidebarTopicSelect}
				/>
			</Card.Root>

			<!-- Network Graph -->
			<Card.Root class="relative overflow-hidden">
				<div class="h-150">
					<NetworkGraph
						bind:this={graphComponent}
						nodes={graphNodes}
						edges={graphEdges}
						selectedNodeId={selectedNode?.id}
						nodeSizeBy="count"
						entityTypeColors={entityTypeConfig}
						{focusMode}
						onNodeClick={handleNodeClick}
					/>

					<!-- Focus Mode Indicator -->
					{#if focusMode && selectedNode}
						<div class="absolute left-4 top-4 z-20">
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
						class="absolute bottom-4 left-4 z-10 flex flex-col gap-2 rounded-lg border bg-card/95 p-3 text-sm shadow-sm backdrop-blur-sm"
					>
						<div class="font-medium">{t('network.legend')}</div>
						<div class="flex items-center gap-2">
							<div class="h-4 w-4 rounded-full bg-green-500"></div>
							<Hash class="h-3.5 w-3.5 text-green-500" />
							<span class="text-muted-foreground">{t('topic_network.topics')}</span>
						</div>
						<div class="flex items-center gap-2">
							<div class="h-2.5 w-2.5 rounded-full bg-blue-500"></div>
							<FileText class="h-3.5 w-3.5 text-blue-500" />
							<span class="text-muted-foreground">{t('topic_network.articles')}</span>
						</div>
						<div class="mt-1 border-t pt-2 text-xs text-muted-foreground">
							{t('network.nodes')}: {displayNodes.length} • {t('network.edges')}: {displayEdges.length}
						</div>
					</div>

					<!-- Article Detail Panel -->
					{#if selectedNode && isArticleNode(selectedNode)}
						<ArticleDetailPanel article={selectedNode} onClose={handleClosePanel} />
					{/if}

					<!-- Topic Detail Panel (when a topic node is selected) -->
					{#if selectedNode && isTopicNode(selectedNode)}
						<div
							class="absolute right-4 top-4 z-20 w-72 rounded-lg border bg-card/95 p-4 shadow-lg backdrop-blur-sm lg:w-80"
						>
							<div class="mb-3 flex items-start justify-between gap-2">
								<div class="min-w-0 flex-1">
									<div class="flex items-center gap-2">
										<Hash class="h-4 w-4 shrink-0 text-green-500" />
										<h3 class="font-semibold">{t('topic_network.topic_details')}</h3>
									</div>
								</div>
								<Button variant="ghost" size="sm" class="h-7 w-7 shrink-0 p-0" onclick={handleClosePanel}>
									<X class="h-4 w-4" />
								</Button>
							</div>

							<div class="space-y-2">
								<p class="text-sm font-medium">{selectedNode.label}</p>

								{#if selectedNode.keywords.length > 0}
									<div class="flex flex-wrap gap-1">
										{#each selectedNode.keywords as keyword}
											<Badge variant="secondary" class="text-xs">{keyword}</Badge>
										{/each}
									</div>
								{/if}

								<div class="mt-3 grid grid-cols-2 gap-2 text-center">
									<div class="rounded bg-muted p-2">
										<div class="text-lg font-bold">{selectedNode.count}</div>
										<div class="text-xs text-muted-foreground">{t('topic_network.articles')}</div>
									</div>
									<div class="rounded bg-muted p-2">
										<div class="text-lg font-bold">{selectedNode.degree}</div>
										<div class="text-xs text-muted-foreground">{t('network.connections')}</div>
									</div>
								</div>
							</div>
						</div>
					{/if}
				</div>
			</Card.Root>
		</div>

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

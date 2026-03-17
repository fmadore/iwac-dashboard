<script lang="ts">
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { X, ArrowLeftRight } from '@lucide/svelte';
	import type { GlobalNetworkNode, EntityType } from '$lib/types/network.js';
	import type { EdgeFocusData } from './NetworkGraph.svelte';
	import type { Component } from 'svelte';

	interface EntityTypeConfig {
		label: string;
		color: string;
		icon: Component;
	}

	interface Props {
		data: EdgeFocusData;
		entityTypeColors?: Record<EntityType, EntityTypeConfig>;
		onClose: () => void;
	}

	let { data, entityTypeColors, onClose }: Props = $props();

	function getNodeColor(node: GlobalNetworkNode): string {
		return entityTypeColors?.[node.type]?.color ?? '#666666';
	}

	function getNodeTypeLabel(node: GlobalNetworkNode): string {
		const config = entityTypeColors?.[node.type];
		return config?.label ? t(config.label) : node.type;
	}
</script>

<div
	class="absolute bottom-4 right-4 z-50 w-72 rounded-lg border bg-card/95 shadow-lg backdrop-blur-sm transition-all animate-in fade-in slide-in-from-bottom-2 duration-300"
>
	<!-- Header -->
	<div class="flex items-center justify-between border-b px-3 py-2">
		<div class="flex items-center gap-1.5 text-sm font-semibold">
			<ArrowLeftRight class="h-4 w-4 text-primary" />
			<span>{t('network.edge_focus')}</span>
		</div>
		<button
			onclick={onClose}
			class="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
			title={t('common.close')}
		>
			<X class="h-3.5 w-3.5" />
		</button>
	</div>

	<!-- Endpoint Nodes -->
	<div class="space-y-2 px-3 py-2.5">
		<!-- Source -->
		<div class="flex items-center gap-2">
			<div
				class="h-3 w-3 shrink-0 rounded-full"
				style="background-color: {getNodeColor(data.sourceNode)}"
			></div>
			<div class="min-w-0 flex-1">
				<div class="truncate text-sm font-medium">{data.sourceNode.label}</div>
				<div class="text-xs text-muted-foreground">{getNodeTypeLabel(data.sourceNode)}</div>
			</div>
		</div>

		<!-- Edge weight connector -->
		<div class="flex items-center gap-2 px-1">
			<div class="h-px flex-1 bg-primary/30"></div>
			<span class="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
				{t('network.weight')}: {data.edge.weight}
			</span>
			<div class="h-px flex-1 bg-primary/30"></div>
		</div>

		<!-- Target -->
		<div class="flex items-center gap-2">
			<div
				class="h-3 w-3 shrink-0 rounded-full"
				style="background-color: {getNodeColor(data.targetNode)}"
			></div>
			<div class="min-w-0 flex-1">
				<div class="truncate text-sm font-medium">{data.targetNode.label}</div>
				<div class="text-xs text-muted-foreground">{getNodeTypeLabel(data.targetNode)}</div>
			</div>
		</div>
	</div>

	<!-- Shared articles count -->
	{#if data.edge.articleIds?.length}
		<div class="border-t px-3 py-2">
			<div class="text-xs text-muted-foreground">
				{t('network.shared_articles', [data.edge.articleIds.length])}
			</div>
		</div>
	{/if}

	<!-- Shared neighbors -->
	{#if data.sharedNeighbors.length > 0}
		<div class="border-t px-3 py-2">
			<div class="mb-1.5 text-xs font-medium text-muted-foreground">
				{t('network.shared_neighbors', [data.sharedNeighbors.length])}
			</div>
			<div class="space-y-1 max-h-28 overflow-y-auto">
				{#each data.sharedNeighbors.slice(0, 8) as neighbor (neighbor.id)}
					<div class="flex items-center gap-1.5 text-xs">
						<div
							class="h-2 w-2 shrink-0 rounded-full"
							style="background-color: {getNodeColor(neighbor)}"
						></div>
						<span class="truncate">{neighbor.label}</span>
					</div>
				{/each}
				{#if data.sharedNeighbors.length > 8}
					<div class="text-xs text-muted-foreground">
						+{data.sharedNeighbors.length - 8} {t('network.more')}
					</div>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Hint -->
	<div class="border-t px-3 py-1.5">
		<p class="text-[10px] text-muted-foreground/70">
			{t('network.edge_focus_hint')}
		</p>
	</div>
</div>

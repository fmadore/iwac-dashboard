<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { ScrollArea } from '$lib/components/ui/scroll-area/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import type { NetworkNode, NetworkEdge } from '$lib/types/network.js';
	import { X, MapPin, FileText, Link2 } from '@lucide/svelte';

	interface Props {
		node: NetworkNode | null;
		edges: NetworkEdge[];
		allNodes: NetworkNode[];
		onClose: () => void;
		onSelectNode: (node: NetworkNode) => void;
	}

	let { node, edges, allNodes, onClose, onSelectNode }: Props = $props();

	// Get connected edges for the selected node
	const connectedEdges = $derived.by(() => {
		if (!node) return [];
		return edges
			.filter((e) => e.source === node.id || e.target === node.id)
			.sort((a, b) => b.weight - a.weight);
	});

	// Get connected nodes with their edge weights
	const connections = $derived.by(() => {
		if (!node) return [];
		return connectedEdges.map((edge) => {
			const connectedNodeId = edge.source === node.id ? edge.target : edge.source;
			const connectedNode = allNodes.find((n) => n.id === connectedNodeId);
			return {
				node: connectedNode,
				weight: edge.weight,
				articleCount: edge.articleIds.length
			};
		});
	});
</script>

{#if node}
	<Card.Root class="absolute right-4 top-4 z-10 w-80 max-h-[calc(100%-2rem)] flex flex-col shadow-lg">
		<Card.Header class="shrink-0 pb-2">
			<div class="flex items-start justify-between gap-2">
				<div class="flex-1 min-w-0">
					<Card.Title class="text-lg leading-tight truncate">{node.label}</Card.Title>
					{#if node.country}
						<Card.Description class="flex items-center gap-1 mt-1">
							<MapPin class="h-3 w-3" />
							{node.country}
							{#if node.region}
								<span class="text-muted-foreground/60">• {node.region}</span>
							{/if}
						</Card.Description>
					{/if}
				</div>
				<Button variant="ghost" size="icon" class="h-8 w-8 shrink-0" onclick={onClose}>
					<X class="h-4 w-4" />
				</Button>
			</div>
		</Card.Header>

		<Card.Content class="flex-1 overflow-hidden pt-0">
			<!-- Stats -->
			<div class="grid grid-cols-3 gap-2 mb-4">
				<div class="text-center p-2 bg-muted rounded-md">
					<div class="text-lg font-bold">{node.count}</div>
					<div class="text-xs text-muted-foreground">{t('network.articles')}</div>
				</div>
				<div class="text-center p-2 bg-muted rounded-md">
					<div class="text-lg font-bold">{node.degree}</div>
					<div class="text-xs text-muted-foreground">{t('network.connections')}</div>
				</div>
				<div class="text-center p-2 bg-muted rounded-md">
					<div class="text-lg font-bold">{node.strength}</div>
					<div class="text-xs text-muted-foreground">{t('network.strength')}</div>
				</div>
			</div>

			<!-- Connections List -->
			{#if connections.length > 0}
				<div class="space-y-2">
					<h4 class="text-sm font-medium flex items-center gap-1">
						<Link2 class="h-4 w-4" />
						{t('network.connected_locations')} ({connections.length})
					</h4>
					<ScrollArea class="h-50">
						<div class="space-y-1 pr-4">
							{#each connections as connection (connection.node?.id)}
								{#if connection.node}
									<button
										class="w-full flex items-center justify-between p-2 text-left rounded-md hover:bg-muted transition-colors"
										onclick={() => onSelectNode(connection.node!)}
									>
										<div class="flex-1 min-w-0">
											<div class="text-sm font-medium truncate">{connection.node.label}</div>
											{#if connection.node.country}
												<div class="text-xs text-muted-foreground truncate">
													{connection.node.country}
												</div>
											{/if}
										</div>
										<Badge variant="secondary" class="ml-2 shrink-0">
											<FileText class="h-3 w-3 mr-1" />
											{connection.weight}
										</Badge>
									</button>
								{/if}
							{/each}
						</div>
					</ScrollArea>
				</div>
			{:else}
				<p class="text-sm text-muted-foreground text-center py-4">
					{t('network.no_connections')}
				</p>
			{/if}
		</Card.Content>
	</Card.Root>
{/if}

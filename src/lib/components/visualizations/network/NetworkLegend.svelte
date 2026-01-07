<script lang="ts">
	import { t } from '$lib/stores/translationStore.svelte.js';
	import type { NodeSizeBy } from '$lib/types/network.js';

	interface Props {
		nodeSizeBy: NodeSizeBy;
		nodeCount: number;
		edgeCount: number;
	}

	let { nodeSizeBy, nodeCount, edgeCount }: Props = $props();

	const sizeByLabels: Record<NodeSizeBy, string> = {
		count: 'network.legend_size_count',
		degree: 'network.legend_size_degree',
		strength: 'network.legend_size_strength'
	};
</script>

<div
	class="absolute bottom-4 left-4 z-10 flex flex-col gap-2 rounded-lg border bg-card/95 p-3 text-sm shadow-sm backdrop-blur-sm"
>
	<div class="font-medium">{t('network.legend')}</div>

	<!-- Node size legend -->
	<div class="flex items-center gap-2">
		<div class="flex items-center gap-1">
			<div class="h-2 w-2 rounded-full bg-chart-1"></div>
			<div class="h-3 w-3 rounded-full bg-chart-1"></div>
			<div class="h-4 w-4 rounded-full bg-chart-1"></div>
		</div>
		<span class="text-muted-foreground">{t(sizeByLabels[nodeSizeBy])}</span>
	</div>

	<!-- Edge thickness legend -->
	<div class="flex items-center gap-2">
		<div class="flex items-center gap-1">
			<div class="h-px w-4 bg-muted-foreground"></div>
			<div class="h-0.5 w-4 bg-muted-foreground"></div>
			<div class="h-1 w-4 bg-muted-foreground"></div>
		</div>
		<span class="text-muted-foreground">{t('network.legend_edge_weight')}</span>
	</div>

	<!-- Stats -->
	<div class="mt-1 border-t pt-2 text-xs text-muted-foreground">
		{t('network.nodes')}: {nodeCount} • {t('network.edges')}: {edgeCount}
	</div>
</div>

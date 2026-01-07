<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import LayerChartPieChart from '$lib/components/charts/LayerChartPieChart.svelte';

	interface PieItem {
		label: string;
		value: number;
		color?: string;
	}

	let { title = 'Facet', data = [] }: { title?: string; data?: PieItem[] } = $props();
</script>

<Card.Root>
	<Card.Header>
		<Card.Title>{title}</Card.Title>
	</Card.Header>
	<Card.Content>
		<div class="mx-auto flex aspect-square max-h-100 items-center justify-center">
			{#if data.length > 0}
				<LayerChartPieChart
					{data}
					innerRadius="40%"
					outerRadius="75%"
					showLabels={true}
					showValues={false}
					animationDuration={800}
					minSlicePercent={0.5}
				/>
			{:else}
				<div class="flex h-50 items-center justify-center text-muted-foreground">No data</div>
			{/if}
		</div>
	</Card.Content>
</Card.Root>

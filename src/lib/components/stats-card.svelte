<script lang="ts">
	import { Card } from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';

	let {
		title,
		value,
		trend = '',
		description = ''
	}: {
		title: string;
		value: number | string;
		trend?: string;
		description?: string;
	} = $props();
</script>

<Card class="p-6">
	<div class="flex flex-row items-center justify-between space-y-0 pb-2">
		<h3 class="text-sm font-medium">{title}</h3>
		{#if trend}
			<Badge variant="secondary" class="text-xs">
				{trend}
			</Badge>
		{/if}
	</div>
	<div class="text-2xl font-bold">{value.toLocaleString()}</div>
	{#if description}
		<p class="text-xs text-muted-foreground">{description}</p>
	{/if}
</Card>

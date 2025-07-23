<script lang="ts">
	import { Card } from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';

	export let title: string;
	export let value: number | string;
	export let trend: string = '';
	export let description: string = '';
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

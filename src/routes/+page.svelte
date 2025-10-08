<script lang="ts">
	import { base } from '$app/paths';
	import { Card } from '$lib/components/ui/card/index.js';
	import { overviewStore } from '$lib/stores/overviewStore.svelte.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import OverviewStatsGrid from '$lib/components/overview-stats-grid.svelte';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';

	// Svelte 5: Get store values directly as state
	const loading = $derived(overviewStore.loading);
	const error = $derived(overviewStore.error);
	const summary = $derived(overviewStore.summary);
	const recentItems = $derived(overviewStore.recentItems);

	// Load on mount using $effect
	$effect(() => {
		overviewStore.load();
	});
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{t('nav.overview')}</h2>
		<p class="text-muted-foreground">{t('overview.description')}</p>
	</div>

	{#if loading}
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
			{#each Array(4) as _, i (i)}
				<Card class="p-6">
					<Skeleton class="mb-2 h-4 w-[100px]" />
					<Skeleton class="mb-2 h-8 w-[60px]" />
					<Skeleton class="h-3 w-[120px]" />
				</Card>
			{/each}
		</div>
	{:else if error}
		<Card class="p-6">
			<p class="text-destructive">{t('overview.error')}: {error}</p>
		</Card>
	{:else if summary}
		<OverviewStatsGrid {summary} />

		<Card class="p-6">
			<h3 class="mb-4 text-lg font-semibold">{t('overview.recent_items')}</h3>
			{#if recentItems.length > 0}
				<div class="space-y-2">
					{#each recentItems as item (`${item.title}-${item.country}-${item.created_date}`)}
						<div class="flex items-center justify-between rounded-lg border p-3">
							<div>
								<h4 class="font-medium">{item.title}</h4>
								<p class="text-sm text-muted-foreground">
									{item.country} • {item.language} • {item.type}
								</p>
							</div>
							{#if item.created_date}
								<div class="text-sm text-muted-foreground">
									{new Date(item.created_date).toLocaleDateString()}
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{:else}
				<p class="text-sm text-muted-foreground">{t('overview.no_recent_items')}</p>
			{/if}
		</Card>
	{/if}
</div>

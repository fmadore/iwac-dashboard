<script lang="ts">
	import { Card } from '$lib/components/ui/card/index.js';
	import { itemsStore, statsData } from '$lib/stores/itemsStore.js';
	import { t } from '$lib/stores/translationStore.js';
	import StatsCard from '$lib/components/stats-card.svelte';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{$t('nav.overview')}</h2>
		<p class="text-muted-foreground">{$t('stats.total_items_desc')}</p>
	</div>

	{#if $itemsStore.loading}
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
			{#each Array(4) as _}
				<Card class="p-6">
					<Skeleton class="h-4 w-[100px] mb-2" />
					<Skeleton class="h-8 w-[60px] mb-2" />
					<Skeleton class="h-3 w-[120px]" />
				</Card>
			{/each}
		</div>
	{:else if $itemsStore.error}
		<Card class="p-6">
			<p class="text-destructive">{$t('common.error')}: {$itemsStore.error}</p>
		</Card>
	{:else}
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
			<StatsCard
				title={$t('stats.total_items')}
				value={$statsData.totalItems}
				trend="+12.5%"
				description={$t('stats.total_items_desc')}
			/>
			<StatsCard
				title={$t('stats.countries')}
				value={$statsData.countries}
				description={$t('stats.countries_desc')}
			/>
			<StatsCard
				title={$t('stats.languages')}
				value={$statsData.languages}
				description={$t('stats.languages_desc')}
			/>
			<StatsCard
				title={$t('stats.types')}
				value={$statsData.types}
				description={$t('stats.types_desc')}
			/>
		</div>

		<div class="grid gap-4 md:grid-cols-2">
			<Card class="p-6">
				<h3 class="text-lg font-semibold mb-4">{$t('chart.recent_additions')}</h3>
				<div class="h-[200px] flex items-center justify-center text-muted-foreground">
					Chart placeholder - Coming soon
				</div>
			</Card>
			<Card class="p-6">
				<h3 class="text-lg font-semibary mb-4">{$t('chart.top_countries')}</h3>
				<div class="h-[200px] flex items-center justify-center text-muted-foreground">
					Chart placeholder - Coming soon
				</div>
			</Card>
		</div>

		<Card class="p-6">
			<h3 class="text-lg font-semibold mb-4">Recent Items</h3>
			<div class="space-y-2">
				{#each $itemsStore.items as item}
					<div class="flex items-center justify-between p-3 border rounded-lg">
						<div>
							<h4 class="font-medium">{item.title}</h4>
							<p class="text-sm text-muted-foreground">
								{item.country} • {item.language} • {item.type}
							</p>
						</div>
						<div class="text-sm text-muted-foreground">
							{new Date(item.created_date).toLocaleDateString()}
						</div>
					</div>
				{/each}
			</div>
		</Card>
	{/if}
</div>

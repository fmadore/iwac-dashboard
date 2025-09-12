<script lang="ts">
	import { onMount } from 'svelte';
	import { PieChart } from "layerchart";
	import TrendingUpIcon from "@lucide/svelte/icons/trending-up";
	import * as Chart from "$lib/components/ui/chart/index.js";
	import * as Card from "$lib/components/ui/card/index.js";
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { itemsStore } from '$lib/stores/itemsStore.js';
	import { t } from '$lib/stores/translationStore.js';

	// Reactive language distribution data
	$: languageData = $itemsStore.items.reduce((acc, item) => {
		const language = item.language || 'Unknown';
		acc[language] = (acc[language] || 0) + 1;
		return acc;
	}, {} as Record<string, number>);

	// Convert to chart data format for LayerChart
	$: chartData = Object.entries(languageData)
		.map(([language, count]) => ({
			language,
			count,
			percentage: ((count / $itemsStore.items.length) * 100).toFixed(1)
		}))
		.sort((a, b) => b.count - a.count);

	// Chart configuration for shadcn-svelte
	const chartConfig = {
		count: {
			label: "Documents",
		},
		French: {
			label: "French",
			color: "hsl(var(--chart-1))",
		},
		English: {
			label: "English", 
			color: "hsl(var(--chart-2))",
		},
		Spanish: {
			label: "Spanish",
			color: "hsl(var(--chart-3))",
		},
		German: {
			label: "German",
			color: "hsl(var(--chart-4))",
		},
		Unknown: {
			label: "Unknown",
			color: "hsl(var(--chart-5))",
		},
	} satisfies Chart.ChartConfig;

	onMount(() => {
		// Only load if not already loaded
		if ($itemsStore.items.length === 0 && !$itemsStore.loading) {
			itemsStore.loadItems();
		}
	});
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{$t('nav.languages')}</h2>
		<p class="text-muted-foreground">{$t('chart.language_distribution_desc')}</p>
	</div>

	{#if $itemsStore.loading}
		<Card.Root>
			<Card.Content class="p-6">
				<div class="space-y-4">
					<Skeleton class="h-6 w-[200px]" />
					<div class="h-[400px] flex items-center justify-center">
						<Skeleton class="h-[300px] w-[300px] rounded-full" />
					</div>
				</div>
			</Card.Content>
		</Card.Root>
	{:else if $itemsStore.error}
		<Card.Root>
			<Card.Content class="p-6">
				<p class="text-destructive">{$t('common.error')}: {$itemsStore.error}</p>
			</Card.Content>
		</Card.Root>
	{:else}
		<div class="grid gap-6 md:grid-cols-2">
			<!-- Pie Chart -->
			<Card.Root>
				<Card.Header>
					<Card.Title>{$t('chart.language_distribution')}</Card.Title>
					<Card.Description>
						Total: {$itemsStore.items.length} {$t('chart.documents').toLowerCase()}
					</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="mx-auto aspect-square max-h-[400px] flex items-center justify-center">
						{#if chartData.length > 0}
							<PieChart
								data={chartData}
								value="count"
								r={120}
								innerRadius={50}
								outerRadius={120}
							>
							</PieChart>
						{:else}
							<div class="flex items-center justify-center h-[200px] text-muted-foreground">
								No data available
							</div>
						{/if}
					</div>
				</Card.Content>
				<Card.Footer class="flex-col items-start gap-2 text-sm">
					<div class="flex gap-2 font-medium leading-none">
						Language distribution <TrendingUpIcon class="h-4 w-4" />
					</div>
					<div class="leading-none text-muted-foreground">
						Showing distribution across {chartData.length} languages
					</div>
				</Card.Footer>
			</Card.Root>

			<!-- Language Stats Table -->
			<Card.Root>
				<Card.Header>
					<Card.Title>Language Statistics</Card.Title>
					<Card.Description>Detailed breakdown by language</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="space-y-2">
						{#each chartData as item, index}
							<div class="flex items-center justify-between p-3 border rounded-lg">
								<div class="flex items-center gap-3">
									<div 
										class="w-4 h-4 rounded-full" 
										style="background-color: hsl(var(--chart-{(index % 5) + 1}))"
									></div>
									<span class="font-medium">{item.language}</span>
								</div>
								<div class="text-right">
									<p class="font-semibold">{item.count}</p>
									<p class="text-sm text-muted-foreground">{item.percentage}%</p>
								</div>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	{/if}
</div>

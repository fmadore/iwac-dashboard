<script lang="ts">
	import { onMount } from 'svelte';
	import { Loader2 } from '@lucide/svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import StackedBarChart from '$lib/components/charts/StackedBarChart.svelte';

	interface SeriesData {
		name: string;
		data: number[];
	}

	interface ByYearData {
		years: number[];
		series: SeriesData[];
		total_records: number;
		year_range: {
			min: number;
			max: number;
		};
		country: string | null;
		generated_at: string;
	}

	// Get preloaded data from +page.ts
	let { data: pageData } = $props<{
		data: {
			data: ByYearData | null;
			error: string | null;
		};
	}>();

	// Use preloaded data directly
	const data = $derived(pageData.data);
	const error = $derived(pageData.error);

	let chartReady = $state(false);

	// Defer chart rendering to allow other UI to paint
	onMount(() => {
		const timer = setTimeout(() => {
			chartReady = true;
		}, 100);
		return () => clearTimeout(timer);
	});
</script>

<svelte:head>
	<title>{t('nav.references_by_year')} - {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 p-6">
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight">{t('nav.references_by_year')}</h1>
		<p class="text-muted-foreground">
			Distribution of bibliographic references over time by document type
		</p>
	</div>

	{#if !data && !error}
		<Card.Root>
			<Card.Header>
				<Skeleton class="h-8 w-64" />
			</Card.Header>
			<Card.Content>
				<Skeleton class="h-96 w-full" />
			</Card.Content>
		</Card.Root>
	{:else if error}
		<Card.Root>
			<Card.Header>
				<Card.Title>Error</Card.Title>
			</Card.Header>
			<Card.Content>
				<p class="text-destructive">{error}</p>
				<p class="mt-4 text-sm text-muted-foreground">
					This visualization requires data generation. Please run:
					<code class="rounded bg-muted px-2 py-1">python scripts/generate_references.py</code>
				</p>
			</Card.Content>
		</Card.Root>
	{:else if data}
		<div class="space-y-4">
			<!-- Statistics Cards -->
			<div class="grid gap-4 md:grid-cols-3">
				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground">Total References</Card.Title>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">{data.total_records.toLocaleString()}</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground">Year Range</Card.Title>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">
							{data.year_range.min}–{data.year_range.max}
						</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground">Reference Types</Card.Title>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">{data.series.length}</div>
					</Card.Content>
				</Card.Root>
			</div>

			<!-- Stacked Bar Chart -->
			<Card.Root>
				<Card.Header>
					<Card.Title>References Distribution by Year and Type</Card.Title>
					<Card.Description>
						Temporal distribution of bibliographic references by document type
					</Card.Description>
				</Card.Header>
				<Card.Content>
					{#if chartReady}
						<StackedBarChart years={data.years} series={data.series} height="600px" />
					{:else}
						<div class="flex h-[600px] w-full flex-col items-center justify-center gap-4">
							<Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
							<p class="text-sm text-muted-foreground">
								{t('categories.loading_chart')}
							</p>
						</div>
					{/if}
				</Card.Content>
			</Card.Root>
		</div>
	{/if}
</div>

<style>
	:global(body) {
		overflow-y: auto;
	}
</style>

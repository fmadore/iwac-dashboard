<script lang="ts">
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.js';
	import StackedBarChart from '$lib/components/charts/StackedBarChart.svelte';

	interface SeriesData {
		name: string;
		data: number[];
	}

	interface CategoryData {
		years: number[];
		series: SeriesData[];
		total_records: number;
		year_range: {
			min: number;
			max: number;
		};
	}

	let data = $state<CategoryData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	async function loadData() {
		try {
			loading = true;
			error = null;
			const response = await fetch(`${base}/data/categories-global.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			data = await response.json();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
			console.error('Error loading categories data:', e);
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		loadData();
	});
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{$t('nav.categories')}</h2>
		<p class="text-muted-foreground">{$t('categories.description')}</p>
	</div>

	{#if loading}
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
			<Card.Content class="py-12">
				<div class="text-center">
					<p class="text-destructive">{$t('errors.failed_to_load')}: {error}</p>
				</div>
			</Card.Content>
		</Card.Root>
	{:else if data}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-3">
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Description>{$t('categories.total_records')}</Card.Description>
					<Card.Title class="text-3xl">{data.total_records.toLocaleString()}</Card.Title>
				</Card.Header>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Description>{$t('categories.year_range')}</Card.Description>
					<Card.Title class="text-3xl">{data.year_range.min} - {data.year_range.max}</Card.Title>
				</Card.Header>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Description>{$t('categories.document_types')}</Card.Description>
					<Card.Title class="text-3xl">{data.series.length}</Card.Title>
				</Card.Header>
			</Card.Root>
		</div>

		<!-- Stacked Bar Chart -->
		<Card.Root>
			<Card.Header>
				<Card.Title>{$t('categories.chart_title')}</Card.Title>
				<Card.Description>{$t('categories.chart_description')}</Card.Description>
			</Card.Header>
			<Card.Content>
				<StackedBarChart
					title={$t('categories.stacked_chart_title')}
					years={data.years}
					series={data.series}
					height="600px"
				/>
			</Card.Content>
		</Card.Root>
	{/if}
</div>
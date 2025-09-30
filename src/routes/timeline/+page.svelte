<script lang="ts">
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import TimelineChart from '$lib/components/charts/TimelineChart.svelte';
	import { t } from '$lib/stores/translationStore.js';

	// Prerender this page
	export const prerender = true;

	interface TimelineData {
		months: string[];
		monthly_additions: number[];
		cumulative_total: number[];
		total_records: number;
		month_range: {
			min: string;
			max: string;
		};
	}

	let data = $state<TimelineData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	async function loadData() {
		try {
			const response = await fetch(`${base}/data/timeline-growth.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			data = await response.json();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load timeline data';
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
		<h2 class="text-3xl font-bold tracking-tight">{$t('timeline.title')}</h2>
		<p class="text-muted-foreground">{$t('timeline.description')}</p>
	</div>

	{#if loading}
		<Card.Root class="p-6">
			<div class="space-y-4">
				<Skeleton class="h-8 w-64" />
				<Skeleton class="h-[500px] w-full" />
			</div>
		</Card.Root>
	{:else if error}
		<Card.Root class="p-6">
			<div class="text-center py-12">
				<h3 class="text-xl font-semibold mb-2 text-destructive">{$t('common.error')}</h3>
				<p class="text-muted-foreground">{error}</p>
			</div>
		</Card.Root>
	{:else if data}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-3">
			<Card.Root>
				<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
					<Card.Title class="text-sm font-medium">{$t('timeline.total_records')}</Card.Title>
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">{data.total_records.toLocaleString()}</div>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
					<Card.Title class="text-sm font-medium">{$t('timeline.month_range')}</Card.Title>
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">
						{data.month_range.min} - {data.month_range.max}
					</div>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
					<Card.Title class="text-sm font-medium">{$t('timeline.monthly_additions')}</Card.Title>
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">
						{Math.round(data.total_records / data.months.length).toLocaleString()}
					</div>
					<p class="text-xs text-muted-foreground">Average per month</p>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Main Chart -->
		<Card.Root class="p-6">
			<Card.Header>
				<Card.Title>{$t('timeline.chart_title')}</Card.Title>
				<Card.Description>{$t('timeline.chart_description')}</Card.Description>
			</Card.Header>
			<Card.Content>
				<TimelineChart
					months={data.months}
					monthlyAdditions={data.monthly_additions}
					cumulativeTotal={data.cumulative_total}
				/>
			</Card.Content>
		</Card.Root>
	{/if}
</div>
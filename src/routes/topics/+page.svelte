<script lang="ts">
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import LayerChartBar from '$lib/components/charts/LayerChartBar.svelte';
	import { Search, ArrowRight, FileText, BrainCircuit, Target, AlertCircle } from '@lucide/svelte';
	import type { TopicsSummaryData, TopicSummary } from '$lib/types/topics.js';

	// State
	let summaryData = $state<TopicsSummaryData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let searchQuery = $state('');

	// Load data
	async function loadData() {
		loading = true;
		error = null;
		try {
			const response = await fetch(`${base}/data/topics/summary.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			summaryData = await response.json();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Unknown error';
		} finally {
			loading = false;
		}
	}

	// Initialize on mount
	$effect(() => {
		loadData();
	});

	// Filter topics based on search (excluding outliers from search)
	const filteredTopics = $derived.by(() => {
		if (!summaryData) return [];
		const topics = summaryData.topics.filter((topic) => topic.id !== -1);
		if (!searchQuery.trim()) return topics;
		const query = searchQuery.toLowerCase();
		return topics.filter((topic) => topic.label.toLowerCase().includes(query));
	});

	// Get outlier topic
	const outlierTopic = $derived.by(() => {
		if (!summaryData) return null;
		return summaryData.topics.find((topic) => topic.id === -1) || null;
	});

	// Statistics
	const stats = $derived.by(() => {
		if (!summaryData) return null;
		const nonOutlierDocs = summaryData.total_docs - (outlierTopic?.count || 0);
		const coveragePercent = ((nonOutlierDocs / summaryData.total_docs) * 100).toFixed(1);
		return {
			totalDocs: summaryData.total_docs,
			uniqueTopics: summaryData.unique_topics - (outlierTopic ? 1 : 0),
			coverage: coveragePercent,
			outliers: outlierTopic?.count || 0
		};
	});

	// Data for top topics bar chart (top 10)
	const topTopicsChartData = $derived.by(() => {
		if (!summaryData) return [];
		return summaryData.topics
			.filter((topic) => topic.id !== -1)
			.slice(0, 10)
			.map((topic) => ({
				category: topic.label,
				documents: topic.count,
				originalKey: topic.label
			}));
	});
</script>

<svelte:head>
	<title>{t('topics.title')} - IWAC</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{t('topics.title')}</h2>
		<p class="text-muted-foreground">{t('topics.description')}</p>
	</div>

	{#if loading}
		<!-- Loading state -->
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
			{#each Array(4) as _, i (i)}
				<Card.Root>
					<Card.Content class="p-6">
						<Skeleton class="mb-2 h-4 w-24" />
						<Skeleton class="h-8 w-16" />
					</Card.Content>
				</Card.Root>
			{/each}
		</div>
		<Card.Root>
			<Card.Content class="p-6">
				<Skeleton class="h-[300px] w-full" />
			</Card.Content>
		</Card.Root>
	{:else if error}
		<!-- Error state -->
		<Card.Root class="border-destructive">
			<Card.Content class="flex items-center gap-4 p-6">
				<AlertCircle class="h-8 w-8 text-destructive" />
				<div>
					<p class="font-semibold">{t('common.error')}</p>
					<p class="text-sm text-muted-foreground">{error}</p>
				</div>
				<Button onclick={loadData} variant="outline" class="ml-auto">
					{t('common.reset')}
				</Button>
			</Card.Content>
		</Card.Root>
	{:else if stats}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
			<Card.Root>
				<Card.Content class="p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-muted-foreground">
								{t('topics.total_documents')}
							</p>
							<p class="text-2xl font-bold">{stats.totalDocs.toLocaleString()}</p>
							<p class="text-xs text-muted-foreground">{t('topics.total_documents_desc')}</p>
						</div>
						<FileText class="h-8 w-8 text-muted-foreground" />
					</div>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Content class="p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-muted-foreground">
								{t('topics.unique_topics')}
							</p>
							<p class="text-2xl font-bold">{stats.uniqueTopics}</p>
							<p class="text-xs text-muted-foreground">{t('topics.unique_topics_desc')}</p>
						</div>
						<BrainCircuit class="h-8 w-8 text-muted-foreground" />
					</div>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Content class="p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-muted-foreground">
								{t('topics.coverage')}
							</p>
							<p class="text-2xl font-bold">{stats.coverage}%</p>
							<p class="text-xs text-muted-foreground">{t('topics.coverage_desc')}</p>
						</div>
						<Target class="h-8 w-8 text-muted-foreground" />
					</div>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Content class="p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-muted-foreground">
								{t('topics.outliers')}
							</p>
							<p class="text-2xl font-bold">{stats.outliers.toLocaleString()}</p>
							<p class="text-xs text-muted-foreground">{t('topics.outliers_desc')}</p>
						</div>
						<AlertCircle class="h-8 w-8 text-muted-foreground" />
					</div>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Top Topics Chart -->
		<Card.Root>
			<Card.Header>
				<Card.Title>{t('topics.top_topics')}</Card.Title>
				<Card.Description>Top 10 topics by document count</Card.Description>
			</Card.Header>
			<Card.Content>
				{#if topTopicsChartData.length > 0}
					<LayerChartBar
						data={topTopicsChartData}
						height={450}
						orientation="horizontal"
						useMultipleColors={true}
						yAxisLabelWidth={200}
					/>
				{:else}
					<p class="text-center text-muted-foreground">{t('chart.no_data')}</p>
				{/if}
			</Card.Content>
		</Card.Root>

		<!-- Topics List -->
		<Card.Root>
			<Card.Header>
				<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
					<div>
						<Card.Title>{t('topics.all_topics')}</Card.Title>
						<Card.Description>
							{t('topics.showing_topics', [filteredTopics.length.toString(), stats.uniqueTopics.toString()])}
						</Card.Description>
					</div>
					<div class="relative w-full sm:w-64">
						<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
						<Input
							type="text"
							placeholder={t('topics.search_topics')}
							bind:value={searchQuery}
							class="pl-9"
						/>
					</div>
				</div>
			</Card.Header>
			<Card.Content>
				{#if filteredTopics.length === 0}
					<p class="py-8 text-center text-muted-foreground">{t('topics.no_topics')}</p>
				{:else}
					<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
						{#each filteredTopics as topic (topic.id)}
							<a
								href="{base}/topics/{topic.id}"
								class="group flex items-start justify-between rounded-lg border bg-card p-4 transition-colors hover:bg-accent"
							>
								<div class="min-w-0 flex-1">
									<p class="font-medium leading-tight group-hover:text-accent-foreground">
										{topic.label}
									</p>
									<p class="mt-1 text-sm text-muted-foreground">
										{topic.count.toLocaleString()} {t('topics.documents').toLowerCase()}
									</p>
								</div>
								<div class="ml-3 flex shrink-0 items-center gap-2">
									<Badge variant="secondary">{topic.count}</Badge>
									<ArrowRight class="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
								</div>
							</a>
						{/each}
					</div>
				{/if}
			</Card.Content>
		</Card.Root>
	{/if}
</div>

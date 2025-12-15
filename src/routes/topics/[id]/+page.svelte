<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import LayerChartBar from '$lib/components/charts/LayerChartBar.svelte';
	import LayerChartPieChart from '$lib/components/charts/LayerChartPieChart.svelte';
	import {
		ArrowLeft,
		FileText,
		ExternalLink,
		Calendar,
		Globe2,
		Percent,
		AlertCircle
	} from '@lucide/svelte';
	import type { TopicDetailData } from '$lib/types/topics.js';

	// Get topic ID from params
	const topicId = $derived(page.params.id);

	// State
	let topicData = $state<TopicDetailData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Load topic data
	async function loadData(id: string) {
		loading = true;
		error = null;
		try {
			const response = await fetch(`${base}/data/topics/${id}.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			topicData = await response.json();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Unknown error';
		} finally {
			loading = false;
		}
	}

	// Load data when topicId changes
	$effect(() => {
		if (topicId) {
			loadData(topicId);
		}
	});

	// Process country distribution for pie chart
	const countryChartData = $derived.by(() => {
		if (!topicData) return [];
		return Object.entries(topicData.counts_by_country)
			.map(([country, count]) => ({
				label: country,
				value: count
			}))
			.sort((a, b) => b.value - a.value);
	});

	// Process temporal distribution for bar chart
	const temporalChartData = $derived.by(() => {
		if (!topicData) return [];
		const byYear: Record<string, number> = {};
		Object.entries(topicData.counts_by_month).forEach(([month, count]) => {
			const year = month.substring(0, 4);
			byYear[year] = (byYear[year] || 0) + count;
		});
		return Object.entries(byYear)
			.map(([year, count]) => ({
				category: year,
				documents: count
			}))
			.sort((a, b) => a.category.localeCompare(b.category));
	});

	// Get polarity badge color
	function getPolarityVariant(polarity: string | null | undefined): 'default' | 'secondary' | 'destructive' | 'outline' {
		if (!polarity) return 'outline';
		const lower = polarity.toLowerCase();
		if (lower.includes('positif') || lower.includes('positive')) return 'default';
		if (lower.includes('négatif') || lower.includes('negative')) return 'destructive';
		return 'secondary';
	}
</script>

<svelte:head>
	<title>{topicData?.label || t('topics.topic_detail')} - IWAC</title>
</svelte:head>

<div class="space-y-6">
	<!-- Back button -->
	<div>
		<Button variant="ghost" href="{base}/topics" class="gap-2">
			<ArrowLeft class="h-4 w-4" />
			{t('topics.back_to_topics')}
		</Button>
	</div>

	{#if loading}
		<!-- Loading state -->
		<div class="space-y-6">
			<Skeleton class="h-10 w-96" />
			<div class="grid gap-4 md:grid-cols-3">
				{#each Array(3) as _, i (i)}
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
		</div>
	{:else if error}
		<!-- Error state -->
		<Card.Root class="border-destructive">
			<Card.Content class="flex items-center gap-4 p-6">
				<AlertCircle class="h-8 w-8 text-destructive" />
				<div>
					<p class="font-semibold">{t('common.error')}</p>
					<p class="text-sm text-muted-foreground">{error}</p>
				</div>
				<Button onclick={() => topicId && loadData(topicId)} variant="outline" class="ml-auto">
					{t('common.reset')}
				</Button>
			</Card.Content>
		</Card.Root>
	{:else if topicData}
		<!-- Header -->
		<div class="flex flex-col gap-2">
			<div class="flex items-start gap-4">
				<h1 class="text-2xl font-bold tracking-tight md:text-3xl">{topicData.label}</h1>
				{#if topicData.id === -1}
					<Badge variant="outline">Outlier</Badge>
				{/if}
			</div>
			<p class="text-muted-foreground">
				Topic ID: {topicData.id}
			</p>
		</div>

		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-3">
			<Card.Root>
				<Card.Content class="p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-muted-foreground">
								{t('topics.documents')}
							</p>
							<p class="text-2xl font-bold">{topicData.count.toLocaleString()}</p>
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
								{t('topics.avg_probability')}
							</p>
							<p class="text-2xl font-bold">{(topicData.avg_prob * 100).toFixed(1)}%</p>
						</div>
						<Percent class="h-8 w-8 text-muted-foreground" />
					</div>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Content class="p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-muted-foreground">
								{t('stats.countries')}
							</p>
							<p class="text-2xl font-bold">{Object.keys(topicData.counts_by_country).length}</p>
						</div>
						<Globe2 class="h-8 w-8 text-muted-foreground" />
					</div>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Charts Row -->
		<div class="grid gap-6 lg:grid-cols-2">
			<!-- Country Distribution -->
			<Card.Root class="min-w-0 overflow-hidden">
				<Card.Header>
					<Card.Title>{t('topics.country_distribution')}</Card.Title>
				</Card.Header>
				<Card.Content>
					{#if countryChartData.length > 0}
						<LayerChartPieChart data={countryChartData} showLabels={true} />
					{:else}
						<p class="py-8 text-center text-muted-foreground">{t('chart.no_data')}</p>
					{/if}
				</Card.Content>
			</Card.Root>

			<!-- Temporal Distribution -->
			<Card.Root class="min-w-0 overflow-hidden">
				<Card.Header>
					<Card.Title>{t('topics.temporal_distribution')}</Card.Title>
				</Card.Header>
				<Card.Content>
					{#if temporalChartData.length > 0}
						<LayerChartBar data={temporalChartData} height={300} xAxisLabelRotate={45} />
					{:else}
						<p class="py-8 text-center text-muted-foreground">{t('chart.no_data')}</p>
					{/if}
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Documents Table -->
		<Card.Root class="overflow-hidden">
			<Card.Header>
				<Card.Title>{t('topics.top_documents')}</Card.Title>
				<Card.Description>
					Showing top {Math.min(topicData.docs.length, 50)} documents by confidence score
				</Card.Description>
			</Card.Header>
			<Card.Content>
				<Table.Root>
					<Table.Header>
						<Table.Row>
							<Table.Head class="min-w-[200px]">{t('table.title')}</Table.Head>
							<Table.Head class="min-w-[100px]">{t('filters.country')}</Table.Head>
							<Table.Head class="min-w-[100px]">
								<span class="flex items-center gap-1">
									<Calendar class="h-4 w-4" />
									Date
								</span>
							</Table.Head>
							<Table.Head class="min-w-[80px]">{t('topics.confidence')}</Table.Head>
							{#if topicData.ai_fields.length > 0}
								<Table.Head class="min-w-[80px]">{t('topics.polarity')}</Table.Head>
							{/if}
							<Table.Head class="w-10"></Table.Head>
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#each topicData.docs.slice(0, 50) as doc (doc.url || doc.title)}
							<Table.Row>
								<Table.Cell class="font-medium">
									<span class="line-clamp-2">{doc.title || doc.ocr_title || 'Untitled'}</span>
									{#if doc.newspaper}
										<span class="block text-xs text-muted-foreground">{doc.newspaper}</span>
									{/if}
								</Table.Cell>
								<Table.Cell>
									{#if doc.country}
										<Badge variant="outline">{doc.country}</Badge>
									{:else}
										<span class="text-muted-foreground">—</span>
									{/if}
								</Table.Cell>
								<Table.Cell class="text-sm">
									{doc.pub_date || doc.date || '—'}
								</Table.Cell>
								<Table.Cell>
									<Badge variant="secondary">
										{(doc.topic_prob * 100).toFixed(0)}%
									</Badge>
								</Table.Cell>
								{#if topicData.ai_fields.length > 0}
									<Table.Cell>
										{@const polarity = doc.gemini_polarite || doc.chatgpt_polarite}
										{#if polarity}
											<Badge variant={getPolarityVariant(polarity)}>{polarity}</Badge>
										{:else}
											<span class="text-muted-foreground">—</span>
										{/if}
									</Table.Cell>
								{/if}
								<Table.Cell>
									{#if doc.url}
										<a
											href={doc.url}
											target="_blank"
											rel="noopener noreferrer"
											class="text-muted-foreground hover:text-foreground"
											title={t('topics.view_article')}
										>
											<ExternalLink class="h-4 w-4" />
										</a>
									{/if}
								</Table.Cell>
							</Table.Row>
						{/each}
					</Table.Body>
				</Table.Root>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

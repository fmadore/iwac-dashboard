<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import LayerChartBar from '$lib/components/charts/LayerChartBar.svelte';
	import LayerChartPieChart from '$lib/components/charts/LayerChartPieChart.svelte';
	import {
		ArrowLeft,
		FileText,
		Calendar,
		Globe2,
		Percent,
		AlertCircle,
		ArrowUpDown,
		ArrowUp,
		ArrowDown
	} from '@lucide/svelte';
	import type { TopicDetailData, TopicDocument } from '$lib/types/topics.js';

	// Get topic ID from params
	const topicId = $derived(page.params.id);

	// State
	let topicData = $state<TopicDetailData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Sorting state
	let sortKey = $state<'title' | 'country' | 'date' | 'confidence' | 'polarity'>('confidence');
	let sortDirection = $state<'asc' | 'desc'>('desc');

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

	// Get item URL based on language
	function getItemUrl(doc: TopicDocument): string | null {
		// Extract item ID from URL or use o:id
		let itemId: string | null = null;

		if (doc['o:id']) {
			itemId = String(doc['o:id']);
		} else if (doc.url) {
			// Extract ID from URL like https://islam.zmo.de/s/afrique_ouest/item/77142
			const match = doc.url.match(/\/item\/(\d+)/);
			if (match) {
				itemId = match[1];
			}
		}

		if (!itemId) return null;

		const baseUrl = languageStore.current === 'fr'
			? 'https://islam.zmo.de/s/afrique_ouest/item/'
			: 'https://islam.zmo.de/s/westafrica/item/';

		return baseUrl + itemId;
	}

	// Get country CSS class for badge styling
	function getCountryClass(country: string | null): string {
		if (!country) return '';
		const normalized = country.toLowerCase().replace(/['\s]/g, '-').replace(/[éè]/g, 'e');
		if (normalized.includes('cote') || normalized.includes('ivoire')) return 'country-cote-divoire';
		if (normalized.includes('burkina')) return 'country-burkina-faso';
		if (normalized.includes('benin') || normalized.includes('bénin')) return 'country-benin';
		if (normalized.includes('togo')) return 'country-togo';
		if (normalized.includes('niger') && !normalized.includes('nigeria')) return 'country-niger';
		if (normalized.includes('nigeria')) return 'country-nigeria';
		return 'country-default';
	}

	// Get polarity class for badge styling
	function getPolarityClass(polarity: string | null | undefined): string {
		if (!polarity) return '';
		const lower = polarity.toLowerCase();
		if (lower.includes('positif') || lower.includes('positive')) return 'polarity-positive';
		if (lower.includes('négatif') || lower.includes('negative')) return 'polarity-negative';
		if (lower.includes('neutre') || lower.includes('neutral')) return 'polarity-neutral';
		return '';
	}

	// Sort function
	function toggleSort(key: typeof sortKey) {
		if (sortKey === key) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortKey = key;
			sortDirection = key === 'confidence' ? 'desc' : 'asc';
		}
	}

	// Sorted documents
	const sortedDocs = $derived.by(() => {
		if (!topicData) return [];
		const docs = [...topicData.docs];

		docs.sort((a, b) => {
			let comparison = 0;

			switch (sortKey) {
				case 'title':
					const titleA = (a.title || a.ocr_title || '').toLowerCase();
					const titleB = (b.title || b.ocr_title || '').toLowerCase();
					comparison = titleA.localeCompare(titleB);
					break;
				case 'country':
					comparison = (a.country || '').localeCompare(b.country || '');
					break;
				case 'date':
					const dateA = a.pub_date || a.date || '';
					const dateB = b.pub_date || b.date || '';
					comparison = dateA.localeCompare(dateB);
					break;
				case 'confidence':
					comparison = a.topic_prob - b.topic_prob;
					break;
				case 'polarity':
					const polA = a.gemini_polarite || a.chatgpt_polarite || '';
					const polB = b.gemini_polarite || b.chatgpt_polarite || '';
					comparison = polA.localeCompare(polB);
					break;
			}

			return sortDirection === 'asc' ? comparison : -comparison;
		});

		return docs.slice(0, 50);
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
					{t('topics.showing_documents', [Math.min(topicData.docs.length, 50).toString()])}
				</Card.Description>
			</Card.Header>
			<Card.Content>
				<Table.Root>
					<Table.Header>
						<Table.Row>
							<Table.Head class="min-w-[200px]">
								<button
									type="button"
									class="flex items-center gap-1 hover:text-foreground"
									onclick={() => toggleSort('title')}
								>
									{t('table.title')}
									{#if sortKey === 'title'}
										{#if sortDirection === 'asc'}
											<ArrowUp class="h-4 w-4" />
										{:else}
											<ArrowDown class="h-4 w-4" />
										{/if}
									{:else}
										<ArrowUpDown class="h-4 w-4" />
									{/if}
								</button>
							</Table.Head>
							<Table.Head class="min-w-[100px]">
								<button
									type="button"
									class="flex items-center gap-1 hover:text-foreground"
									onclick={() => toggleSort('country')}
								>
									{t('filters.country')}
									{#if sortKey === 'country'}
										{#if sortDirection === 'asc'}
											<ArrowUp class="h-4 w-4" />
										{:else}
											<ArrowDown class="h-4 w-4" />
										{/if}
									{:else}
										<ArrowUpDown class="h-4 w-4" />
									{/if}
								</button>
							</Table.Head>
							<Table.Head class="min-w-[100px]">
								<button
									type="button"
									class="flex items-center gap-1 hover:text-foreground"
									onclick={() => toggleSort('date')}
								>
									<Calendar class="h-4 w-4" />
									{t('topics.date')}
									{#if sortKey === 'date'}
										{#if sortDirection === 'asc'}
											<ArrowUp class="h-4 w-4" />
										{:else}
											<ArrowDown class="h-4 w-4" />
										{/if}
									{:else}
										<ArrowUpDown class="h-4 w-4" />
									{/if}
								</button>
							</Table.Head>
							<Table.Head class="min-w-[80px]">
								<button
									type="button"
									class="flex items-center gap-1 hover:text-foreground"
									onclick={() => toggleSort('confidence')}
								>
									{t('topics.confidence')}
									{#if sortKey === 'confidence'}
										{#if sortDirection === 'asc'}
											<ArrowUp class="h-4 w-4" />
										{:else}
											<ArrowDown class="h-4 w-4" />
										{/if}
									{:else}
										<ArrowUpDown class="h-4 w-4" />
									{/if}
								</button>
							</Table.Head>
							{#if topicData.ai_fields.length > 0}
								<Table.Head class="min-w-[80px]">
									<button
										type="button"
										class="flex items-center gap-1 hover:text-foreground"
										onclick={() => toggleSort('polarity')}
									>
										{t('topics.polarity')}
										{#if sortKey === 'polarity'}
											{#if sortDirection === 'asc'}
												<ArrowUp class="h-4 w-4" />
											{:else}
												<ArrowDown class="h-4 w-4" />
											{/if}
										{:else}
											<ArrowUpDown class="h-4 w-4" />
										{/if}
									</button>
								</Table.Head>
							{/if}
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#each sortedDocs as doc (doc.url || doc.title)}
							{@const itemUrl = getItemUrl(doc)}
							<Table.Row>
								<Table.Cell class="font-medium">
									{#if itemUrl}
										<a
											href={itemUrl}
											target="_blank"
											rel="noopener noreferrer"
											class="line-clamp-2 text-primary underline-offset-4 hover:underline"
										>
											{doc.title || doc.ocr_title || 'Untitled'}
										</a>
									{:else}
										<span class="line-clamp-2">{doc.title || doc.ocr_title || 'Untitled'}</span>
									{/if}
									{#if doc.newspaper}
										<span class="block text-xs text-muted-foreground">{doc.newspaper}</span>
									{/if}
								</Table.Cell>
								<Table.Cell>
									{#if doc.country}
										<Badge variant="outline" class={getCountryClass(doc.country)}>
											{doc.country}
										</Badge>
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
											<Badge variant="outline" class={getPolarityClass(polarity)}>
												{polarity}
											</Badge>
										{:else}
											<span class="text-muted-foreground">—</span>
										{/if}
									</Table.Cell>
								{/if}
							</Table.Row>
						{/each}
					</Table.Body>
				</Table.Root>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

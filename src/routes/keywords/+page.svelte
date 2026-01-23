<script lang="ts">
	import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import { KeywordsLineChart } from '$lib/components/visualizations/charts/layerchart/index.js';
	import { Search, Check, Plus } from '@lucide/svelte';

	// Props from page load
	let { data } = $props();

	// URL sync for filter state
	const urlSync = useUrlSync();

	// Data interfaces
	interface KeywordSeriesData {
		years: number[];
		counts: number[];
		total?: number;
		articles?: number;
	}

	interface KeywordData {
		field: string;
		years: number[];
		top_keywords: string[];
		global_series: Record<string, KeywordSeriesData>;
		by_country: Record<string, { top_keywords: string[]; series: Record<string, KeywordSeriesData>; total_keywords: number }>;
		by_newspaper: Record<string, { top_keywords: string[]; series: Record<string, KeywordSeriesData>; total_keywords: number }>;
		all_keywords: Array<{ keyword: string; total: number; articles: number }>;
		stats: {
			total_keywords: number;
			total_occurrences: number;
			year_range: [number, number] | null;
			countries_count: number;
			newspapers_count: number;
		};
	}

	interface Metadata {
		total_articles: number;
		countries: string[];
		newspapers: string[];
		subjects: { total_keywords: number; total_occurrences: number; top_5: string[] };
		spatial: { total_keywords: number; total_occurrences: number; top_5: string[] };
		year_range: [number, number] | null;
		generated_at: string;
	}

	// Data from page load
	const subjectsData = $derived(data.subjects as KeywordData);
	const spatialData = $derived(data.spatial as KeywordData);
	const metadata = $derived(data.metadata as Metadata);

	// Current keyword type (subject or spatial)
	const keywordType = $derived((urlSync.filters.type as 'subject' | 'spatial') || 'subject');
	const currentData = $derived(keywordType === 'subject' ? subjectsData : spatialData);

	// View mode: 'top' (most frequent) or 'compare' (selected keywords)
	const viewMode = $derived((urlSync.filters.view as 'top' | 'compare') || 'top');

	// Facet type: 'global', 'country', or 'newspaper'
	const facetType = $derived((urlSync.filters.facet as 'global' | 'country' | 'newspaper') || 'global');

	// Selected country/newspaper for faceted view
	const selectedCountry = $derived(urlSync.filters.country);
	const selectedNewspaper = $derived(urlSync.filters.newspaper);

	// Number of top keywords to show
	const topN = $derived(Number(urlSync.filters.topN) || 5);

	// Helper functions to convert between keyword names and indices
	function keywordToId(keyword: string): number | undefined {
		const index = currentData.all_keywords.findIndex((item) => item.keyword === keyword);
		return index >= 0 ? index : undefined;
	}

	function idToKeyword(id: number): string | undefined {
		return currentData.all_keywords[id]?.keyword;
	}

	// Selected keywords for comparison mode (stored as comma-separated IDs in URL)
	const selectedKeywordIds = $derived(urlSync.filters.keywords as string || '');
	const selectedKeywords = $derived.by(() => {
		if (!selectedKeywordIds) return [];
		return selectedKeywordIds
			.split(',')
			.map((id) => idToKeyword(Number(id)))
			.filter((kw): kw is string => kw !== undefined);
	});

	// Search query for keyword selection
	let searchQuery = $state('');

	// Pagination for All Keywords table
	let tablePage = $state(1);
	const tableItemsPerPage = 50;

	// Calculate pagination
	const tableTotalPages = $derived(Math.ceil(currentData.all_keywords.length / tableItemsPerPage));
	const tableStartIndex = $derived((tablePage - 1) * tableItemsPerPage);
	const tableEndIndex = $derived(Math.min(tableStartIndex + tableItemsPerPage, currentData.all_keywords.length));
	const tablePaginatedKeywords = $derived(currentData.all_keywords.slice(tableStartIndex, tableEndIndex));

	// Reset table page when keyword type changes
	$effect(() => {
		const _ = keywordType; // Create dependency
		tablePage = 1;
	});

	// Get available keywords based on current facet
	const availableKeywords = $derived.by(() => {
		if (facetType === 'country' && selectedCountry && currentData.by_country[selectedCountry]) {
			return currentData.by_country[selectedCountry].top_keywords;
		}
		if (facetType === 'newspaper' && selectedNewspaper && currentData.by_newspaper[selectedNewspaper]) {
			return currentData.by_newspaper[selectedNewspaper].top_keywords;
		}
		return currentData.top_keywords;
	});

	// Get series data based on current facet
	const currentSeries = $derived.by(() => {
		if (facetType === 'country' && selectedCountry && currentData.by_country[selectedCountry]) {
			return currentData.by_country[selectedCountry].series;
		}
		if (facetType === 'newspaper' && selectedNewspaper && currentData.by_newspaper[selectedNewspaper]) {
			return currentData.by_newspaper[selectedNewspaper].series;
		}
		return currentData.global_series;
	});

	// Build chart series based on view mode
	const chartSeries = $derived.by(() => {
		const keywords = viewMode === 'top'
			? availableKeywords.slice(0, topN)
			: selectedKeywords.filter((kw) => currentSeries[kw]);

		const chartColors = [
			'var(--chart-1)',
			'var(--chart-2)',
			'var(--chart-3)',
			'var(--chart-4)',
			'var(--chart-5)',
			'hsl(var(--primary))',
			'hsl(var(--destructive))',
			'hsl(280 60% 50%)',
			'hsl(160 60% 40%)',
			'hsl(30 80% 50%)'
		];

		return keywords.map((keyword, idx) => {
			const seriesData = currentSeries[keyword];
			return {
				keyword,
				years: seriesData?.years || currentData.years,
				counts: seriesData?.counts || [],
				color: chartColors[idx % chartColors.length]
			};
		});
	});

	// Filtered keywords for search
	const filteredKeywords = $derived.by(() => {
		const allKws = currentData.all_keywords;
		if (!searchQuery.trim()) return allKws.slice(0, 100);
		const query = searchQuery.toLowerCase().trim();
		return allKws.filter((item) => item.keyword.toLowerCase().includes(query)).slice(0, 100);
	});

	// Handlers
	function handleKeywordTypeChange(value: string) {
		urlSync.setFilter('type', value);
		// Reset selected keywords when type changes
		urlSync.clearFilter('keywords');
	}

	function handleViewModeChange(value: string) {
		urlSync.setFilter('view', value);
	}

	function handleFacetChange(value: string) {
		urlSync.setFilter('facet', value);
		// Clear facet-specific selections
		if (value !== 'country') urlSync.clearFilter('country');
		if (value !== 'newspaper') urlSync.clearFilter('newspaper');
	}

	function handleCountryChange(value: string | undefined) {
		if (value && value !== 'all') {
			urlSync.setFilter('country', value);
		} else {
			urlSync.clearFilter('country');
		}
	}

	function handleNewspaperChange(value: string | undefined) {
		if (value && value !== 'all') {
			urlSync.setFilter('newspaper', value);
		} else {
			urlSync.clearFilter('newspaper');
		}
	}

	function handleTopNChange(value: string | undefined) {
		if (value) {
			urlSync.setFilter('topN', value);
		}
	}

	function toggleKeyword(keyword: string) {
		const current = new Set(selectedKeywords);
		if (current.has(keyword)) {
			current.delete(keyword);
		} else if (current.size < 10) {
			current.add(keyword);
		}
		// Convert keywords to IDs for URL
		const ids = Array.from(current)
			.map((kw) => keywordToId(kw))
			.filter((id): id is number => id !== undefined)
			.sort((a, b) => a - b);

		const newValue = ids.join(',');
		if (newValue) {
			urlSync.setFilter('keywords', newValue);
		} else {
			urlSync.clearFilter('keywords');
		}
	}

	function clearSelectedKeywords() {
		urlSync.clearFilter('keywords');
	}

	function clearAllFilters() {
		urlSync.clearFilter('facet');
		urlSync.clearFilter('country');
		urlSync.clearFilter('newspaper');
		urlSync.clearFilter('keywords');
	}

	// Check if any filters are active
	const hasActiveFilters = $derived.by(() => {
		return facetType !== 'global' || selectedCountry || selectedNewspaper || selectedKeywords.length > 0;
	});

	// Chart title
	const chartTitle = $derived.by(() => {
		const lang = languageStore.current;
		if (viewMode === 'top') {
			return t('keywords.top_n_over_time', [topN]);
		}
		return t('keywords.comparison_chart');
	});

	// Chart subtitle
	const chartSubtitle = $derived.by(() => {
		if (facetType === 'country' && selectedCountry) {
			return t('keywords.filtered_by_country', [selectedCountry]);
		}
		if (facetType === 'newspaper' && selectedNewspaper) {
			return t('keywords.filtered_by_newspaper', [selectedNewspaper]);
		}
		return t('keywords.all_data');
	});

	// Empty state message
	const emptyStateMessage = $derived.by(() => {
		if (viewMode === 'compare' && selectedKeywords.length === 0) {
			return t('keywords.select_keywords_prompt');
		}
		if (viewMode === 'compare' && selectedKeywords.length > 0) {
			// Keywords selected but no data (likely due to facet filter)
			if (facetType === 'country' && selectedCountry) {
				return t('keywords.no_data_for_country', [selectedCountry]);
			}
			if (facetType === 'newspaper' && selectedNewspaper) {
				return t('keywords.no_data_for_newspaper', [selectedNewspaper]);
			}
		}
		return t('chart.no_data');
	});
</script>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{t('keywords.title')}</h2>
		<p class="text-muted-foreground">{t('keywords.description')}</p>
	</div>

	<!-- Keyword Type Tabs -->
	<Card>
		<CardContent class="pt-6">
			<Tabs.Root value={keywordType} onValueChange={handleKeywordTypeChange}>
				<Tabs.List class="grid w-full grid-cols-2">
					<Tabs.Trigger value="subject">{t('keywords.subjects')}</Tabs.Trigger>
					<Tabs.Trigger value="spatial">{t('keywords.spatial')}</Tabs.Trigger>
				</Tabs.List>
			</Tabs.Root>
		</CardContent>
	</Card>

	<!-- Stats Overview -->
	<div class="grid grid-cols-2 gap-4 md:grid-cols-4">
		<Card>
			<CardContent class="pt-6">
				<div class="text-sm font-medium text-muted-foreground">{t('keywords.total_keywords')}</div>
				<div class="text-2xl font-bold">{currentData.stats.total_keywords.toLocaleString()}</div>
			</CardContent>
		</Card>
		<Card>
			<CardContent class="pt-6">
				<div class="text-sm font-medium text-muted-foreground">{t('keywords.total_occurrences')}</div>
				<div class="text-2xl font-bold">{currentData.stats.total_occurrences.toLocaleString()}</div>
			</CardContent>
		</Card>
		<Card>
			<CardContent class="pt-6">
				<div class="text-sm font-medium text-muted-foreground">{t('keywords.year_range')}</div>
				<div class="text-2xl font-bold">
					{#if currentData.stats.year_range}
						{currentData.stats.year_range[0]}-{currentData.stats.year_range[1]}
					{:else}
						-
					{/if}
				</div>
			</CardContent>
		</Card>
		<Card>
			<CardContent class="pt-6">
				<div class="text-sm font-medium text-muted-foreground">{t('keywords.articles_analyzed')}</div>
				<div class="text-2xl font-bold">{metadata.total_articles.toLocaleString()}</div>
			</CardContent>
		</Card>
	</div>

	<!-- Main Content: Controls + Chart -->
	<div class="grid gap-6 lg:grid-cols-4">
		<!-- Controls Sidebar -->
		<Card class="lg:col-span-1">
			<CardHeader>
				<div class="flex items-center justify-between">
					<CardTitle class="text-base">{t('keywords.filters')}</CardTitle>
					{#if hasActiveFilters}
						<Button variant="ghost" size="sm" onclick={clearAllFilters}>
							{t('common.clear')}
						</Button>
					{/if}
				</div>
			</CardHeader>
			<CardContent class="space-y-6">
				<!-- Facet Selection -->
				<div class="space-y-2">
					<Label>{t('keywords.facet_by')}</Label>
					<Select.Root
						type="single"
						value={facetType}
						onValueChange={handleFacetChange}
					>
						<Select.Trigger class="w-full">
							{facetType === 'global' ? t('keywords.global') : facetType === 'country' ? t('keywords.by_country') : t('keywords.by_newspaper')}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="global">{t('keywords.global')}</Select.Item>
							<Select.Item value="country">{t('keywords.by_country')}</Select.Item>
							<Select.Item value="newspaper">{t('keywords.by_newspaper')}</Select.Item>
						</Select.Content>
					</Select.Root>
				</div>

				<!-- Country selector (when faceted by country) -->
				{#if facetType === 'country'}
					<div class="space-y-2">
						<Label>{t('keywords.select_country')}</Label>
						<Select.Root
							type="single"
							value={selectedCountry || 'all'}
							onValueChange={handleCountryChange}
						>
							<Select.Trigger class="w-full">
								{selectedCountry || t('keywords.all_countries')}
							</Select.Trigger>
							<Select.Content>
								<Select.Item value="all">{t('keywords.all_countries')}</Select.Item>
								{#each metadata.countries as country (country)}
									<Select.Item value={country}>{country}</Select.Item>
								{/each}
							</Select.Content>
						</Select.Root>
					</div>
				{/if}

				<!-- Newspaper selector (when faceted by newspaper) -->
				{#if facetType === 'newspaper'}
					<div class="space-y-2">
						<Label>{t('keywords.select_newspaper')}</Label>
						<Select.Root
							type="single"
							value={selectedNewspaper || 'all'}
							onValueChange={handleNewspaperChange}
						>
							<Select.Trigger class="w-full">
								{selectedNewspaper || t('keywords.all_newspapers')}
							</Select.Trigger>
							<Select.Content class="max-h-60">
								<Select.Item value="all">{t('keywords.all_newspapers')}</Select.Item>
								{#each metadata.newspapers.slice(0, 50) as newspaper (newspaper)}
									<Select.Item value={newspaper}>{newspaper}</Select.Item>
								{/each}
							</Select.Content>
						</Select.Root>
					</div>
				{/if}

				<hr class="border-border" />

				<!-- View Mode -->
				<div class="space-y-2">
					<Label>{t('keywords.view_mode')}</Label>
					<div class="flex flex-wrap gap-2">
						<Button
							variant={viewMode === 'top' ? 'default' : 'outline'}
							size="sm"
							class="flex-1 min-w-0"
							title={t('keywords.top_frequent')}
							onclick={() => handleViewModeChange('top')}
						>
							<span class="truncate">{t('keywords.top_frequent')}</span>
						</Button>
						<Button
							variant={viewMode === 'compare' ? 'default' : 'outline'}
							size="sm"
							class="flex-1 min-w-0"
							title={t('keywords.compare')}
							onclick={() => handleViewModeChange('compare')}
						>
							<span class="truncate">{t('keywords.compare')}</span>
						</Button>
					</div>
				</div>

				<!-- Top N selector (when in top mode) -->
				{#if viewMode === 'top'}
					<div class="space-y-2">
						<Label>{t('keywords.number_to_show')}</Label>
						<Select.Root
							type="single"
							value={String(topN)}
							onValueChange={handleTopNChange}
						>
							<Select.Trigger class="w-full">
								{topN} {t('keywords.keywords')}
							</Select.Trigger>
							<Select.Content>
								<Select.Item value="3">3 {t('keywords.keywords')}</Select.Item>
								<Select.Item value="5">5 {t('keywords.keywords')}</Select.Item>
								<Select.Item value="10">10 {t('keywords.keywords')}</Select.Item>
							</Select.Content>
						</Select.Root>
					</div>
				{/if}

				<!-- Keyword selector (when in compare mode) -->
				{#if viewMode === 'compare'}
					<div class="space-y-2">
						<div class="flex items-center justify-between">
							<Label>{t('keywords.select_keywords')}</Label>
							{#if selectedKeywords.length > 0}
								<Button variant="ghost" size="sm" onclick={clearSelectedKeywords}>
									{t('common.clear')}
								</Button>
							{/if}
						</div>
						<p class="text-xs text-muted-foreground">
							{t('keywords.select_up_to', [10])} ({selectedKeywords.length}/10)
						</p>

						<!-- Search -->
						<div class="relative">
							<Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
							<Input
								type="search"
								placeholder={t('keywords.search_keywords')}
								class="pl-8"
								bind:value={searchQuery}
							/>
						</div>

						<!-- Selected keywords -->
						{#if selectedKeywords.length > 0}
							<div class="flex flex-wrap gap-1">
								{#each selectedKeywords as kw (kw)}
									<Badge
										variant="secondary"
										class="cursor-pointer"
										onclick={() => toggleKeyword(kw)}
									>
										{kw} &times;
									</Badge>
								{/each}
							</div>
						{/if}

						<!-- Keyword list -->
						<div class="max-h-48 space-y-1 overflow-y-auto rounded border p-2">
							{#each filteredKeywords as item (item.keyword)}
								<button
									type="button"
									class="flex w-full cursor-pointer items-center gap-2 rounded p-1 text-left hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
									disabled={!selectedKeywords.includes(item.keyword) && selectedKeywords.length >= 10}
									onclick={() => toggleKeyword(item.keyword)}
								>
									<span class="flex h-4 w-4 items-center justify-center rounded border border-primary {selectedKeywords.includes(item.keyword) ? 'bg-primary text-primary-foreground' : ''}">
										{#if selectedKeywords.includes(item.keyword)}
											<Check class="h-3 w-3" />
										{/if}
									</span>
									<span class="flex-1 truncate text-sm">{item.keyword}</span>
									<span class="text-xs text-muted-foreground">{item.total}</span>
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</CardContent>
		</Card>

		<!-- Chart Area -->
		<Card class="lg:col-span-3">
			<CardHeader>
				<CardTitle>{chartTitle}</CardTitle>
				<CardDescription>{chartSubtitle}</CardDescription>
			</CardHeader>
			<CardContent>
				{#if chartSeries.length > 0}
					<KeywordsLineChart series={chartSeries} height={450} />
				{:else}
					<div class="flex h-[450px] flex-col items-center justify-center gap-4">
						<div class="text-center">
							<p class="text-muted-foreground">
								{emptyStateMessage}
							</p>
							{#if viewMode === 'compare' && selectedKeywords.length > 0 && hasActiveFilters}
								<p class="mt-2 text-sm text-muted-foreground">
									{t('keywords.try_different_filters')}
								</p>
							{/if}
						</div>
						{#if hasActiveFilters && viewMode === 'compare' && selectedKeywords.length > 0}
							<Button variant="outline" size="sm" onclick={clearAllFilters}>
								{t('keywords.clear_filters')}
							</Button>
						{/if}
					</div>
				{/if}
			</CardContent>
		</Card>
	</div>

	<!-- Top Keywords Table -->
	<Card>
		<CardHeader>
			<div class="flex items-start justify-between">
				<div>
					<CardTitle>{t('keywords.all_keywords_table')}</CardTitle>
					<CardDescription class="mt-1.5">
						{t('keywords.showing_range', [tableStartIndex + 1, tableEndIndex, currentData.all_keywords.length])}
					</CardDescription>
				</div>
				{#if tableTotalPages > 1}
					<div class="flex items-center gap-2">
						<Button
							variant="outline"
							size="sm"
							disabled={tablePage === 1}
							onclick={() => tablePage--}
						>
							{t('keywords.previous')}
						</Button>
						<span class="text-sm text-muted-foreground">
							{t('keywords.page_of', [tablePage, tableTotalPages])}
						</span>
						<Button
							variant="outline"
							size="sm"
							disabled={tablePage === tableTotalPages}
							onclick={() => tablePage++}
						>
							{t('keywords.next')}
						</Button>
					</div>
				{/if}
			</div>
		</CardHeader>
		<CardContent>
			<div class="rounded-md border">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/50">
							<th class="p-3 text-left text-sm font-medium">{t('keywords.rank')}</th>
							<th class="p-3 text-left text-sm font-medium">{t('keywords.keyword')}</th>
							<th class="p-3 text-right text-sm font-medium">{t('keywords.occurrences')}</th>
							<th class="p-3 text-right text-sm font-medium">{t('keywords.articles')}</th>
							<th class="p-3 text-center text-sm font-medium">{t('keywords.actions')}</th>
						</tr>
					</thead>
					<tbody>
						{#each tablePaginatedKeywords as item, idx (item.keyword)}
							<tr class="border-b last:border-0">
								<td class="p-3 text-sm text-muted-foreground">{tableStartIndex + idx + 1}</td>
								<td class="p-3 text-sm font-medium">{item.keyword}</td>
								<td class="p-3 text-right text-sm tabular-nums">{item.total.toLocaleString()}</td>
								<td class="p-3 text-right text-sm tabular-nums">{item.articles.toLocaleString()}</td>
								<td class="p-3 text-center">
									<Button
										variant="ghost"
										size="sm"
										onclick={() => {
											handleViewModeChange('compare');
											toggleKeyword(item.keyword);
										}}
									>
										{selectedKeywords.includes(item.keyword) ? t('keywords.remove') : t('keywords.add')}
									</Button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</CardContent>
	</Card>

	<!-- Dataset Info -->
	<Card>
		<CardHeader>
			<CardTitle>{t('keywords.dataset_info')}</CardTitle>
		</CardHeader>
		<CardContent>
			<div class="grid gap-4 text-sm md:grid-cols-2">
				<div>
					<p><span class="font-medium">{t('keywords.generated_at')}:</span> {new Date(metadata.generated_at).toLocaleDateString()}</p>
					<p><span class="font-medium">{t('keywords.total_articles')}:</span> {metadata.total_articles.toLocaleString()}</p>
				</div>
				<div>
					<p><span class="font-medium">{t('keywords.countries_count')}:</span> {metadata.countries.length}</p>
					<p><span class="font-medium">{t('keywords.newspapers_count')}:</span> {metadata.newspapers.length}</p>
				</div>
			</div>
		</CardContent>
	</Card>
</div>

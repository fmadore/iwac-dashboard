<script lang="ts">
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import { DataTable, type ColumnDef } from '$lib/components/ui/data-table/index.js';
	import { ExternalLink } from '@lucide/svelte';

	interface PublisherData {
		publisher: string;
		publication_count: number;
		types: Record<string, number>;
		earliest_year?: number;
		latest_year?: number;
		o_id?: string;
	}

	// Build islam.zmo.de URL based on current language
	function getItemUrl(oId: string): string {
		const lang = languageStore.current;
		const path = lang === 'fr' ? 'afrique_ouest' : 'westafrica';
		return `https://islam.zmo.de/s/${path}/item/${oId}`;
	}

	interface PublishersResponse {
		publishers: PublisherData[];
		total_publishers: number;
		total_publications: number;
		country: string | null;
		generated_at: string;
	}

	interface MetadataResponse {
		countries: {
			with_individual_files: string[];
		};
	}

	// Use URL sync hook
	const urlSync = useUrlSync();

	// Get preloaded data from +page.ts
	let { data: pageData } = $props<{
		data: {
			publishersData: PublishersResponse | null;
			metadata: MetadataResponse | null;
			error: string | null;
		};
	}>();

	// Use preloaded data directly
	const globalData = $derived(pageData.publishersData);
	const metadata = $derived(pageData.metadata);
	let countryData = $state<PublishersResponse | null>(null);
	let countryLoading = $state(false);
	const error = $derived(pageData.error);

	// Filter states from URL
	const selectedCountry = $derived(urlSync.filters.country);

	// Table column definitions
	const tableColumns: ColumnDef<PublisherData>[] = [
		{
			key: 'publisher',
			label: 'publishers.publisher',
			align: 'left' as const
		},
		{
			key: 'publication_count',
			label: 'publishers.publications',
			align: 'right' as const
		},
		{
			key: 'year_range',
			label: 'publishers.year_range',
			align: 'left' as const,
			sortable: false,
			render: (row) => {
				if (row.earliest_year && row.latest_year) {
					return `${row.earliest_year}–${row.latest_year}`;
				}
				return '—';
			}
		},
		{
			key: 'top_type',
			label: 'publishers.top_type',
			align: 'left' as const,
			sortable: false,
			searchable: false,
			render: (row) => {
				const topType = Object.entries(row.types).sort((a, b) => b[1] - a[1])[0];
				if (topType) {
					return `${t(`type.${topType[0]}`, [topType[0]])} (${topType[1]})`;
				}
				return '—';
			}
		}
	];

	async function loadCountryData(country: string | undefined) {
		if (!country) {
			countryData = null;
			return;
		}

		try {
			countryLoading = true;
			const filename = country.toLowerCase().replace(/\s+/g, '-');
			const response = await fetch(`${base}/data/references/publishers-${filename}.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			countryData = await response.json();
		} catch (e) {
			console.error(`Error loading country data for ${country}:`, e);
			countryData = null;
		} finally {
			countryLoading = false;
		}
	}

	// Watch for country selection changes
	$effect(() => {
		loadCountryData(selectedCountry);
	});

	// Get active data based on country selection
	const activeData = $derived(selectedCountry ? countryData : globalData);

	const countryOptions = $derived(metadata?.countries.with_individual_files ?? []);

	// Handlers for filter changes
	function handleCountryChange(value: string | undefined) {
		if (value && value !== 'all-countries') {
			urlSync.setFilter('country', value);
		} else {
			urlSync.clearFilter('country');
		}
	}

	function handleClearFilters() {
		urlSync.clearFilters();
	}
</script>

<svelte:head>
	<title>{t('nav.publishers')} - {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 p-6">
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight">{t('publishers.title')}</h1>
		<p class="text-muted-foreground">
			{t('publishers.description')}
		</p>
	</div>

	{#if !globalData && !error}
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
				<Card.Title>{t('common.error')}</Card.Title>
			</Card.Header>
			<Card.Content>
				<p class="text-destructive">{error}</p>
				<p class="mt-4 text-sm text-muted-foreground">
					{t('publishers.run_script_hint')}
					<code class="rounded bg-muted px-2 py-1">python scripts/generate_references.py</code>
				</p>
			</Card.Content>
		</Card.Root>
	{:else if activeData || countryLoading}
		<div class="space-y-4">
			<!-- Statistics Cards -->
			<div class="grid gap-4 md:grid-cols-3">
				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground"
							>{t('publishers.total_publishers')}</Card.Title
						>
					</Card.Header>
					<Card.Content>
						{#if countryLoading}
							<Skeleton class="h-8 w-24" />
						{:else}
							<div class="text-2xl font-bold">
								{activeData?.total_publishers.toLocaleString() ?? 0}
							</div>
						{/if}
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground"
							>{t('publishers.total_publications')}</Card.Title
						>
					</Card.Header>
					<Card.Content>
						{#if countryLoading}
							<Skeleton class="h-8 w-24" />
						{:else}
							<div class="text-2xl font-bold">
								{activeData?.total_publications.toLocaleString() ?? 0}
							</div>
						{/if}
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground"
							>{t('publishers.avg_per_publisher')}</Card.Title
						>
					</Card.Header>
					<Card.Content>
						{#if countryLoading}
							<Skeleton class="h-8 w-24" />
						{:else}
							<div class="text-2xl font-bold">
								{activeData && activeData.total_publishers > 0
									? (activeData.total_publications / activeData.total_publishers).toFixed(1)
									: '0'}
							</div>
						{/if}
					</Card.Content>
				</Card.Root>
			</div>

			<!-- Country Filter -->
			<Card.Root>
				<Card.Header>
					<Card.Title>{t('filters.title')}</Card.Title>
					<Card.Description>{t('filters.description')}</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="flex flex-wrap items-center gap-4">
						<div class="flex items-center gap-2">
							<label for="countrySelect" class="text-sm font-medium">{t('filters.country')}:</label>
							<Select.Root
								type="single"
								value={selectedCountry ?? 'all-countries'}
								onValueChange={(v) => handleCountryChange(v === 'all-countries' ? undefined : v)}
							>
								<Select.Trigger class="w-50" id="countrySelect">
									{selectedCountry || t('filters.all_countries')}
								</Select.Trigger>
								<Select.Content>
									<Select.Item value="all-countries">{t('filters.all_countries')}</Select.Item>
									{#each countryOptions as country (country)}
										<Select.Item value={country}>{country}</Select.Item>
									{/each}
								</Select.Content>
							</Select.Root>
						</div>
						{#if selectedCountry}
							<Button variant="secondary" size="sm" onclick={handleClearFilters}>
								{t('filters.clear')}
							</Button>
						{/if}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Publishers Table -->
			<Card.Root>
				<Card.Header>
					<Card.Title>
						{#if selectedCountry}
							{t('publishers.table_title')} - {selectedCountry}
						{:else}
							{t('publishers.table_title')}
						{/if}
					</Card.Title>
					<Card.Description>{t('publishers.table_description')}</Card.Description>
				</Card.Header>
				<Card.Content>
					{#if countryLoading}
						<Skeleton class="h-96 w-full" />
					{:else if activeData}
						<DataTable
							data={activeData.publishers}
							columns={tableColumns}
							searchPlaceholder={t('common.search')}
							noResultsText={t('table.no_results')}
							pageSize={50}
							defaultSortKey="publication_count"
							defaultSortDir="desc"
						>
							{#snippet cellRenderer({ row, column, value })}
								{#if column.key === 'publisher' && row.o_id}
									<a
										href={getItemUrl(row.o_id)}
										target="_blank"
										rel="noopener noreferrer"
										class="inline-flex items-center gap-1 text-primary hover:underline"
									>
										{value}
										<ExternalLink class="h-3 w-3" />
									</a>
								{:else if column.render}
									{column.render(row)}
								{:else}
									{value}
								{/if}
							{/snippet}
						</DataTable>
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

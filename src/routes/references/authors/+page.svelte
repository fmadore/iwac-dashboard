<script lang="ts">
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { DataTable, type ColumnDef } from '$lib/components/ui/data-table/index.js';

	interface AuthorData {
		author: string;
		publication_count: number;
		types: Record<string, number>;
		earliest_year?: number;
		latest_year?: number;
	}

	interface AuthorsResponse {
		authors: AuthorData[];
		total_authors: number;
		total_publications: number;
		country: string | null;
		generated_at: string;
	}

	let data = $state<AuthorData[]>([]);
	let responseData = $state<AuthorsResponse | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Table column definitions
	const tableColumns: ColumnDef<AuthorData>[] = [
		{
			key: 'author',
			label: 'Author',
			align: 'left' as const
		},
		{
			key: 'publication_count',
			label: 'Publications',
			align: 'right' as const
		},
		{
			key: 'year_range',
			label: 'Year Range',
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
			label: 'Most Common Type',
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

	async function loadData() {
		try {
			const response = await fetch(`${base}/data/references/authors.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			const result: AuthorsResponse = await response.json();
			responseData = result;
			data = result.authors || [];
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load authors data';
		} finally {
			loading = false;
		}
	}


	$effect(() => {
		loadData();
	});
</script>

<svelte:head>
	<title>{t('nav.top_authors')} - {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 p-6">
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight">{t('nav.top_authors')}</h1>
		<p class="text-muted-foreground">
			Top authors by publication count in the bibliographic references
		</p>
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
	{:else}
		<div class="space-y-4">
			<!-- Statistics Cards -->
			<div class="grid gap-4 md:grid-cols-3">
				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground">Total Authors</Card.Title>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">
							{responseData?.total_authors.toLocaleString() || data.length.toLocaleString()}
						</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground">Total Publications</Card.Title>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">
							{responseData?.total_publications.toLocaleString() ||
								data.reduce((sum, a) => sum + a.publication_count, 0).toLocaleString()}
						</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground">Avg Publications per Author</Card.Title>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">
							{responseData && responseData.total_authors > 0
								? (responseData.total_publications / responseData.total_authors).toFixed(1)
								: data.length > 0
									? (data.reduce((sum, a) => sum + a.publication_count, 0) / data.length).toFixed(1)
									: '0'}
						</div>
					</Card.Content>
				</Card.Root>
			</div>

			<!-- Authors Table -->
			<Card.Root>
				<Card.Header>
					<Card.Title>Authors by Publication Count</Card.Title>
					<Card.Description>Search and explore top authors</Card.Description>
				</Card.Header>
				<Card.Content>
					<DataTable
						data={data}
						columns={tableColumns}
						searchPlaceholder={t('common.search')}
						noResultsText={t('table.no_results')}
						pageSize={50}
						defaultSortKey="publication_count"
						defaultSortDir="desc"
					/>
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

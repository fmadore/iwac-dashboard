<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { Treemap } from '$lib/components/visualizations/charts/layerchart/index.js';
	import type { TreemapData, TreemapNode } from '$lib/types/treemap.js';

	// Get preloaded data from +page.ts
	let { data: pageData } = $props<{
		data: {
			treemapData: (TreemapData & {
				meta: {
					totalCountries: number;
					totalReferences: number;
					generatedAt: string;
				};
			}) | null;
			error: string | null;
		};
	}>();

	const treemapData = $derived(pageData.treemapData);
	const error = $derived(pageData.error);

	// Track selected node for drilldown
	let selectedNested = $state<TreemapNode | null>(null);

	// Calculate stats from data
	const stats = $derived(() => {
		if (!treemapData) return null;

		// Count unique document types across all countries
		const types = new Set<string>();
		for (const country of treemapData.children ?? []) {
			for (const docType of country.children ?? []) {
				types.add(docType.name);
			}
		}

		return {
			totalReferences: treemapData.meta?.totalReferences ?? 0,
			totalCountries: treemapData.meta?.totalCountries ?? 0,
			documentTypes: types.size
		};
	});
</script>

<svelte:head>
	<title>{t('treemap.title')} - {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 p-6">
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight">{t('treemap.title')}</h1>
		<p class="text-muted-foreground">
			{t('treemap.description')}
		</p>
	</div>

	{#if !treemapData && !error}
		<Card.Root>
			<Card.Header>
				<Skeleton class="h-8 w-64" />
			</Card.Header>
			<Card.Content>
				<Skeleton class="h-[600px] w-full" />
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
	{:else if treemapData}
		<div class="space-y-4">
			<!-- Statistics Cards -->
			<div class="grid gap-4 md:grid-cols-3">
				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground">
							{t('treemap.total_references')}
						</Card.Title>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">
							{stats()?.totalReferences.toLocaleString() ?? 0}
						</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground">
							{t('treemap.countries')}
						</Card.Title>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">
							{stats()?.totalCountries ?? 0}
						</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="pb-3">
						<Card.Title class="text-sm font-medium text-muted-foreground">
							{t('treemap.document_types')}
						</Card.Title>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">
							{stats()?.documentTypes ?? 0}
						</div>
					</Card.Content>
				</Card.Root>
			</div>

			<!-- Treemap Visualization -->
			<Card.Root>
				<Card.Header>
					<Card.Title>{t('treemap.title')}</Card.Title>
					<Card.Description>
						{t('treemap.description')}
					</Card.Description>
				</Card.Header>
				<Card.Content class="p-0">
					<Treemap
						data={treemapData}
						bind:selectedNested
						showBreadcrumb={true}
						paddingTop={24}
						paddingInner={2}
						paddingOuter={4}
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

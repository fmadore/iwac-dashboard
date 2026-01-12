<script lang="ts">
	import { onMount } from 'svelte';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { entitySpatialStore } from '$lib/stores/entitySpatialStore.svelte.js';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import {
		EntityCategorySelector,
		EntityPicker,
		EntityStatsCards,
		EntityLocationMap,
		LocationArticlePanel
	} from '$lib/components/visualizations/entity-spatial/index.js';
	import type { EntitySpatialIndex } from '$lib/types/entity-spatial.js';

	interface Props {
		data: {
			indexData: EntitySpatialIndex | null;
			error: string | null;
		};
	}

	let { data: pageData }: Props = $props();

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	// Derived state from store
	const isLoading = $derived(entitySpatialStore.isLoading);
	const isLoadingDetails = $derived(entitySpatialStore.isLoadingDetails);
	const error = $derived(entitySpatialStore.error);
	const currentEntity = $derived(entitySpatialStore.currentEntity);

	// Initialize store with page data
	onMount(() => {
		if (pageData.indexData) {
			entitySpatialStore.setIndexData(pageData.indexData);
			// Pre-load details for the default category (Personnes)
			entitySpatialStore.loadTypeDetails('Personnes');
		} else if (pageData.error) {
			entitySpatialStore.setError(pageData.error);
		}

		return () => {
			entitySpatialStore.reset();
		};
	});
</script>

<svelte:head>
	<title>{t('entity_spatial.title')} | IWAC Dashboard</title>
</svelte:head>

<div class="container mx-auto space-y-6 p-4">
	<!-- Page Header -->
	<div class="space-y-2">
		<h1 class="text-2xl font-bold tracking-tight">{t('entity_spatial.title')}</h1>
		<p class="text-muted-foreground">{t('entity_spatial.description')}</p>
	</div>

	{#if isLoading}
		<!-- Loading State -->
		<div class="space-y-4">
			<Skeleton class="h-12 w-full" />
			<Skeleton class="h-10 w-full" />
			<div class="grid grid-cols-3 gap-4">
				<Skeleton class="h-24" />
				<Skeleton class="h-24" />
				<Skeleton class="h-24" />
			</div>
			<Skeleton class="h-[500px] w-full" />
		</div>
	{:else if error}
		<!-- Error State -->
		<Card class="border-destructive">
			<CardContent class="p-6">
				<div class="flex items-center gap-2 text-destructive">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="20"
						height="20"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<circle cx="12" cy="12" r="10" />
						<line x1="12" y1="8" x2="12" y2="12" />
						<line x1="12" y1="16" x2="12.01" y2="16" />
					</svg>
					<span>{t('errors.failed_to_load')}: {error}</span>
				</div>
			</CardContent>
		</Card>
	{:else}
		<!-- Main Content -->
		<div class="space-y-6">
			<!-- Category Selector -->
			<Card>
				<CardHeader class="pb-3">
					<CardTitle class="text-base">{t('entity_spatial.select_category')}</CardTitle>
				</CardHeader>
				<CardContent>
					<EntityCategorySelector />
				</CardContent>
			</Card>

			<!-- Entity Picker -->
			<Card>
				<CardHeader class="pb-3">
					<CardTitle class="text-base">{t('entity_spatial.select_entity')}</CardTitle>
				</CardHeader>
				<CardContent>
					<EntityPicker />
					{#if isLoadingDetails}
						<div class="mt-2 text-sm text-muted-foreground">
							{t('common.loading')}
						</div>
					{/if}
				</CardContent>
			</Card>

			<!-- Entity Details (shown when entity selected) -->
			{#if currentEntity}
				<!-- Stats Cards -->
				<EntityStatsCards
					articleCount={currentEntity.stats.articleCount}
					countries={currentEntity.stats.countries}
					dateRange={currentEntity.stats.dateRange}
				/>

				<!-- Map -->
				<Card>
					<CardHeader class="pb-3">
						<CardTitle class="flex items-center gap-2">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="20"
								height="20"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
								class="text-primary"
							>
								<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21" />
								<line x1="9" y1="3" x2="9" y2="18" />
								<line x1="15" y1="6" x2="15" y2="21" />
							</svg>
							{t('entity_spatial.map_title', [currentEntity.name])}
						</CardTitle>
					</CardHeader>
					<CardContent>
						<p class="mb-4 text-sm text-muted-foreground">
							{t('entity_spatial.map_description')}
						</p>
						<EntityLocationMap height="500px" />
					</CardContent>
				</Card>
			{:else if isLoadingDetails}
				<!-- Loading details -->
				<Card>
					<CardContent class="flex h-[400px] items-center justify-center">
						<div class="text-center">
							<Skeleton class="mx-auto mb-4 h-12 w-12 rounded-full" />
							<p class="text-muted-foreground">{t('common.loading')}</p>
						</div>
					</CardContent>
				</Card>
			{:else}
				<!-- Empty state when no entity selected -->
				<Card>
					<CardContent class="flex h-[400px] items-center justify-center">
						<div class="text-center">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="48"
								height="48"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="1.5"
								stroke-linecap="round"
								stroke-linejoin="round"
								class="mx-auto mb-4 text-muted-foreground/50"
							>
								<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21" />
								<line x1="9" y1="3" x2="9" y2="18" />
								<line x1="15" y1="6" x2="15" y2="21" />
							</svg>
							<p class="text-muted-foreground">{t('entity_spatial.no_entity_selected')}</p>
						</div>
					</CardContent>
				</Card>
			{/if}
		</div>
	{/if}

	<!-- Location Article Panel (Sheet) -->
	<LocationArticlePanel />
</div>

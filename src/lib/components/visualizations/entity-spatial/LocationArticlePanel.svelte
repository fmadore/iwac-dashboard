<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { entitySpatialStore } from '$lib/stores/entitySpatialStore.svelte.js';
	import {
		Sheet,
		SheetContent,
		SheetHeader,
		SheetTitle,
		SheetDescription
	} from '$lib/components/ui/sheet/index.js';
	import { ScrollArea } from '$lib/components/ui/scroll-area/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';

	// Pagination state
	const ITEMS_PER_PAGE = 20;
	let currentPage = $state(1);

	// Derived state from store
	const selectedLocation = $derived(entitySpatialStore.selectedLocation);
	const currentEntity = $derived(entitySpatialStore.currentEntity);
	const articles = $derived(entitySpatialStore.currentLocationArticles);

	// Pagination derived values
	const totalPages = $derived(Math.ceil(articles.length / ITEMS_PER_PAGE));
	const paginatedArticles = $derived(
		articles.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
	);

	// Reset page when location changes
	$effect(() => {
		if (selectedLocation) {
			currentPage = 1;
		}
	});

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	// Control sheet open state based on selected location
	const isOpen = $derived(selectedLocation !== null);

	// IWAC base URL for article links
	const IWAC_BASE_URL = 'https://islam.zmo.de/s/westafrica/item/';

	function handleOpenChange(open: boolean) {
		if (!open) {
			entitySpatialStore.setSelectedLocation(null);
		}
	}

	function goToPage(page: number) {
		currentPage = Math.max(1, Math.min(page, totalPages));
	}

	function formatDate(dateStr: string): string {
		if (!dateStr) return '';
		// Format YYYY-MM-DD to locale string
		try {
			const date = new Date(dateStr);
			return date.toLocaleDateString(lang === 'fr' ? 'fr-FR' : 'en-US', {
				year: 'numeric',
				month: 'short',
				day: 'numeric'
			});
		} catch {
			return dateStr;
		}
	}

	function getArticleTypeLabel(type: string): string {
		if (type === 'articles') {
			return t('entity_spatial.type_article');
		}
		if (type === 'publications') {
			return t('entity_spatial.type_publication');
		}
		return type;
	}
</script>

<Sheet open={isOpen} onOpenChange={handleOpenChange}>
	<SheetContent side="right" class="w-full sm:max-w-lg">
		<SheetHeader>
			<SheetTitle class="flex items-center gap-2">
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
					<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
					<circle cx="12" cy="10" r="3" />
				</svg>
				{selectedLocation?.name ?? ''}
			</SheetTitle>
			<SheetDescription>
				{#if selectedLocation && currentEntity}
					{t('entity_spatial.location_panel_description', [
						currentEntity.name,
						selectedLocation.name
					])}
				{/if}
			</SheetDescription>
		</SheetHeader>

		<div class="mt-4">
			{#if selectedLocation}
				<!-- Location info -->
				<div class="mb-4 flex items-center gap-2">
					<Badge variant="outline">{selectedLocation.country}</Badge>
					<span class="text-sm text-muted-foreground">
						{articles.length}
						{articles.length === 1
							? t('entity_spatial.article_singular')
							: t('entity_spatial.articles_plural')}
					</span>
				</div>

				<!-- Articles list -->
				<ScrollArea class="h-[calc(100vh-220px)]">
					<div class="space-y-3 pr-4">
						{#each articles as article (article.id)}
							<div
								class="rounded-lg border border-border bg-card p-3 transition-colors hover:bg-accent/50"
							>
								<div class="mb-2 flex items-start justify-between gap-2">
									<h4 class="line-clamp-2 text-sm font-medium leading-tight">
										{article.title || t('entity_spatial.untitled')}
									</h4>
									<Badge variant="secondary" class="shrink-0 text-xs">
										{getArticleTypeLabel(article.type)}
									</Badge>
								</div>

								<div class="mb-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
									{#if article.date}
										<span class="flex items-center gap-1">
											<svg
												xmlns="http://www.w3.org/2000/svg"
												width="12"
												height="12"
												viewBox="0 0 24 24"
												fill="none"
												stroke="currentColor"
												stroke-width="2"
												stroke-linecap="round"
												stroke-linejoin="round"
											>
												<rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
												<line x1="16" y1="2" x2="16" y2="6" />
												<line x1="8" y1="2" x2="8" y2="6" />
												<line x1="3" y1="10" x2="21" y2="10" />
											</svg>
											{formatDate(article.date)}
										</span>
									{/if}
									{#if article.newspaper}
										<span class="flex items-center gap-1">
											<svg
												xmlns="http://www.w3.org/2000/svg"
												width="12"
												height="12"
												viewBox="0 0 24 24"
												fill="none"
												stroke="currentColor"
												stroke-width="2"
												stroke-linecap="round"
												stroke-linejoin="round"
											>
												<path
													d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"
												/>
												<path d="M18 14h-8" />
												<path d="M15 18h-5" />
												<path d="M10 6h8v4h-8V6Z" />
											</svg>
											{article.newspaper}
										</span>
									{/if}
									{#if article.country}
										<span class="flex items-center gap-1">
											<svg
												xmlns="http://www.w3.org/2000/svg"
												width="12"
												height="12"
												viewBox="0 0 24 24"
												fill="none"
												stroke="currentColor"
												stroke-width="2"
												stroke-linecap="round"
												stroke-linejoin="round"
											>
												<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
												<line x1="4" y1="22" x2="4" y2="15" />
											</svg>
											{article.country}
										</span>
									{/if}
								</div>

								<Button
									variant="outline"
									size="sm"
									class="w-full"
									href="{IWAC_BASE_URL}{article.id}"
									target="_blank"
									rel="noopener noreferrer"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										width="14"
										height="14"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										stroke-linecap="round"
										stroke-linejoin="round"
										class="mr-2"
									>
										<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
										<polyline points="15 3 21 3 21 9" />
										<line x1="10" y1="14" x2="21" y2="3" />
									</svg>
									{t('entity_spatial.view_in_iwac')}
								</Button>
							</div>
						{/each}
					</div>
				</ScrollArea>
			{/if}
		</div>
	</SheetContent>
</Sheet>

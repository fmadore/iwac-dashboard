<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
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
	import { MapPin, ExternalLink, Calendar, Newspaper, Flag, ChevronLeft, ChevronRight } from '@lucide/svelte';
	import type { MapLocation, MapLocationItem } from '$lib/types/map-location.js';

	interface Props {
		location: MapLocation | null;
		onClose: () => void;
		itemBaseUrl?: string;
		itemLabel?: string;
	}

	let { location, onClose, itemBaseUrl = 'https://islam.zmo.de/s/westafrica/item/', itemLabel = 'publications' }: Props = $props();

	// Pagination state
	const ITEMS_PER_PAGE = 20;
	let currentPage = $state(1);

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	// Control sheet open state based on selected location
	const isOpen = $derived(location !== null);

	// Pagination derived values
	const items = $derived(location?.items ?? []);
	const totalPages = $derived(Math.ceil(items.length / ITEMS_PER_PAGE));
	const paginatedItems = $derived(
		items.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
	);

	// Reset page when location changes
	$effect(() => {
		if (location) {
			currentPage = 1;
		}
	});

	function handleOpenChange(open: boolean) {
		if (!open) {
			onClose();
		}
	}

	function goToPage(page: number) {
		currentPage = Math.max(1, Math.min(page, totalPages));
	}

	function formatDate(dateStr: string | undefined): string {
		if (!dateStr) return '';
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

	function getItemUrl(id: string): string {
		// Adjust URL based on language if needed
		const basePath = lang === 'fr' ? 'https://islam.zmo.de/s/afrique_ouest/item/' : itemBaseUrl;
		return basePath + id;
	}

	function getItemTypeLabel(type: string): string {
		// Try to translate the type, fall back to original
		const translated = t(`type.${type}`, [type]);
		return translated !== `type.${type}` ? translated : type;
	}
</script>

<Sheet open={isOpen} onOpenChange={handleOpenChange}>
	<SheetContent side="right" class="w-full sm:max-w-lg">
		<SheetHeader>
			<SheetTitle class="flex items-center gap-2">
				<MapPin class="h-5 w-5 text-primary" />
				<span class="flex-1 truncate">{location?.name ?? ''}</span>
				{#if location?.externalUrl}
					<Button
						variant="ghost"
						size="sm"
						class="h-8 w-8 p-0 shrink-0"
						href={location.externalUrl}
						target="_blank"
						rel="noopener noreferrer"
					>
						<ExternalLink class="h-4 w-4" />
						<span class="sr-only">{t('map_popup.view_in_iwac')}</span>
					</Button>
				{/if}
			</SheetTitle>
			<SheetDescription>
				{#if location}
					{t('map_popup.showing', [
						((currentPage - 1) * ITEMS_PER_PAGE + 1).toString(),
						Math.min(currentPage * ITEMS_PER_PAGE, items.length).toString(),
						items.length.toString()
					])}
				{/if}
			</SheetDescription>
		</SheetHeader>

		<div class="mt-4">
			{#if location}
				<!-- Location info -->
				<div class="mb-4 flex items-center gap-2">
					{#if location.country}
						<Badge variant="outline">{location.country}</Badge>
					{/if}
					<span class="text-sm text-muted-foreground">
						{items.length} {t(`map_popup.${itemLabel}`)}
					</span>
					{#if location.yearRange}
						<span class="text-sm text-muted-foreground">
							({location.yearRange.start}–{location.yearRange.end})
						</span>
					{/if}
				</div>

				<!-- Items list -->
				<ScrollArea class="h-[calc(100vh-280px)]">
					<div class="space-y-3 pr-4">
						{#each paginatedItems as item (item.id)}
							<div
								class="rounded-lg border border-border bg-card p-3 transition-colors hover:bg-accent/50"
							>
								<div class="mb-2 flex items-start justify-between gap-2">
									<h4 class="line-clamp-2 text-sm font-medium leading-tight">
										{item.title || t('map_popup.untitled')}
									</h4>
									<Badge variant="secondary" class="shrink-0 text-xs">
										{getItemTypeLabel(item.type)}
									</Badge>
								</div>

								<div class="mb-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
									{#if item.date || item.year}
										<span class="flex items-center gap-1">
											<Calendar class="h-3 w-3" />
											{item.date ? formatDate(item.date) : item.year}
										</span>
									{/if}
									{#if item.newspaper}
										<span class="flex items-center gap-1">
											<Newspaper class="h-3 w-3" />
											{item.newspaper}
										</span>
									{/if}
									{#if item.country}
										<span class="flex items-center gap-1">
											<Flag class="h-3 w-3" />
											{item.country}
										</span>
									{/if}
									{#if item.authors && item.authors.length > 0}
										<span class="line-clamp-1">
											{item.authors.slice(0, 2).join(', ')}{item.authors.length > 2 ? '...' : ''}
										</span>
									{/if}
								</div>

								<Button
									variant="outline"
									size="sm"
									class="w-full"
									href={getItemUrl(item.id)}
									target="_blank"
									rel="noopener noreferrer"
								>
									<ExternalLink class="mr-2 h-3.5 w-3.5" />
									{t('map_popup.view_in_iwac')}
								</Button>
							</div>
						{/each}
					</div>
				</ScrollArea>

				<!-- Pagination controls -->
				{#if totalPages > 1}
					<div class="mt-4 flex items-center justify-between border-t border-border pt-4">
						<Button
							variant="outline"
							size="sm"
							disabled={currentPage === 1}
							onclick={() => goToPage(currentPage - 1)}
						>
							<ChevronLeft class="mr-1 h-4 w-4" />
							{t('map_popup.previous')}
						</Button>

						<div class="flex items-center gap-1">
							{#if totalPages <= 7}
								{#each Array(totalPages) as _, i}
									<Button
										variant={currentPage === i + 1 ? 'default' : 'outline'}
										size="sm"
										class="h-8 w-8 p-0"
										onclick={() => goToPage(i + 1)}
									>
										{i + 1}
									</Button>
								{/each}
							{:else}
								<!-- First page -->
								<Button
									variant={currentPage === 1 ? 'default' : 'outline'}
									size="sm"
									class="h-8 w-8 p-0"
									onclick={() => goToPage(1)}
								>
									1
								</Button>

								{#if currentPage > 3}
									<span class="px-1 text-muted-foreground">...</span>
								{/if}

								<!-- Pages around current -->
								{#each Array(Math.min(3, totalPages - 2)) as _, i}
									{@const page = Math.max(2, Math.min(currentPage - 1, totalPages - 3)) + i}
									{#if page > 1 && page < totalPages}
										<Button
											variant={currentPage === page ? 'default' : 'outline'}
											size="sm"
											class="h-8 w-8 p-0"
											onclick={() => goToPage(page)}
										>
											{page}
										</Button>
									{/if}
								{/each}

								{#if currentPage < totalPages - 2}
									<span class="px-1 text-muted-foreground">...</span>
								{/if}

								<!-- Last page -->
								<Button
									variant={currentPage === totalPages ? 'default' : 'outline'}
									size="sm"
									class="h-8 w-8 p-0"
									onclick={() => goToPage(totalPages)}
								>
									{totalPages}
								</Button>
							{/if}
						</div>

						<Button
							variant="outline"
							size="sm"
							disabled={currentPage === totalPages}
							onclick={() => goToPage(currentPage + 1)}
						>
							{t('map_popup.next')}
							<ChevronRight class="ml-1 h-4 w-4" />
						</Button>
					</div>
				{/if}
			{/if}
		</div>
	</SheetContent>
</Sheet>

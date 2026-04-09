<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { formatDate } from '$lib/utils/formatDate.js';
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
	import { PaginationControls } from '$lib/components/ui/pagination-controls/index.js';
	import { usePagination } from '$lib/hooks/usePagination.svelte.js';
	import { MapPin, ExternalLink, Calendar, Newspaper, Flag } from '@lucide/svelte';
	import type { MapLocation } from '$lib/types/map-location.js';

	interface Props {
		location: MapLocation | null;
		onClose: () => void;
		itemBaseUrl?: string;
		itemLabel?: string;
	}

	let {
		location,
		onClose,
		itemBaseUrl = 'https://islam.zmo.de/s/westafrica/item/',
		itemLabel = 'publications'
	}: Props = $props();

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	// Control sheet open state based on selected location
	const isOpen = $derived(location !== null);

	// Items and pagination
	const items = $derived(location?.items ?? []);
	const pagination = usePagination(() => items);

	function handleOpenChange(open: boolean) {
		if (!open) {
			onClose();
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
						class="h-8 w-8 shrink-0 p-0"
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
				{#if location && pagination.totalPages > 1}
					{t('map_popup.showing', [
						((pagination.currentPage - 1) * pagination.itemsPerPage + 1).toString(),
						Math.min(pagination.currentPage * pagination.itemsPerPage, items.length).toString(),
						items.length.toString()
					])}
				{:else if location}
					{t('map_popup.showing', ['1', items.length.toString(), items.length.toString()])}
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
						{items.length}
						{t(`map_popup.${itemLabel}`)}
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
						{#each pagination.paginatedItems as item (item.id)}
							<div
								class="rounded-lg border border-border bg-card p-3 transition-colors hover:bg-accent/50"
							>
								<div class="mb-2 flex items-start justify-between gap-2">
									<h4 class="line-clamp-2 text-sm leading-tight font-medium">
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
											{item.date ? formatDate(item.date, lang) : item.year}
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
				<PaginationControls
					currentPage={pagination.currentPage}
					totalPages={pagination.totalPages}
					totalItems={items.length}
					itemsPerPage={pagination.itemsPerPage}
					onPageChange={pagination.goToPage}
				/>
			{/if}
		</div>
	</SheetContent>
</Sheet>

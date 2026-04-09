<script lang="ts">
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { ChevronLeft, ChevronRight } from '@lucide/svelte';

	interface Props {
		currentPage: number;
		totalPages: number;
		totalItems: number;
		itemsPerPage: number;
		onPageChange: (page: number) => void;
	}

	let { currentPage, totalPages, totalItems, itemsPerPage, onPageChange }: Props = $props();

	const start = $derived((currentPage - 1) * itemsPerPage + 1);
	const end = $derived(Math.min(currentPage * itemsPerPage, totalItems));
</script>

{#if totalPages > 1}
	<!-- Range info -->
	<div class="mb-3 flex items-center justify-between text-xs text-muted-foreground">
		<span>
			{t('pagination.showing_range', [start.toString(), end.toString(), totalItems.toString()])}
		</span>
		<span>
			{t('pagination.page_of', [currentPage.toString(), totalPages.toString()])}
		</span>
	</div>
{/if}

{#if totalPages > 1}
	<!-- Navigation controls -->
	<div class="mt-4 flex items-center justify-between border-t border-border pt-4">
		<Button
			variant="outline"
			size="sm"
			disabled={currentPage === 1}
			onclick={() => onPageChange(currentPage - 1)}
		>
			<ChevronLeft class="mr-1 h-4 w-4" />
			{t('pagination.previous')}
		</Button>

		<div class="flex items-center gap-1">
			{#if totalPages <= 7}
				{#each Array(totalPages) as _, i (i)}
					<Button
						variant={currentPage === i + 1 ? 'default' : 'outline'}
						size="sm"
						class="h-8 w-8 p-0"
						onclick={() => onPageChange(i + 1)}
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
					onclick={() => onPageChange(1)}
				>
					1
				</Button>

				{#if currentPage > 3}
					<span class="px-1 text-muted-foreground">...</span>
				{/if}

				<!-- Pages around current -->
				{#each Array(Math.min(3, totalPages - 2)) as _, i (i)}
					{@const page = Math.max(2, Math.min(currentPage - 1, totalPages - 3)) + i}
					{#if page > 1 && page < totalPages}
						<Button
							variant={currentPage === page ? 'default' : 'outline'}
							size="sm"
							class="h-8 w-8 p-0"
							onclick={() => onPageChange(page)}
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
					onclick={() => onPageChange(totalPages)}
				>
					{totalPages}
				</Button>
			{/if}
		</div>

		<Button
			variant="outline"
			size="sm"
			disabled={currentPage === totalPages}
			onclick={() => onPageChange(currentPage + 1)}
		>
			{t('pagination.next')}
			<ChevronRight class="ml-1 h-4 w-4" />
		</Button>
	</div>
{/if}

/**
 * usePagination - Reactive Pagination Hook
 *
 * Provides pagination state and controls for any list of items.
 * Uses Svelte 5 runes for reactivity.
 *
 * Usage:
 * ```svelte
 * <script>
 *   import { usePagination } from '$lib/hooks/usePagination.svelte.js';
 *
 *   let allItems = $state([...]);
 *
 *   const pagination = usePagination(() => allItems, { itemsPerPage: 20 });
 *
 *   // Access values
 *   pagination.currentPage;      // current page number (1-based)
 *   pagination.totalPages;       // total number of pages
 *   pagination.paginatedItems;   // items for the current page
 *
 *   // Navigate
 *   pagination.goToPage(3);
 *   pagination.nextPage();
 *   pagination.prevPage();
 * </script>
 * ```
 */

export interface PaginationOptions {
	itemsPerPage?: number;
}

export interface PaginationResult<T> {
	readonly currentPage: number;
	readonly totalPages: number;
	readonly paginatedItems: T[];
	readonly itemsPerPage: number;
	goToPage: (page: number) => void;
	nextPage: () => void;
	prevPage: () => void;
}

export function usePagination<T>(
	items: () => T[],
	options?: PaginationOptions
): PaginationResult<T> {
	const perPage = options?.itemsPerPage ?? 20;
	let currentPage = $state(1);

	const totalPages = $derived(Math.max(1, Math.ceil(items().length / perPage)));

	const paginatedItems = $derived(
		items().slice((currentPage - 1) * perPage, currentPage * perPage)
	);

	// Auto-reset to page 1 when items change (by length or reference)
	let prevItemsRef: T[] | null = null;
	$effect(() => {
		const current = items();
		if (prevItemsRef !== null && current !== prevItemsRef) {
			currentPage = 1;
		}
		prevItemsRef = current;
	});

	function goToPage(page: number) {
		currentPage = Math.max(1, Math.min(page, totalPages));
	}

	function nextPage() {
		goToPage(currentPage + 1);
	}

	function prevPage() {
		goToPage(currentPage - 1);
	}

	return {
		get currentPage() {
			return currentPage;
		},
		get totalPages() {
			return totalPages;
		},
		get paginatedItems() {
			return paginatedItems;
		},
		get itemsPerPage() {
			return perPage;
		},
		goToPage,
		nextPage,
		prevPage
	};
}

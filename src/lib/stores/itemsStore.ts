import { writable, derived } from 'svelte/store';
import type { OmekaItem } from '$lib/types/index.js';

interface ItemsState {
	items: OmekaItem[];
	loading: boolean;
	error: string | null;
}

function createItemsStore() {
	const { subscribe, set, update } = writable<ItemsState>({
		items: [],
		loading: false,
		error: null
	});

	return {
		subscribe,
		loadItems: async () => {
			update((state) => ({ ...state, loading: true, error: null }));
			try {
				// Load data from static JSON file
				const response = await fetch('/data/iwac-data.json');
				if (!response.ok) {
					throw new Error(`Failed to load data: ${response.status} ${response.statusText}`);
				}
				
				const items: OmekaItem[] = await response.json();
				
				// Optional: Add a small delay to show loading state
				await new Promise((resolve) => setTimeout(resolve, 500));

				set({ items, loading: false, error: null });
			} catch (error) {
				set({
					items: [],
					loading: false,
					error: error instanceof Error ? error.message : 'Failed to load data'
				});
			}
		},
		reset: () => {
			set({ items: [], loading: false, error: null });
		}
	};
}

export const itemsStore = createItemsStore();

// Derived stores for computed values
export const totalItems = derived(itemsStore, ($itemsStore) => $itemsStore.items.length);

export const uniqueCountries = derived(itemsStore, ($itemsStore) => {
	const countries = new Set($itemsStore.items.map((item) => item.country).filter(Boolean));
	return Array.from(countries).sort();
});

export const uniqueLanguages = derived(itemsStore, ($itemsStore) => {
	const languages = new Set($itemsStore.items.map((item) => item.language).filter(Boolean));
	return Array.from(languages).sort();
});

export const uniqueTypes = derived(itemsStore, ($itemsStore) => {
	const types = new Set($itemsStore.items.map((item) => item.type).filter(Boolean));
	return Array.from(types).sort();
});

export const statsData = derived(
	[totalItems, uniqueCountries, uniqueLanguages, uniqueTypes],
	([$totalItems, $uniqueCountries, $uniqueLanguages, $uniqueTypes]) => ({
		totalItems: $totalItems,
		countries: $uniqueCountries.length,
		languages: $uniqueLanguages.length,
		types: $uniqueTypes.length
	})
);

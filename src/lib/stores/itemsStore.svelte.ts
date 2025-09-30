import type { OmekaItem } from '$lib/types/index.js';

interface ItemsState {
	items: OmekaItem[];
	loading: boolean;
	error: string | null;
}

class ItemsStore {
	items = $state<OmekaItem[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);

	async loadItems() {
		this.loading = true;
		this.error = null;

		try {
			// Load data from static JSON file
			const response = await fetch('/data/iwac-data.json');
			if (!response.ok) {
				throw new Error(`Failed to load data: ${response.status} ${response.statusText}`);
			}
			
			this.items = await response.json();
			this.loading = false;
			
			// Optional: Add a small delay to show loading state
			await new Promise((resolve) => setTimeout(resolve, 500));
		} catch (err) {
			this.items = [];
			this.loading = false;
			this.error = err instanceof Error ? err.message : 'Failed to load data';
		}
	}

	reset() {
		this.items = [];
		this.loading = false;
		this.error = null;
	}

	// Computed getters
	get totalItems(): number {
		return this.items.length;
	}

	get uniqueCountries(): string[] {
		const countries = new Set(this.items.map((item) => item.country).filter((c): c is string => !!c));
		return Array.from(countries).sort();
	}

	get uniqueLanguages(): string[] {
		const languages = new Set(this.items.map((item) => item.language).filter((l): l is string => !!l));
		return Array.from(languages).sort();
	}

	get uniqueTypes(): string[] {
		const types = new Set(this.items.map((item) => item.type).filter((t): t is string => !!t));
		return Array.from(types).sort();
	}

	get statsData() {
		return {
			totalItems: this.totalItems,
			countries: this.uniqueCountries.length,
			languages: this.uniqueLanguages.length,
			types: this.uniqueTypes.length
		};
	}
}

export const itemsStore = new ItemsStore();

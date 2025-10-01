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

	/**
	 * @deprecated This method is kept for legacy fallback support only.
	 * All data is now loaded from pre-computed JSON files (index-entities.json, etc.).
	 * This method will not be called automatically and can be removed in the future.
	 */
	async loadItems() {
		this.loading = true;
		this.error = null;

		try {
			// Legacy fallback - this file no longer exists
			// Keep this code for backward compatibility but it won't be called
			const response = await fetch('/data/index-entities.json');
			if (!response.ok) {
				throw new Error(`Failed to load data: ${response.status} ${response.statusText}`);
			}
			
			const data = await response.json();
			// Extract items if it's wrapped in a structure
			this.items = Array.isArray(data) ? data : (data.entities || []);
			this.loading = false;
		} catch (err) {
			this.items = [];
			this.loading = false;
			this.error = err instanceof Error ? err.message : 'Failed to load data';
			console.warn('ItemsStore: Failed to load fallback data (this is expected):', err);
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

/**
 * useUrlSync - Svelte 5 Pattern
 * 
 * Provides reactive access to URL state and functions to update it.
 * Must be called within a component context.
 * 
 * This hook does NOT use $effect internally to avoid context issues.
 * Instead, effects must be set up in the component that uses this hook.
 * 
 * Usage:
 * ```svelte
 * <script>
 *   import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
 *   
 *   const urlSync = useUrlSync();
 *   
 *   // Access reactive filter values
 *   console.log(urlSync.filters.country);
 *   
 *   // Update filters
 *   urlSync.setFilter('country', 'Nigeria');
 *   
 *   // Clear filters
 *   urlSync.clearFilter('country');
 * </script>
 * ```
 */

import { browser } from '$app/environment';
import { urlManager } from '$lib/stores/urlManager.svelte.js';

export interface FilterState {
	country?: string;
	type?: string;
	yearMin?: number;
	yearMax?: number;
	search?: string;
	[key: string]: string | number | undefined;
}

export function useUrlSync() {

	// Create a trigger to force re-evaluation when URL changes
	let updateTrigger = $state(0);
	
	// Subscribe to URL manager changes (only in browser)
	$effect(() => {
		if (!browser) return;
		
		const unsubscribe = urlManager.subscribe(() => {
			updateTrigger++;
		});
		return unsubscribe;
	});

	// Create reactive filter state getter that depends on the trigger
	const filters = $derived.by<FilterState>(() => {
		// Access the trigger to create dependency
		const _ = updateTrigger;
		
		return {
			country: urlManager.get('country') as string | undefined,
			type: urlManager.get('type') as string | undefined,
			yearMin: urlManager.get('yearMin') as number | undefined,
			yearMax: urlManager.get('yearMax') as number | undefined,
			search: urlManager.get('search') as string | undefined,
		};
	});

	/**
	 * Set a filter value and update URL
	 */
	function setFilter(key: keyof FilterState, value: string | number | undefined) {
		urlManager.set(key, value);
	}

	/**
	 * Set multiple filters at once
	 */
	function setFilters(updates: Partial<FilterState>) {
		urlManager.setMany(updates);
	}

	/**
	 * Clear a specific filter
	 */
	function clearFilter(key: keyof FilterState) {
		urlManager.clear(key);
	}

	/**
	 * Clear all filters (but keep lang and theme)
	 */
	function clearFilters() {
		const lang = urlManager.get('lang');
		const theme = urlManager.get('theme');
		urlManager.clearAll();
		if (lang) urlManager.set('lang', lang);
		if (theme) urlManager.set('theme', theme);
	}

	/**
	 * Check if a filter is active
	 */
	function hasFilter(key: keyof FilterState): boolean {
		return urlManager.has(key);
	}

	/**
	 * Get all active filter keys
	 */
	function getActiveFilters(): string[] {
		return urlManager.keys().filter(k => !['lang', 'theme'].includes(k));
	}

	return {
		get filters() {
			return filters;
		},
		setFilter,
		setFilters,
		clearFilter,
		clearFilters,
		hasFilter,
		getActiveFilters,
	};
}

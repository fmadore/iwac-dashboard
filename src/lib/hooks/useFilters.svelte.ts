/**
 * useFilters - Enhanced Filter Management Hook
 *
 * Builds on useUrlSync to provide:
 * - Mutually exclusive filter handling
 * - hasActiveFilters derived value
 * - Year range helpers
 * - Filter validation
 * - Default value support
 *
 * Usage:
 * ```svelte
 * <script>
 *   import { useFilters } from '$lib/hooks/useFilters.svelte.js';
 *
 *   // Basic usage
 *   const filters = useFilters();
 *
 *   // With mutually exclusive filters
 *   const filters = useFilters({
 *     mutuallyExclusive: [['type', 'country']]
 *   });
 *
 *   // With defaults and validation
 *   const filters = useFilters({
 *     defaults: { topN: 5, view: 'top' },
 *     validators: {
 *       topN: (v) => typeof v === 'number' && v > 0 && v <= 20
 *     },
 *     excludeFromActive: ['view', 'topN']
 *   });
 *
 *   // Access values
 *   const country = filters.get('country');
 *   const hasFilters = filters.hasActiveFilters;
 *
 *   // Use year range helpers
 *   const { min, max, isSet } = filters.yearRange;
 *   filters.setYearRange(1990, 2020);
 * </script>
 * ```
 */

import { browser } from '$app/environment';
import { urlManager } from '$lib/stores/urlManager.svelte.js';

// Define all possible filter keys
export type FilterKey =
	| 'country'
	| 'type'
	| 'yearMin'
	| 'yearMax'
	| 'search'
	| 'order'
	| 'view'
	| 'term'
	| 'entity'
	| 'focus'
	| 'facet'
	| 'newspaper'
	| 'topN'
	| 'keywords'
	| 'topic'
	| 'year';

export type FilterValue = string | number | undefined;

export interface FilterValues {
	country?: string;
	type?: string;
	yearMin?: number;
	yearMax?: number;
	search?: string;
	order?: string;
	view?: string;
	term?: string;
	entity?: string;
	focus?: string;
	facet?: string;
	newspaper?: string;
	topN?: number;
	keywords?: string;
	topic?: string;
	year?: string;
	[key: string]: FilterValue;
}

export interface YearRange {
	min: number | undefined;
	max: number | undefined;
	isSet: boolean;
}

export interface FilterConfig {
	/** Default values for filters */
	defaults?: Partial<FilterValues>;
	/** Pairs of filter keys that are mutually exclusive - setting one clears the other */
	mutuallyExclusive?: Array<[FilterKey, FilterKey]>;
	/** Validation functions for filter values */
	validators?: Partial<Record<FilterKey, (value: unknown) => boolean>>;
	/** Filter keys to exclude from hasActiveFilters calculation */
	excludeFromActive?: FilterKey[];
}

export interface UseFiltersReturn {
	/** Get a filter value (with default if configured) */
	get: <K extends FilterKey>(key: K) => FilterValues[K];
	/** Set a filter value (handles mutual exclusivity and validation) */
	set: <K extends FilterKey>(key: K, value: FilterValues[K]) => void;
	/** Set multiple filters at once */
	setMany: (updates: Partial<FilterValues>) => void;
	/** Clear a specific filter */
	clear: (key: FilterKey) => void;
	/** Clear all filters (preserves lang and theme) */
	clearAll: () => void;
	/** Check if a filter has a value */
	has: (key: FilterKey) => boolean;
	/** Get all active filter keys (excluding those in excludeFromActive) */
	readonly activeKeys: string[];
	/** Whether any filters are active (excluding those in excludeFromActive) */
	readonly hasActiveFilters: boolean;
	/** Year range helpers */
	readonly yearRange: YearRange;
	/** Set both year min and max at once */
	setYearRange: (min: number | undefined, max: number | undefined) => void;
	/** Clear year range filters */
	clearYearRange: () => void;
	/** Get all current filter values as an object */
	readonly values: Readonly<FilterValues>;
}

// System keys that should never be considered "active" filters
const SYSTEM_KEYS = ['lang', 'theme'];

export function useFilters(config: FilterConfig = {}): UseFiltersReturn {
	const { defaults = {}, mutuallyExclusive = [], validators = {}, excludeFromActive = [] } = config;

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

	/**
	 * Get a filter value, falling back to default if not set
	 */
	function get<K extends FilterKey>(key: K): FilterValues[K] {
		// Access trigger to create dependency
		const _ = updateTrigger;

		const value = urlManager.get(key) as FilterValues[K];
		if (value === undefined && key in defaults) {
			return defaults[key] as FilterValues[K];
		}
		return value;
	}

	/**
	 * Validate a filter value
	 */
	function validate(key: FilterKey, value: FilterValue): boolean {
		const validator = validators[key];
		if (!validator) return true;
		return validator(value);
	}

	/**
	 * Get mutually exclusive keys for a given key
	 */
	function getMutuallyExclusiveKeys(key: FilterKey): FilterKey[] {
		const exclusiveKeys: FilterKey[] = [];
		for (const [a, b] of mutuallyExclusive) {
			if (a === key) exclusiveKeys.push(b);
			if (b === key) exclusiveKeys.push(a);
		}
		return exclusiveKeys;
	}

	/**
	 * Set a filter value with validation and mutual exclusivity handling
	 */
	function set<K extends FilterKey>(key: K, value: FilterValues[K]): void {
		// Validate if validator exists
		if (value !== undefined && !validate(key, value)) {
			console.warn(`Invalid value for filter "${key}":`, value);
			return;
		}

		// Clear mutually exclusive filters
		const exclusiveKeys = getMutuallyExclusiveKeys(key);
		for (const exclusiveKey of exclusiveKeys) {
			if (urlManager.has(exclusiveKey)) {
				urlManager.clear(exclusiveKey);
			}
		}

		// Set the value
		urlManager.set(key, value);
	}

	/**
	 * Set multiple filters at once
	 */
	function setMany(updates: Partial<FilterValues>): void {
		// Validate all values first
		for (const [key, value] of Object.entries(updates)) {
			if (value !== undefined && !validate(key as FilterKey, value)) {
				console.warn(`Invalid value for filter "${key}":`, value);
				delete updates[key];
			}
		}

		// Handle mutual exclusivity - collect all keys to clear
		const keysToClear = new Set<FilterKey>();
		for (const key of Object.keys(updates) as FilterKey[]) {
			const exclusiveKeys = getMutuallyExclusiveKeys(key);
			for (const exclusiveKey of exclusiveKeys) {
				if (!(exclusiveKey in updates)) {
					keysToClear.add(exclusiveKey);
				}
			}
		}

		// Clear mutually exclusive keys first
		for (const key of keysToClear) {
			urlManager.clear(key);
		}

		// Set all values
		urlManager.setMany(updates);
	}

	/**
	 * Clear a specific filter
	 */
	function clear(key: FilterKey): void {
		urlManager.clear(key);
	}

	/**
	 * Clear all filters (preserves lang and theme)
	 */
	function clearAll(): void {
		const lang = urlManager.get('lang');
		const theme = urlManager.get('theme');
		urlManager.clearAll();
		if (lang) urlManager.set('lang', lang);
		if (theme) urlManager.set('theme', theme);
	}

	/**
	 * Check if a filter has a value (not counting defaults)
	 */
	function has(key: FilterKey): boolean {
		// Access trigger to create dependency
		const _ = updateTrigger;
		return urlManager.has(key);
	}

	/**
	 * Set year range
	 */
	function setYearRange(min: number | undefined, max: number | undefined): void {
		const updates: Partial<FilterValues> = {};
		if (min !== undefined) updates.yearMin = min;
		else urlManager.clear('yearMin');
		if (max !== undefined) updates.yearMax = max;
		else urlManager.clear('yearMax');

		if (Object.keys(updates).length > 0) {
			urlManager.setMany(updates);
		}
	}

	/**
	 * Clear year range filters
	 */
	function clearYearRange(): void {
		urlManager.clear('yearMin');
		urlManager.clear('yearMax');
	}

	// Computed: active filter keys (excluding system keys and excludeFromActive)
	const activeKeys = $derived.by<string[]>(() => {
		// Access trigger to create dependency
		const _ = updateTrigger;

		const excludeSet = new Set([...SYSTEM_KEYS, ...excludeFromActive]);
		return urlManager.keys().filter((k) => !excludeSet.has(k as FilterKey));
	});

	// Computed: whether any filters are active
	const hasActiveFilters = $derived(activeKeys.length > 0);

	// Computed: year range helper
	const yearRange = $derived.by<YearRange>(() => {
		// Access trigger to create dependency
		const _ = updateTrigger;

		const min = urlManager.get('yearMin') as number | undefined;
		const max = urlManager.get('yearMax') as number | undefined;
		return {
			min,
			max,
			isSet: min !== undefined || max !== undefined
		};
	});

	// Computed: all current values
	const values = $derived.by<Readonly<FilterValues>>(() => {
		// Access trigger to create dependency
		const _ = updateTrigger;

		const result: FilterValues = {};
		const allKeys: FilterKey[] = [
			'country',
			'type',
			'yearMin',
			'yearMax',
			'search',
			'order',
			'view',
			'term',
			'entity',
			'focus',
			'facet',
			'newspaper',
			'topN',
			'keywords',
			'topic',
			'year'
		];

		for (const key of allKeys) {
			const value = get(key);
			if (value !== undefined) {
				(result as Record<string, FilterValue>)[key] = value;
			}
		}

		return result;
	});

	return {
		get,
		set,
		setMany,
		clear,
		clearAll,
		has,
		get activeKeys() {
			return activeKeys;
		},
		get hasActiveFilters() {
			return hasActiveFilters;
		},
		get yearRange() {
			return yearRange;
		},
		setYearRange,
		clearYearRange,
		get values() {
			return values;
		}
	};
}

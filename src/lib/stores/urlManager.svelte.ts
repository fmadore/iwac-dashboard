/**
 * URL Manager - Svelte 5 Pattern
 *
 * Manages synchronization between app state (language, theme, facets) and URL search parameters.
 * Uses plain JavaScript reactivity (not runes) to avoid component context requirements.
 *
 * Features:
 * - Language (lang=en|fr)
 * - Theme (theme=light|dark)
 * - Facet filters (country, type, year, etc.)
 * - Browser history integration
 * - Type-safe with TypeScript
 */

import { browser } from '$app/environment';
import { replaceState } from '$app/navigation';
import type { Language } from './translationStore.svelte.js';

export type Theme = 'light' | 'dark' | 'system';

export interface UrlState {
	lang?: Language;
	theme?: Theme;
	country?: string;
	type?: string;
	yearMin?: number;
	yearMax?: number;
	search?: string;
	view?: string;
	year?: string;
	// Extensible for other facets
	[key: string]: string | number | undefined;
}

class UrlManager {
	private state: UrlState = {};
	private initialized = false;
	private urlWritingEnabled = false;
	private listeners: Set<() => void> = new Set();

	constructor() {
		// Initialize from URL on construction (client-side only)
		if (browser) {
			this.readFromUrl();
			this.initialized = true;
		}
	}

	/**
	 * Enable URL writing after router is initialized
	 */
	enableUrlWriting() {
		this.urlWritingEnabled = true;
	}

	/**
	 * Subscribe to state changes (for reactivity)
	 */
	subscribe(listener: () => void): () => void {
		this.listeners.add(listener);
		return () => {
			this.listeners.delete(listener);
		};
	}

	/**
	 * Notify all listeners of state change
	 */
	private notify() {
		this.listeners.forEach((listener) => listener());
	}

	/**
	 * Get current state
	 */
	get current(): Readonly<UrlState> {
		return { ...this.state };
	}

	/**
	 * Get a specific value from state
	 */
	get(key: keyof UrlState): string | number | undefined {
		return this.state[key];
	}

	/**
	 * Set a single value and update URL
	 */
	set(key: keyof UrlState, value: string | number | undefined) {
		if (!browser) return;

		// Update state
		if (value === undefined || value === null || value === '') {
			delete this.state[key];
		} else {
			this.state[key] = value;
		}

		// Update URL
		this.writeToUrl();

		// Notify listeners
		this.notify();
	}

	/**
	 * Set multiple values at once and update URL
	 */
	setMany(updates: Partial<UrlState>) {
		if (!browser) return;

		// Update state
		Object.entries(updates).forEach(([key, value]) => {
			if (value === undefined || value === null || value === '') {
				delete this.state[key];
			} else {
				this.state[key] = value;
			}
		});

		// Update URL
		this.writeToUrl();

		// Notify listeners
		this.notify();
	}

	/**
	 * Clear a specific key
	 */
	clear(key: keyof UrlState) {
		if (!browser) return;
		delete this.state[key];
		this.writeToUrl();
		this.notify();
	}

	/**
	 * Clear multiple keys
	 */
	clearMany(keys: (keyof UrlState)[]) {
		if (!browser) return;
		keys.forEach((key) => delete this.state[key]);
		this.writeToUrl();
		this.notify();
	}

	/**
	 * Clear all state
	 */
	clearAll() {
		if (!browser) return;
		this.state = {};
		this.writeToUrl();
		this.notify();
	}

	/**
	 * Read state from URL search params
	 */
	private readFromUrl() {
		if (!browser) return;

		const params = new URLSearchParams(window.location.search);
		const newState: UrlState = {};

		// Language
		const lang = params.get('lang');
		if (lang === 'en' || lang === 'fr') {
			newState.lang = lang;
		}

		// Theme
		const theme = params.get('theme');
		if (theme === 'light' || theme === 'dark' || theme === 'system') {
			newState.theme = theme;
		}

		// Country filter
		const country = params.get('country');
		if (country) {
			newState.country = country;
		}

		// Type filter
		const type = params.get('type');
		if (type) {
			newState.type = type;
		}

		// Year range
		const yearMin = params.get('yearMin');
		if (yearMin) {
			const parsed = parseInt(yearMin, 10);
			if (!isNaN(parsed)) {
				newState.yearMin = parsed;
			}
		}

		const yearMax = params.get('yearMax');
		if (yearMax) {
			const parsed = parseInt(yearMax, 10);
			if (!isNaN(parsed)) {
				newState.yearMax = parsed;
			}
		}

		// Search query
		const search = params.get('search');
		if (search) {
			newState.search = search;
		}

		// Any other params (extensible)
		params.forEach((value, key) => {
			if (!['lang', 'theme', 'country', 'type', 'yearMin', 'yearMax', 'search'].includes(key)) {
				// Try to parse as number, otherwise keep as string
				const numValue = Number(value);
				newState[key] = isNaN(numValue) ? value : numValue;
			}
		});

		this.state = newState;
	}

	/**
	 * Write current state to URL
	 */
	private writeToUrl() {
		if (!browser || !this.urlWritingEnabled) return;

		const params = new URLSearchParams();

		// Add all non-empty values to params
		Object.entries(this.state).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				params.set(key, String(value));
			}
		});

		// Build the new URL with updated search params
		const currentUrl = new URL(window.location.href);
		const newSearch = params.toString();

		// Only update if URL search params actually changed
		if (newSearch !== currentUrl.search.slice(1)) {
			const url = new URL(window.location.origin + window.location.pathname);
			url.search = newSearch;

			// eslint-disable-next-line svelte/no-navigation-without-resolve
			replaceState(url.href, { ...this.state });
		}
	}

	/**
	 * Check if a key exists in state
	 */
	has(key: keyof UrlState): boolean {
		return key in this.state && this.state[key] !== undefined;
	}

	/**
	 * Get all keys currently in state
	 */
	keys(): string[] {
		return Object.keys(this.state);
	}

	/**
	 * Check if manager is initialized (client-side)
	 */
	get isInitialized(): boolean {
		return this.initialized;
	}
}

// Export singleton instance
export const urlManager = new UrlManager();

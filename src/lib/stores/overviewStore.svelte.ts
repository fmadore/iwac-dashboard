/**
 * Overview Statistics Store
 * 
 * Loads and manages precomputed overview statistics from the Python-generated
 * overview-stats.json file. This provides comprehensive statistics for the
 * dashboard overview page including totals, country/language/type breakdowns,
 * and recent items.
 */

import { base } from '$app/paths';

export interface OverviewSummary {
	total_items: number;
	total_words: number;
	total_pages: number;
	total_duration_minutes: number;
	countries: number;
	languages: number;
	types: number;
	newspapers: number;
	audiovisual_duration: number;
	references_count: number;
	country_list: string[];
	language_list: string[];
	type_list: string[];
}

export interface DatasetStats {
	total_records: number;
	total_words: number;
	total_pages: number;
	records_with_word_count: number;
	records_with_page_count: number;
	records_with_ocr: number;
	total_duration_minutes?: number;
	records_with_duration?: number;
	average_duration_minutes?: number;
}

export interface CountryStats {
	total_records: number;
	by_dataset: Record<string, number>;
}

export interface LanguageStats {
	total_records: number;
	by_dataset: Record<string, number>;
}

export interface TypeStats {
	total_records: number;
}

export interface RecentItem {
	title: string;
	country: string;
	language: string;
	type: string;
	created_date: string;
}

export interface OverviewMetadata {
	repository: string;
	generated_at: string;
	script_version: string;
}

export interface OverviewStats {
	metadata: OverviewMetadata;
	summary: OverviewSummary;
	by_dataset: Record<string, DatasetStats>;
	by_country: Record<string, CountryStats>;
	by_language: Record<string, LanguageStats>;
	by_type: Record<string, TypeStats>;
	recent_items: RecentItem[];
}

export interface OverviewStoreState {
	data: OverviewStats | null;
	loading: boolean;
	error: string | null;
}

class OverviewStore {
	data = $state<OverviewStats | null>(null);
	loading = $state(false);
	error = $state<string | null>(null);
	hasLoaded = false;

	async load() {
		if (this.hasLoaded) return;

		this.loading = true;
		this.error = null;

		try {
			const response = await fetch(`${base}/data/overview-stats.json`);
			
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			this.data = await response.json();
			this.loading = false;
			this.hasLoaded = true;
		} catch (e) {
			const error = e instanceof Error ? e.message : 'Failed to load overview statistics';
			this.error = error;
			this.loading = false;
			console.error('Failed to load overview statistics:', e);
		}
	}

	reload() {
		this.hasLoaded = false;
		this.data = null;
		this.loading = false;
		this.error = null;
	}

	// Computed getters using $derived would go in components, not the store
	get summary(): OverviewSummary | null {
		return this.data?.summary || null;
	}

	get byDataset(): Record<string, DatasetStats> {
		return this.data?.by_dataset || {};
	}

	get byCountry(): Record<string, CountryStats> {
		return this.data?.by_country || {};
	}

	get byLanguage(): Record<string, LanguageStats> {
		return this.data?.by_language || {};
	}

	get byType(): Record<string, TypeStats> {
		return this.data?.by_type || {};
	}

	get recentItems(): RecentItem[] {
		return this.data?.recent_items || [];
	}

	get metadata(): OverviewMetadata | null {
		return this.data?.metadata || null;
	}
}

export const overviewStore = new OverviewStore();

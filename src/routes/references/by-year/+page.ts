import { base } from '$app/paths';
import type { PageLoad } from './$types.js';

interface SeriesData {
	name: string;
	data: number[];
}

interface ByYearData {
	years: number[];
	series: SeriesData[];
	total_records: number;
	year_range: {
		min: number;
		max: number;
	};
	country: string | null;
	generated_at: string;
}

interface MetadataResponse {
	total_records: number;
	records_with_year: number;
	temporal: {
		min_year: number;
		max_year: number;
		year_count: number;
	};
	countries: {
		count: number;
		values: string[];
		with_individual_files: string[];
		counts: Record<string, number>;
	};
	reference_types: {
		count: number;
		values: string[];
	};
}

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	try {
		// Preload global data and metadata in parallel
		const [globalResponse, metadataResponse] = await Promise.all([
			fetch(`${base}/data/references/by-year-global.json`),
			fetch(`${base}/data/references/metadata.json`)
		]);

		if (!globalResponse.ok || !metadataResponse.ok) {
			throw new Error('Failed to load data');
		}

		const globalData: ByYearData = await globalResponse.json();
		const metadata: MetadataResponse = await metadataResponse.json();

		return {
			globalData,
			metadata,
			error: null
		};
	} catch (e) {
		return {
			globalData: null,
			metadata: null,
			error: e instanceof Error ? e.message : 'Failed to load references data'
		};
	}
};

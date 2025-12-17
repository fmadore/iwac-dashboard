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

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch(`${base}/data/references/by-year-global.json`);
		if (!response.ok) throw new Error(`HTTP ${response.status}`);
		const data: ByYearData = await response.json();

		return {
			data,
			error: null
		};
	} catch (e) {
		return {
			data: null,
			error: e instanceof Error ? e.message : 'Failed to load references data'
		};
	}
};

import { base } from '$app/paths';
import type { PageLoad } from './$types.js';

interface PublisherData {
	publisher: string;
	publication_count: number;
	types: Record<string, number>;
	earliest_year?: number;
	latest_year?: number;
}

interface PublishersResponse {
	publishers: PublisherData[];
	total_publishers: number;
	total_publications: number;
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
	publishers?: {
		total_unique: number;
		total_publications: number;
	};
}

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	try {
		// Preload global data and metadata in parallel
		const [publishersResponse, metadataResponse] = await Promise.all([
			fetch(`${base}/data/references/publishers.json`),
			fetch(`${base}/data/references/metadata.json`)
		]);

		if (!publishersResponse.ok || !metadataResponse.ok) {
			throw new Error('Failed to load data');
		}

		const publishersData: PublishersResponse = await publishersResponse.json();
		const metadata: MetadataResponse = await metadataResponse.json();

		return {
			publishersData,
			metadata,
			error: null
		};
	} catch (e) {
		return {
			publishersData: null,
			metadata: null,
			error: e instanceof Error ? e.message : 'Failed to load publishers data'
		};
	}
};

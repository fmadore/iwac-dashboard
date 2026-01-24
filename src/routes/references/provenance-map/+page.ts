import { base } from '$app/paths';
import type { PageLoad } from './$types.js';

interface ProvenanceLocation {
	name: string;
	lat: number;
	lng: number;
	count: number;
	countNorm: number;
	types: Record<string, number>;
	publications: Array<{
		pub_id: string;
		title: string;
		type: string;
		year: number | null;
		authors: string[];
	}>;
	o_id?: string;
	earliestYear?: number;
	latestYear?: number;
}

interface ProvenanceMapBounds {
	north: number;
	south: number;
	east: number;
	west: number;
}

interface ProvenanceMapMeta {
	totalLocations: number;
	totalPublications: number;
	maxCount: number;
	generatedAt: string;
}

export interface ProvenanceMapData {
	locations: ProvenanceLocation[];
	bounds: ProvenanceMapBounds | null;
	meta: ProvenanceMapMeta;
}

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch(`${base}/data/references/provenance-map.json`);

		if (!response.ok) {
			throw new Error('Failed to load provenance map data');
		}

		const mapData: ProvenanceMapData = await response.json();

		return {
			mapData,
			error: null
		};
	} catch (e) {
		return {
			mapData: null,
			error: e instanceof Error ? e.message : 'Failed to load provenance map data'
		};
	}
};

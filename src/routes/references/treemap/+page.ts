import { base } from '$app/paths';
import type { PageLoad } from './$types.js';
import type { TreemapData } from '$lib/types/treemap.js';

interface TreemapResponse extends TreemapData {
	meta: {
		totalCountries: number;
		totalReferences: number;
		generatedAt: string;
	};
}

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch(`${base}/data/references/treemap.json`);

		if (!response.ok) {
			throw new Error('Failed to load treemap data');
		}

		const data: TreemapResponse = await response.json();

		return {
			treemapData: data,
			error: null
		};
	} catch (e) {
		return {
			treemapData: null,
			error: e instanceof Error ? e.message : 'Failed to load treemap data'
		};
	}
};

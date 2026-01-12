import type { PageLoad } from './$types.js';
import { base } from '$app/paths';
import type { EntitySpatialIndex } from '$lib/types/entity-spatial.js';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	// Only load the index file initially (summaries)
	// Details are lazy-loaded per entity type when needed
	const response = await fetch(`${base}/data/entity-spatial/index.json`);

	if (!response.ok) {
		console.error(`Failed to load entity-spatial index: ${response.status}`);
		return {
			indexData: null,
			error: `Failed to load data: ${response.status}`
		};
	}

	const indexData: EntitySpatialIndex = await response.json();

	return {
		indexData,
		error: null
	};
};

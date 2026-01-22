import type { PageLoad } from './$types.js';
import { base } from '$app/paths';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const [subjectsResponse, spatialResponse, metadataResponse] = await Promise.all([
		fetch(`${base}/data/keywords-subjects.json`),
		fetch(`${base}/data/keywords-spatial.json`),
		fetch(`${base}/data/keywords-metadata.json`)
	]);

	if (!subjectsResponse.ok) {
		throw new Error(`Failed to load subjects data: ${subjectsResponse.status}`);
	}
	if (!spatialResponse.ok) {
		throw new Error(`Failed to load spatial data: ${spatialResponse.status}`);
	}
	if (!metadataResponse.ok) {
		throw new Error(`Failed to load metadata: ${metadataResponse.status}`);
	}

	const [subjects, spatial, metadata] = await Promise.all([
		subjectsResponse.json(),
		spatialResponse.json(),
		metadataResponse.json()
	]);

	return {
		subjects,
		spatial,
		metadata
	};
};

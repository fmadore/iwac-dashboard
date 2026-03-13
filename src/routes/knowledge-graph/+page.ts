import { base } from '$app/paths';
import type { PageLoad } from './$types.js';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	try {
		const [graphRes, ontologyRes, statsRes] = await Promise.all([
			fetch(`${base}/data/knowledge-graph/graph.json`),
			fetch(`${base}/data/knowledge-graph/ontology.json`),
			fetch(`${base}/data/knowledge-graph/stats.json`)
		]);

		if (!graphRes.ok) {
			throw new Error(`Failed to load graph data: ${graphRes.status}`);
		}

		const [graph, ontology, stats] = await Promise.all([
			graphRes.json(),
			ontologyRes.ok ? ontologyRes.json() : null,
			statsRes.ok ? statsRes.json() : null
		]);

		return { graph, ontology, stats, error: null };
	} catch (e) {
		return {
			graph: null,
			ontology: null,
			stats: null,
			error: e instanceof Error ? e.message : 'Failed to load data'
		};
	}
};

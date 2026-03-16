import { base } from '$app/paths';
import type { PageLoad } from './$types.js';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	try {
		const [graphRes, ontologyRes, statsRes] = await Promise.all([
			fetch(`${base}/data/knowledge-graph/graph.json`),
			fetch(`${base}/data/knowledge-graph/ontology.json`).catch(() => null),
			fetch(`${base}/data/knowledge-graph/stats.json`).catch(() => null)
		]);

		if (!graphRes.ok) {
			throw new Error(`Failed to load graph data: ${graphRes.status}`);
		}

		const graph = await graphRes.json();
		const ontology = ontologyRes?.ok ? await ontologyRes.json() : null;
		const stats = statsRes?.ok ? await statsRes.json() : null;

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

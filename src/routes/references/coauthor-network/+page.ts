import { base } from '$app/paths';
import type { PageLoad } from './$types.js';

interface CoauthorNetworkNode {
	id: string;
	type: 'author';
	label: string;
	count: number;
	degree: number;
	strength: number;
	labelPriority: number;
}

interface CoauthorNetworkEdge {
	source: string;
	target: string;
	type: 'coauthor';
	weight: number;
	weightNorm: number;
	articleIds: string[];
}

interface CoauthorNetworkMeta {
	generatedAt: string;
	totalNodes: number;
	totalEdges: number;
	supportedTypes: string[];
	weightMinConfigured: number;
	weightMinActual: number;
	weightMax: number;
	degree: { min: number; max: number; mean: number };
	strength: { min: number; max: number; mean: number };
	topLabelCount: number;
	typePairs: [string, string][];
	labelPriorityTop: string[];
}

interface CoauthorNetworkData {
	nodes: CoauthorNetworkNode[];
	edges: CoauthorNetworkEdge[];
	meta: CoauthorNetworkMeta;
}

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch(`${base}/data/references/coauthor-network.json`);

		if (!response.ok) {
			throw new Error('Failed to load co-author network data');
		}

		const networkData: CoauthorNetworkData = await response.json();

		return {
			networkData,
			error: null
		};
	} catch (e) {
		return {
			networkData: null,
			error: e instanceof Error ? e.message : 'Failed to load co-author network data'
		};
	}
};

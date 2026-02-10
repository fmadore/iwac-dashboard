import { base } from '$app/paths';
import type { PageLoad } from './$types.js';

interface SubjectCooccurrenceNode {
	id: string;
	type: 'subject';
	label: string;
	count: number;
	degree: number;
	strength: number;
	labelPriority: number;
}

interface SubjectCooccurrenceEdge {
	source: string;
	target: string;
	type: 'subject-subject';
	weight: number;
	weightNorm: number;
	articleIds: string[];
}

interface SubjectCooccurrenceMeta {
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

interface SubjectCooccurrenceData {
	nodes: SubjectCooccurrenceNode[];
	edges: SubjectCooccurrenceEdge[];
	meta: SubjectCooccurrenceMeta;
}

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch(`${base}/data/references/subject-cooccurrence.json`);

		if (!response.ok) {
			throw new Error('Failed to load subject co-occurrence data');
		}

		const networkData: SubjectCooccurrenceData = await response.json();

		return {
			networkData,
			error: null
		};
	} catch (e) {
		return {
			networkData: null,
			error: e instanceof Error ? e.message : 'Failed to load subject co-occurrence data'
		};
	}
};

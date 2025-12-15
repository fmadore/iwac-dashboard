import type { EntryGenerator } from './$types.js';
import type { TopicsSummaryData } from '$lib/types/topics.js';

export const prerender = true;

// Generate entries for all topics
export const entries: EntryGenerator = async () => {
	try {
		// During build, fetch from the static folder
		const summaryModule = await import('../../../../static/data/topics/summary.json');
		const summary: TopicsSummaryData = summaryModule.default;
		return summary.topics.map((topic) => ({ id: topic.id.toString() }));
	} catch {
		// Fallback: return common topic IDs
		return Array.from({ length: 50 }, (_, i) => ({ id: (i - 1).toString() }));
	}
};

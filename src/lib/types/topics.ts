/**
 * Type definitions for Topic Modeling data structures
 */

/** Summary of a single topic in the overview */
export interface TopicSummary {
	id: number;
	label: string;
	count: number;
}

/** Global summary data from summary.json */
export interface TopicsSummaryData {
	total_docs: number;
	unique_topics: number;
	topics: TopicSummary[];
	ai_fields: string[];
}

/** Individual document within a topic */
export interface TopicDocument {
	topic_id: number;
	topic_prob: number;
	topic_label: string;
	pub_date: string | null;
	date: string | null;
	country: string | null;
	newspaper: string | null;
	source: string | null;
	title: string | null;
	ocr_title: string | null;
	url: string | null;
	source_url: string | null;
	'o:source': string | null;
	sentiment_label: string | null;
	sentiment_score: number | null;
	// AI fields (Gemini or ChatGPT)
	gemini_centralite_islam_musulmans?: string | null;
	gemini_centralite_justification?: string | null;
	gemini_subjectivite_score?: number | null;
	gemini_subjectivite_justification?: string | null;
	gemini_polarite?: string | null;
	gemini_polarite_justification?: string | null;
	chatgpt_polarite?: string | null;
	[key: string]: string | number | null | undefined;
}

/** Detailed data for a single topic from {topic_id}.json */
export interface TopicDetailData {
	id: number;
	label: string;
	count: number;
	avg_prob: number;
	counts_by_country: Record<string, number>;
	counts_by_month: Record<string, number>;
	ai_fields: string[];
	docs: TopicDocument[];
}

/** Processed temporal data for charts */
export interface TemporalDataPoint {
	month: string;
	count: number;
}

/** Country distribution for charts */
export interface CountryDataPoint {
	country: string;
	count: number;
}

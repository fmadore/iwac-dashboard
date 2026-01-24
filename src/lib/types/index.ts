// Export treemap types
export type * from './treemap.js';

// Export world map types
export type * from './worldmap.js';

// Export entity spatial types
export type * from './entity-spatial.js';

// Export map location types (reusable map components)
export type * from './map-location.js';

export interface OmekaItem {
	id: number;
	title: string;
	resource_class_label?: string;
	created_date: string;
	publication_date?: string | null;
	num_pages?: number | null;
	language?: string | null;
	word_count?: number;
	item_set_title?: string;
	country?: string | null;
	type?: string;
}

export interface ChartDataPoint {
	label: string;
	value: number;
	percentage?: number;
	metadata?: Record<string, any>;
}

export interface FilterState {
	countries: string[];
	types: string[];
	languages: string[];
	dateRange?: [Date, Date];
}

export interface StatsData {
	totalItems: number;
	countries: number;
	languages: number;
	types: number;
}

export interface ChartConfig {
	type: 'pie' | 'bar' | 'line' | 'doughnut';
	data: any;
	options?: any;
}

// Word cloud types
export interface Word {
	text: string;
	size: number;
	x?: number;
	y?: number;
	rotate?: number;
	font?: string;
	style?: string;
	weight?: string;
	color?: string;
	padding?: number;
}

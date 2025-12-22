/**
 * World Map visualization types for the IWAC Dashboard
 */

export type ViewMode = 'bubbles' | 'choropleth';

export interface GeoJsonFeature {
	type: 'Feature';
	properties: {
		name: string;
		name_long?: string;
		admin?: string;
		iso_a3?: string;
		iso_a2?: string;
		[key: string]: unknown;
	};
	geometry: {
		type: 'Polygon' | 'MultiPolygon';
		coordinates: number[][][] | number[][][][];
	};
}

export interface GeoJsonData {
	type: 'FeatureCollection';
	features: GeoJsonFeature[];
}

export interface LocationData {
	name: string;
	country: string;
	lat: number;
	lng: number;
	articleCount: number;
}

export interface WorldMapData {
	locations: LocationData[];
	countryCounts: Record<string, number>;
	metadata: {
		totalLocations: number;
		totalArticles: number;
		countriesWithData: string[];
		updatedAt: string;
	};
}

export interface MapBounds {
	north: number;
	south: number;
	east: number;
	west: number;
}

export interface BubbleScaleConfig {
	minRadius: number;
	maxRadius: number;
	minValue: number;
	maxValue: number;
}

export interface LegendItem {
	color: string;
	label: string;
	value?: number;
}

export interface ChoroplethScaleConfig {
	mode: 'log' | 'linear' | 'quantile';
	colorRange: string[];
}

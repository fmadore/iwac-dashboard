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

/** Filter data for country and year-based filtering */
export interface WorldMapFilterData {
	/** Available source countries (countries where articles were published) */
	sourceCountries: string[];
	/** Available years in the data */
	years: number[];
	/** Year range for slider */
	yearRange: {
		min: number | null;
		max: number | null;
	};
	/** 
	 * Counts by source country and year
	 * Structure: { sourceCountry: { year: count } }
	 * Year "0" represents articles without a date
	 */
	countsBySourceCountryYear: Record<string, Record<string, number>>;
	/**
	 * Location counts by source country and year for filtering
	 * Structure: { locationName: { sourceCountry: { year: count } } }
	 */
	locationCountsByFilter: Record<string, Record<string, Record<string, number>>>;
}

export interface WorldMapData {
	locations: LocationData[];
	countryCounts: Record<string, number>;
	filterData: WorldMapFilterData;
	metadata: {
		totalLocations: number;
		totalArticles: number;
		countriesWithData: string[];
		sourceCountries: string[];
		yearRange: {
			min: number | null;
			max: number | null;
		};
		generatedAt: string;
		dataSource: string;
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

import type { LngLatLike } from 'maplibre-gl';

/**
 * Base data point for circle layer
 */
export interface CircleDataPoint {
	id: string | number;
	lat: number;
	lng: number;
	value: number;
	label?: string;
	[key: string]: unknown;
}

/**
 * Choropleth data mapping country names to values
 */
export type ChoroplethData = Record<string, number>;

/**
 * Network edge for line layer
 */
export interface NetworkEdge {
	source: [number, number]; // [lng, lat]
	target: [number, number]; // [lng, lat]
	weight: number;
	id?: string;
}

/**
 * Map bounds configuration
 */
export interface MapBounds {
	north: number;
	south: number;
	east: number;
	west: number;
}

/**
 * Map style options
 */
export type MapStyleMode = 'light' | 'dark';

/**
 * Tile provider URLs
 */
export const TILE_STYLES = {
	// OpenFreeMap vector tiles (free, no API key)
	openFreeMap: {
		light: 'https://tiles.openfreemap.org/styles/liberty',
		dark: 'https://tiles.openfreemap.org/styles/dark'
	},
	// CartoDB raster tiles (fallback)
	carto: {
		light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
		dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
	}
} as const;

/**
 * Create a raster tile style for MapLibre
 */
export function createRasterStyle(isDark: boolean): maplibregl.StyleSpecification {
	const tileUrl = isDark ? TILE_STYLES.carto.dark : TILE_STYLES.carto.light;

	return {
		version: 8,
		sources: {
			carto: {
				type: 'raster',
				tiles: [
					tileUrl.replace('{s}', 'a'),
					tileUrl.replace('{s}', 'b'),
					tileUrl.replace('{s}', 'c')
				],
				tileSize: 256,
				attribution:
					'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
			}
		},
		layers: [
			{
				id: 'carto-tiles',
				type: 'raster',
				source: 'carto',
				minzoom: 0,
				maxzoom: 19
			}
		]
	};
}

/**
 * Convert GeoJSON feature collection for MapLibre source
 */
export function toGeoJsonSource(
	features: GeoJSON.Feature[]
): GeoJSON.FeatureCollection<GeoJSON.Geometry> {
	return {
		type: 'FeatureCollection',
		features
	};
}

/**
 * Create a point feature for MapLibre
 */
export function createPointFeature<T extends Record<string, unknown>>(
	id: string | number,
	lng: number,
	lat: number,
	properties: T
): GeoJSON.Feature<GeoJSON.Point, T & { id: string | number }> {
	return {
		type: 'Feature',
		geometry: {
			type: 'Point',
			coordinates: [lng, lat]
		},
		properties: {
			...properties,
			id
		}
	};
}

/**
 * Create a line feature for MapLibre
 */
export function createLineFeature<T extends Record<string, unknown>>(
	id: string | number,
	coordinates: [number, number][],
	properties: T
): GeoJSON.Feature<GeoJSON.LineString, T & { id: string | number }> {
	return {
		type: 'Feature',
		geometry: {
			type: 'LineString',
			coordinates
		},
		properties: {
			...properties,
			id
		}
	};
}

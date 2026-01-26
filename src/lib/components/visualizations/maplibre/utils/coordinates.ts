import type { Map, LngLat } from 'maplibre-gl';
import type { PopoverPosition } from '$lib/types/map-location.js';

/**
 * Convert a MapLibre LngLat to a popover position relative to the map container
 */
export function getPopoverPosition(
	map: Map,
	lngLat: LngLat | { lng: number; lat: number }
): PopoverPosition {
	const point = map.project([lngLat.lng, lngLat.lat]);
	const placement = point.y < 150 ? 'bottom' : 'top';

	return {
		x: point.x,
		y: placement === 'top' ? point.y - 10 : point.y + 10,
		placement
	};
}

/**
 * Calculate bounds from an array of coordinates
 */
export function calculateBounds(
	coordinates: Array<{ lat: number; lng: number }>
): [[number, number], [number, number]] | null {
	if (coordinates.length === 0) return null;

	let minLng = Infinity;
	let maxLng = -Infinity;
	let minLat = Infinity;
	let maxLat = -Infinity;

	for (const coord of coordinates) {
		minLng = Math.min(minLng, coord.lng);
		maxLng = Math.max(maxLng, coord.lng);
		minLat = Math.min(minLat, coord.lat);
		maxLat = Math.max(maxLat, coord.lat);
	}

	// Return as [[sw], [ne]] format for MapLibre
	return [
		[minLng, minLat],
		[maxLng, maxLat]
	];
}

/**
 * West Africa default center point (lng, lat order for MapLibre)
 */
export const WEST_AFRICA_CENTER: [number, number] = [0, 12];

/**
 * Default zoom level for West Africa view
 */
export const DEFAULT_ZOOM = 4;

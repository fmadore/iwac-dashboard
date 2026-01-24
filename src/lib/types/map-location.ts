/**
 * Represents a single item (article, publication, etc.) within a map location.
 */
export interface MapLocationItem {
	id: string;
	title: string;
	type: string;
	year?: number | null;
	date?: string;
	authors?: string[];
	newspaper?: string;
	country?: string;
}

/**
 * Represents a geographic location on the map with associated items.
 */
export interface MapLocation {
	name: string;
	lat: number;
	lng: number;
	count: number;
	country?: string;
	yearRange?: { start: number; end: number };
	externalUrl?: string;
	items: MapLocationItem[];
}

/**
 * Position for popover placement relative to map container.
 */
export interface PopoverPosition {
	x: number;
	y: number;
	placement: 'top' | 'bottom';
}

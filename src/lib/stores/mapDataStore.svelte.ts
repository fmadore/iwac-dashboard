/**
 * World Map state store using Svelte 5 runes
 */
import type { ViewMode, LocationData, WorldMapData } from '$lib/types/worldmap.js';

class MapDataStore {
	viewMode = $state<ViewMode>('bubbles');
	selectedLocation = $state<LocationData | null>(null);
	isLoading = $state(true);
	error = $state<string | null>(null);
	
	// Data
	locations = $state<LocationData[]>([]);
	countryCounts = $state<Record<string, number>>({});
	metadata = $state<WorldMapData['metadata'] | null>(null);
	
	// Map configuration
	zoom = $state(4);
	center = $state<[number, number]>([8, 2]); // West Africa center
	
	setViewMode(mode: ViewMode) {
		this.viewMode = mode;
	}
	
	setSelectedLocation(location: LocationData | null) {
		this.selectedLocation = location;
	}
	
	setData(data: WorldMapData) {
		this.locations = data.locations;
		this.countryCounts = data.countryCounts;
		this.metadata = data.metadata;
		this.isLoading = false;
		this.error = null;
	}
	
	setLoading(loading: boolean) {
		this.isLoading = loading;
	}
	
	setError(error: string | null) {
		this.error = error;
		this.isLoading = false;
	}
	
	reset() {
		this.viewMode = 'bubbles';
		this.selectedLocation = null;
		this.locations = [];
		this.countryCounts = {};
		this.metadata = null;
		this.isLoading = true;
		this.error = null;
	}
}

export const mapDataStore = new MapDataStore();

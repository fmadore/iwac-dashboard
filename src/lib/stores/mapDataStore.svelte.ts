/**
 * World Map state store using Svelte 5 runes
 */
import type { ViewMode, LocationData, WorldMapData, WorldMapFilterData } from '$lib/types/worldmap.js';

class MapDataStore {
	viewMode = $state<ViewMode>('bubbles');
	selectedLocation = $state<LocationData | null>(null);
	isLoading = $state(true);
	error = $state<string | null>(null);
	
	// Data
	locations = $state<LocationData[]>([]);
	countryCounts = $state<Record<string, number>>({});
	metadata = $state<WorldMapData['metadata'] | null>(null);
	filterData = $state<WorldMapFilterData | null>(null);
	
	// Filter state
	selectedSourceCountry = $state<string | null>(null); // null means "All countries"
	selectedYearRange = $state<[number, number] | null>(null); // null means full range
	
	// Map configuration
	zoom = $state(4);
	center = $state<[number, number]>([8, 2]); // West Africa center
	
	// Derived filtered data
	get filteredLocations(): LocationData[] {
		if (!this.selectedSourceCountry && !this.selectedYearRange) {
			return this.locations;
		}
		
		if (!this.filterData?.locationCountsByFilter) {
			return this.locations;
		}
		
		return this.locations
			.map(loc => {
				const locFilterData = this.filterData?.locationCountsByFilter[loc.name];
				if (!locFilterData) {
					return { ...loc, articleCount: 0 };
				}
				
				let count = 0;
				const sourceCountries = this.selectedSourceCountry 
					? [this.selectedSourceCountry] 
					: Object.keys(locFilterData);
				
				for (const srcCountry of sourceCountries) {
					const yearData = locFilterData[srcCountry];
					if (!yearData) continue;
					
					if (this.selectedYearRange) {
						const [minYear, maxYear] = this.selectedYearRange;
						for (const [yearStr, yearCount] of Object.entries(yearData)) {
							const year = parseInt(yearStr, 10);
							if (year >= minYear && year <= maxYear) {
								count += yearCount;
							}
						}
					} else {
						// Sum all years
						count += Object.values(yearData).reduce((sum, c) => sum + c, 0);
					}
				}
				
				return { ...loc, articleCount: count };
			})
			.filter(loc => loc.articleCount > 0);
	}
	
	get filteredCountryCounts(): Record<string, number> {
		if (!this.selectedSourceCountry && !this.selectedYearRange) {
			return this.countryCounts;
		}
		
		// Aggregate filtered location counts by country
		const counts: Record<string, number> = {};
		for (const loc of this.filteredLocations) {
			if (loc.country && loc.country !== 'Unknown') {
				counts[loc.country] = (counts[loc.country] || 0) + loc.articleCount;
			}
		}
		return counts;
	}
	
	get availableSourceCountries(): string[] {
		return this.filterData?.sourceCountries ?? [];
	}
	
	get yearRange(): { min: number; max: number } | null {
		const range = this.filterData?.yearRange;
		if (range && range.min !== null && range.max !== null) {
			return { min: range.min, max: range.max };
		}
		return null;
	}
	
	setViewMode(mode: ViewMode) {
		this.viewMode = mode;
	}
	
	setSelectedLocation(location: LocationData | null) {
		this.selectedLocation = location;
	}
	
	setSelectedSourceCountry(country: string | null) {
		this.selectedSourceCountry = country;
	}
	
	setSelectedYearRange(range: [number, number] | null) {
		this.selectedYearRange = range;
	}
	
	setData(data: WorldMapData) {
		this.locations = data.locations;
		this.countryCounts = data.countryCounts;
		this.metadata = data.metadata;
		this.filterData = data.filterData ?? null;
		this.isLoading = false;
		this.error = null;
		
		// Initialize year range to full range
		if (data.filterData?.yearRange) {
			const { min, max } = data.filterData.yearRange;
			if (min !== null && max !== null) {
				this.selectedYearRange = null; // null means show all
			}
		}
	}
	
	setLoading(loading: boolean) {
		this.isLoading = loading;
	}
	
	setError(error: string | null) {
		this.error = error;
		this.isLoading = false;
	}
	
	resetFilters() {
		this.selectedSourceCountry = null;
		this.selectedYearRange = null;
	}
	
	reset() {
		this.viewMode = 'bubbles';
		this.selectedLocation = null;
		this.locations = [];
		this.countryCounts = {};
		this.metadata = null;
		this.filterData = null;
		this.selectedSourceCountry = null;
		this.selectedYearRange = null;
		this.isLoading = true;
		this.error = null;
	}
}

export const mapDataStore = new MapDataStore();

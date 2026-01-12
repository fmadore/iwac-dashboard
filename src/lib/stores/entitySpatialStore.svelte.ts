/**
 * Entity Spatial state store using Svelte 5 runes
 *
 * Manages state for the entity spatial visualization including:
 * - Selected entity category
 * - Selected entity
 * - Selected location on map
 * - Lazy loading of individual entity details
 */

import { base } from '$app/paths';
import type {
	EntityType,
	EntitySummary,
	EntityDetail,
	EntityLocation,
	EntitySpatialIndex
} from '$lib/types/entity-spatial.js';

class EntitySpatialStore {
	// UI State
	selectedCategory = $state<EntityType>('Personnes');
	selectedEntityId = $state<number | null>(null);
	selectedLocation = $state<EntityLocation | null>(null);
	searchQuery = $state<string>('');

	// Loading state
	isLoading = $state(true);
	isLoadingDetails = $state(false);
	error = $state<string | null>(null);

	// Data - index (summaries)
	indexData = $state<EntitySpatialIndex | null>(null);

	// Data - currently loaded entity detail (one at a time)
	currentEntityDetail = $state<EntityDetail | null>(null);

	// Cache of loaded entity details to avoid re-fetching
	entityCache = $state<Map<string, EntityDetail>>(new Map());

	// Derived: entities in current category
	get entitiesInCategory(): EntitySummary[] {
		if (!this.indexData?.entities) return [];
		return this.indexData.entities[this.selectedCategory] ?? [];
	}

	// Derived: filtered entities based on search
	get filteredEntities(): EntitySummary[] {
		const entities = this.entitiesInCategory;
		if (!this.searchQuery.trim()) {
			return entities;
		}
		const query = this.searchQuery.toLowerCase().trim();
		return entities.filter((e) => e.name.toLowerCase().includes(query));
	}

	// Derived: current entity details
	get currentEntity(): EntityDetail | null {
		return this.currentEntityDetail;
	}

	// Derived: locations for current entity
	get currentLocations(): EntityLocation[] {
		return this.currentEntity?.locations ?? [];
	}

	// Derived: articles at selected location
	get currentLocationArticles() {
		if (!this.selectedLocation) return [];
		return this.selectedLocation.articles;
	}

	// Derived: category counts for display
	get categoryCounts(): Record<EntityType, number> {
		if (!this.indexData?.entities) {
			return {
				Personnes: 0,
				Événements: 0,
				Sujets: 0,
				Organisations: 0
			};
		}
		return {
			Personnes: this.indexData.entities['Personnes']?.length ?? 0,
			Événements: this.indexData.entities['Événements']?.length ?? 0,
			Sujets: this.indexData.entities['Sujets']?.length ?? 0,
			Organisations: this.indexData.entities['Organisations']?.length ?? 0
		};
	}

	// Actions
	setCategory(category: EntityType) {
		this.selectedCategory = category;
		this.selectedEntityId = null;
		this.selectedLocation = null;
		this.currentEntityDetail = null;
		this.searchQuery = '';
	}

	async setSelectedEntity(entityId: number | null) {
		this.selectedEntityId = entityId;
		this.selectedLocation = null;
		this.currentEntityDetail = null;

		if (entityId) {
			await this.loadEntityDetail(entityId);
		}
	}

	setSelectedLocation(location: EntityLocation | null) {
		this.selectedLocation = location;
	}

	setSearchQuery(query: string) {
		this.searchQuery = query;
	}

	setIndexData(data: EntitySpatialIndex) {
		this.indexData = data;
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

	// Load details for a specific entity
	async loadEntityDetail(entityId: number): Promise<void> {
		const cacheKey = `${this.selectedCategory}/${entityId}`;

		// Check cache first
		const cached = this.entityCache.get(cacheKey);
		if (cached) {
			this.currentEntityDetail = cached;
			return;
		}

		this.isLoadingDetails = true;

		try {
			const response = await fetch(
				`${base}/data/entity-spatial/${this.selectedCategory}/${entityId}.json`
			);

			if (!response.ok) {
				// Entity might not have location data - this is normal
				if (response.status === 404) {
					console.info(`No location data for entity ${entityId}`);
					this.currentEntityDetail = null;
				} else {
					console.warn(`Failed to load entity ${entityId}: ${response.status}`);
				}
				return;
			}

			const detail: EntityDetail = await response.json();
			this.currentEntityDetail = detail;

			// Add to cache
			const newCache = new Map(this.entityCache);
			newCache.set(cacheKey, detail);
			this.entityCache = newCache;
		} catch (error) {
			console.error(`Error loading entity ${entityId}:`, error);
			this.currentEntityDetail = null;
		} finally {
			this.isLoadingDetails = false;
		}
	}

	reset() {
		this.selectedCategory = 'Personnes';
		this.selectedEntityId = null;
		this.selectedLocation = null;
		this.searchQuery = '';
		this.indexData = null;
		this.currentEntityDetail = null;
		this.entityCache = new Map();
		this.isLoading = true;
		this.isLoadingDetails = false;
		this.error = null;
	}
}

export const entitySpatialStore = new EntitySpatialStore();

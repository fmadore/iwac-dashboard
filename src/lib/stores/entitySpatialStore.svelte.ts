/**
 * Entity Spatial state store using Svelte 5 runes
 *
 * Manages state for the entity spatial visualization including:
 * - Selected entity category
 * - Selected entity
 * - Selected location on map
 * - Lazy loading of entity details by type
 */

import { base } from '$app/paths';
import type {
	EntityType,
	EntitySummary,
	EntityDetail,
	EntityLocation,
	EntitySpatialIndex,
	EntityTypeDetails
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

	// Data - details by type (lazy loaded)
	detailsByType = $state<Partial<Record<EntityType, EntityTypeDetails>>>({});

	// Track which types have been loaded
	loadedTypes = $state<Set<EntityType>>(new Set());

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
		if (!this.selectedEntityId) return null;
		const typeDetails = this.detailsByType[this.selectedCategory];
		if (!typeDetails) return null;
		return typeDetails[String(this.selectedEntityId)] ?? null;
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
	async setCategory(category: EntityType) {
		this.selectedCategory = category;
		this.selectedEntityId = null;
		this.selectedLocation = null;
		this.searchQuery = '';

		// Load details for this category if not already loaded
		if (!this.loadedTypes.has(category)) {
			await this.loadTypeDetails(category);
		}
	}

	async setSelectedEntity(entityId: number | null) {
		this.selectedEntityId = entityId;
		this.selectedLocation = null;

		// Ensure details are loaded for current category
		if (entityId && !this.loadedTypes.has(this.selectedCategory)) {
			await this.loadTypeDetails(this.selectedCategory);
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

	// Load entity details for a specific type
	async loadTypeDetails(entityType: EntityType): Promise<void> {
		if (this.loadedTypes.has(entityType)) {
			return;
		}

		this.isLoadingDetails = true;

		try {
			const response = await fetch(`${base}/data/entity-spatial/${entityType}.json`);

			if (!response.ok) {
				console.warn(`Failed to load details for ${entityType}: ${response.status}`);
				// Mark as loaded anyway to prevent repeated attempts
				this.loadedTypes = new Set([...this.loadedTypes, entityType]);
				this.detailsByType[entityType] = {};
				return;
			}

			const details: EntityTypeDetails = await response.json();
			this.detailsByType[entityType] = details;
			this.loadedTypes = new Set([...this.loadedTypes, entityType]);
		} catch (error) {
			console.error(`Error loading details for ${entityType}:`, error);
			// Mark as loaded to prevent repeated attempts
			this.loadedTypes = new Set([...this.loadedTypes, entityType]);
			this.detailsByType[entityType] = {};
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
		this.detailsByType = {};
		this.loadedTypes = new Set();
		this.isLoading = true;
		this.isLoadingDetails = false;
		this.error = null;
	}
}

export const entitySpatialStore = new EntitySpatialStore();

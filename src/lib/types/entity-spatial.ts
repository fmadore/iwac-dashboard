/**
 * Entity Spatial visualization types for the IWAC Dashboard
 *
 * Represents the data structure for showing where entities
 * (persons, events, topics, organisations) appear geographically.
 */

/** Supported entity types */
export type EntityType = 'Personnes' | 'Événements' | 'Sujets' | 'Organisations';

/** Article reference in entity spatial data */
export interface EntityArticle {
	id: string;
	title: string;
	date: string;
	newspaper: string;
	country: string;
	type: string; // 'articles' | 'publications'
}

/** Location with associated articles for an entity */
export interface EntityLocation {
	name: string;
	lat: number;
	lng: number;
	country: string;
	articleCount: number;
	articles: EntityArticle[];
}

/** Entity summary for picker/search (from index.json) */
export interface EntitySummary {
	id: number;
	name: string;
	articleCount: number;
	locationCount: number;
}

/** Full entity details with all location data (from {Type}/{entityId}.json) */
export interface EntityDetail {
	id: number;
	name: string;
	type: EntityType;
	stats: {
		articleCount: number;
		countries: string[];
		dateRange: {
			first: string;
			last: string;
		};
	};
	locations: EntityLocation[];
}

/** Type labels for i18n */
export interface TypeLabels {
	[key: string]: {
		en: string;
		fr: string;
	};
}

/** Index data structure (from index.json) */
export interface EntitySpatialIndex {
	/** Entities grouped by type (summaries only) */
	entities: Record<EntityType, EntitySummary[]>;
	/** Type labels for i18n */
	typeLabels: TypeLabels;
	/** Generation metadata */
	metadata: {
		totalEntities: number;
		entitiesWithLocations: number;
		entityTypes: EntityType[];
		generatedAt: string;
		dataSource: string;
	};
}

/** Props for EntityLocationMap component */
export interface EntityLocationMapProps {
	locations: EntityLocation[];
	onLocationSelect?: (location: EntityLocation) => void;
	selectedLocation?: EntityLocation | null;
	height?: string;
}

/** Props for LocationArticlePanel component */
export interface LocationArticlePanelProps {
	location: EntityLocation | null;
	entityName: string;
	onClose: () => void;
}

/** Props for EntityStatsCards component */
export interface EntityStatsCardsProps {
	articleCount: number;
	countries: string[];
	dateRange: {
		first: string;
		last: string;
	};
}

<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { entitySpatialStore } from '$lib/stores/entitySpatialStore.svelte.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { MapLocationPopover } from '$lib/components/visualizations/map/index.js';
	import {
		BaseMap,
		CircleLayer,
		type CircleDataPoint,
		calculateBounds
	} from '$lib/components/visualizations/maplibre/index.js';
	import type { EntityLocation } from '$lib/types/entity-spatial.js';
	import type { MapLocation, PopoverPosition } from '$lib/types/map-location.js';

	interface Props {
		height?: string;
	}

	let { height = '500px' }: Props = $props();

	// Derived state from store
	const locations = $derived(entitySpatialStore.currentLocations);
	const selectedLocation = $derived(entitySpatialStore.selectedLocation);
	const currentEntity = $derived(entitySpatialStore.currentEntity);

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	// Loading state (we use BaseMap's built-in loading now)
	let mapLoading = $state(false);

	// Popover state
	let hoveredLocation = $state<MapLocation | null>(null);
	let popoverPosition = $state<PopoverPosition | null>(null);

	// Transform EntityLocation to MapLocation
	function toMapLocation(location: EntityLocation): MapLocation {
		return {
			name: location.name,
			lat: location.lat,
			lng: location.lng,
			count: location.articleCount,
			country: location.country,
			items: [] // Items are loaded separately via entitySpatialStore
		};
	}

	// Transform locations to CircleDataPoints for MapLibre
	const circleData = $derived<CircleDataPoint[]>(
		locations.map((location) => ({
			id: location.name,
			lat: location.lat,
			lng: location.lng,
			value: location.articleCount,
			label: location.name,
			country: location.country
		}))
	);

	// Get selected ID for highlighting
	const selectedId = $derived(selectedLocation?.name ?? null);

	// Calculate bounds from locations
	const bounds = $derived.by(() => {
		if (locations.length === 0) return undefined;
		const coords = locations.map((l) => ({ lat: l.lat, lng: l.lng }));
		return calculateBounds(coords) ?? undefined;
	});

	// Handle hover from CircleLayer
	function handleHover(item: CircleDataPoint | null, position: PopoverPosition | null) {
		if (item) {
			const location = locations.find((l) => l.name === item.id);
			if (location) {
				hoveredLocation = toMapLocation(location);
				popoverPosition = position;
			}
		} else {
			hoveredLocation = null;
			popoverPosition = null;
		}
	}

	// Handle click from CircleLayer
	function handleClick(item: CircleDataPoint) {
		const location = locations.find((l) => l.name === item.id);
		if (location) {
			entitySpatialStore.setSelectedLocation(location);
			hoveredLocation = null;
			popoverPosition = null;
		}
	}
</script>

<div class="map-wrapper relative">
	<div
		class="map-container relative z-0"
		style="height: {height};"
		data-testid="entity-map-container"
	>
		<BaseMap height={height} bounds={bounds} zoom={4} maxZoom={8}>
			{#if circleData.length > 0}
				<CircleLayer
					data={circleData}
					radiusRange={[8, 35]}
					selectedId={selectedId}
					onHover={handleHover}
					onClick={handleClick}
				/>
			{/if}
		</BaseMap>

		<!-- Hover popover -->
		<MapLocationPopover location={hoveredLocation} position={popoverPosition} itemLabel="articles" />
	</div>

	{#if !mapLoading && locations.length === 0 && currentEntity}
		<div class="absolute inset-0 flex items-center justify-center bg-background/50">
			<p class="text-muted-foreground">{t('entity_spatial.no_locations')}</p>
		</div>
	{/if}

	{#if !mapLoading && !currentEntity}
		<div class="absolute inset-0 flex items-center justify-center bg-background/50">
			<p class="text-muted-foreground">{t('entity_spatial.no_entity_selected')}</p>
		</div>
	{/if}
</div>

<style>
	.map-wrapper {
		width: 100%;
	}

	.map-container {
		width: 100%;
		background: linear-gradient(135deg, var(--muted) 0%, var(--background) 100%);
		border-radius: 12px;
		overflow: hidden;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
		border: 1px solid var(--border);
	}
</style>

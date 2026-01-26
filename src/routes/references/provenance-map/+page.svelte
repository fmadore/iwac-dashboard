<script lang="ts">
	import { browser } from '$app/environment';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { StatsCard } from '$lib/components/dashboard/index.js';
	import { MapLocationPopover, MapLocationSheet } from '$lib/components/visualizations/map/index.js';
	import { BaseMap, CircleLayer, type CircleDataPoint, calculateBounds } from '$lib/components/visualizations/maplibre/index.js';
	import { ExternalLink, MapPin } from '@lucide/svelte';
	import type { ProvenanceMapData } from './+page.js';
	import type { MapLocation, PopoverPosition } from '$lib/types/map-location.js';

	// Get preloaded data from +page.ts
	let { data: pageData } = $props<{
		data: {
			mapData: ProvenanceMapData | null;
			error: string | null;
		};
	}>();

	const mapData = $derived(pageData.mapData);
	const error = $derived(pageData.error);

	// Popover and sheet state
	let hoveredLocation = $state<MapLocation | null>(null);
	let selectedLocation = $state<MapLocation | null>(null);
	let popoverPosition = $state<PopoverPosition | null>(null);

	// Build islam.zmo.de URL based on current language
	function getItemUrl(oId: string): string {
		const lang = languageStore.current;
		const path = lang === 'fr' ? 'afrique_ouest' : 'westafrica';
		return `https://islam.zmo.de/s/${path}/item/${oId}`;
	}

	// Transform ProvenanceLocation to MapLocation
	function toMapLocation(location: ProvenanceMapData['locations'][0]): MapLocation {
		return {
			name: location.name,
			lat: location.lat,
			lng: location.lng,
			count: location.count,
			yearRange: location.earliestYear && location.latestYear
				? { start: location.earliestYear, end: location.latestYear }
				: undefined,
			externalUrl: location.o_id ? getItemUrl(location.o_id) : undefined,
			items: location.publications.map(pub => ({
				id: pub.pub_id,
				title: pub.title,
				type: pub.type,
				year: pub.year,
				authors: pub.authors
			}))
		};
	}

	// Transform locations to CircleDataPoints for MapLibre
	const circleData = $derived<CircleDataPoint[]>(
		mapData?.locations.map((location) => ({
			id: location.name,
			lat: location.lat,
			lng: location.lng,
			value: location.count,
			label: location.name,
			o_id: location.o_id,
			earliestYear: location.earliestYear,
			latestYear: location.latestYear,
			types: location.types,
			publications: location.publications
		})) ?? []
	);

	// Calculate bounds from locations
	const bounds = $derived.by(() => {
		if (!mapData?.locations?.length) return undefined;
		const coords = mapData.locations.map(l => ({ lat: l.lat, lng: l.lng }));
		return calculateBounds(coords) ?? undefined;
	});

	// Handle hover from CircleLayer
	function handleHover(item: CircleDataPoint | null, position: PopoverPosition | null) {
		if (item && mapData) {
			const location = mapData.locations.find(l => l.name === item.id);
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
		if (mapData) {
			const location = mapData.locations.find(l => l.name === item.id);
			if (location) {
				selectedLocation = toMapLocation(location);
				hoveredLocation = null;
				popoverPosition = null;
			}
		}
	}

	function handleSheetClose() {
		selectedLocation = null;
	}
</script>

<svelte:head>
	<title>{t('provenance.title')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 py-6">
	<!-- Page Header -->
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight text-foreground">{t('provenance.title')}</h1>
		<p class="text-muted-foreground">{t('provenance.description')}</p>
	</div>

	{#if !mapData && !error}
		<div class="space-y-4">
			<div class="grid gap-4 md:grid-cols-3">
				{#each Array(3) as _, i (i)}
					<Skeleton class="h-24" />
				{/each}
			</div>
			<Skeleton class="h-[600px]" />
		</div>
	{:else if error}
		<Card.Root class="p-6">
			<div class="py-12 text-center">
				<h3 class="mb-2 text-xl font-semibold text-destructive">{t('common.error')}</h3>
				<p class="text-muted-foreground">{error}</p>
				<p class="mt-4 text-sm text-muted-foreground">
					{t('provenance.run_script_hint')}
				</p>
			</div>
		</Card.Root>
	{:else if mapData}
		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-3">
			<StatsCard title={t('provenance.total_locations')} value={mapData.meta.totalLocations} />
			<StatsCard
				title={t('provenance.total_publications')}
				value={mapData.meta.totalPublications}
			/>
			<StatsCard title={t('provenance.top_location')} value={mapData.locations[0]?.name || '—'} />
		</div>

		<!-- Map Card -->
		<Card.Root class="overflow-hidden">
			<Card.Header>
				<Card.Title class="flex items-center gap-2">
					<MapPin class="h-5 w-5" />
					{t('provenance.map_title')}
				</Card.Title>
				<Card.Description>{t('provenance.map_description')}</Card.Description>
			</Card.Header>
			<Card.Content class="p-0">
				<div class="relative h-[600px]">
					<BaseMap height="600px" bounds={bounds} zoom={5}>
						{#if circleData.length > 0}
							<CircleLayer
								data={circleData}
								radiusRange={[8, 40]}
								colorRange={['#f97316', '#ea580c']}
								onHover={handleHover}
								onClick={handleClick}
							/>
						{/if}
					</BaseMap>

					<!-- Hover popover -->
					<MapLocationPopover
						location={hoveredLocation}
						position={popoverPosition}
						itemLabel="publications"
					/>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Legend -->
		<Card.Root>
			<Card.Content class="py-4">
				<div class="flex flex-wrap items-center gap-6 text-sm">
					<div class="flex items-center gap-2">
						<div class="h-4 w-4 rounded-full bg-orange-500/60 border-2 border-orange-700"></div>
						<span class="text-muted-foreground">{t('provenance.legend_size')}</span>
					</div>
					<div class="flex items-center gap-4">
						<div class="flex items-center gap-1">
							<div class="h-3 w-3 rounded-full bg-orange-500/60 border border-orange-700"></div>
							<span class="text-xs text-muted-foreground">1</span>
						</div>
						<div class="flex items-center gap-1">
							<div class="h-6 w-6 rounded-full bg-orange-500/60 border-2 border-orange-700"></div>
							<span class="text-xs text-muted-foreground">{mapData.meta.maxCount}</span>
						</div>
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Top Locations Table -->
		<Card.Root>
			<Card.Header>
				<Card.Title>{t('provenance.top_locations')}</Card.Title>
				<Card.Description>{t('provenance.top_locations_description')}</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b">
								<th class="py-2 text-left font-medium">{t('provenance.location')}</th>
								<th class="py-2 text-right font-medium">{t('provenance.publications')}</th>
								<th class="py-2 text-left font-medium">{t('provenance.year_range')}</th>
								<th class="py-2 text-left font-medium">{t('provenance.top_type')}</th>
							</tr>
						</thead>
						<tbody>
							{#each mapData.locations.slice(0, 20) as location (location.name)}
								{@const topType = Object.entries(location.types).sort((a, b) => (b[1] as number) - (a[1] as number))[0]}
								<tr class="border-b border-border/50 hover:bg-muted/50">
									<td class="py-2">
										{#if location.o_id}
											<a
												href={getItemUrl(location.o_id)}
												target="_blank"
												rel="noopener noreferrer"
												class="inline-flex items-center gap-1 text-primary hover:underline"
											>
												{location.name}
												<ExternalLink class="h-3 w-3" />
											</a>
										{:else}
											{location.name}
										{/if}
									</td>
									<td class="py-2 text-right font-medium">{location.count}</td>
									<td class="py-2 text-muted-foreground">
										{#if location.earliestYear && location.latestYear}
											{location.earliestYear}–{location.latestYear}
										{:else}
											—
										{/if}
									</td>
									<td class="py-2">
										{#if topType}
											<Badge variant="outline" class="text-xs">
												{t(`type.${topType[0]}`, [topType[0]])} ({topType[1]})
											</Badge>
										{:else}
											—
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

<!-- Sheet for location details (at page level to avoid clipping) -->
<MapLocationSheet
	location={selectedLocation}
	onClose={handleSheetClose}
	itemLabel="publications"
/>

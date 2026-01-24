<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { StatsCard } from '$lib/components/dashboard/index.js';
	import { ExternalLink, MapPin } from '@lucide/svelte';
	import { scaleSqrt } from 'd3-scale';
	import type { ProvenanceMapData } from './+page.js';

	// Get preloaded data from +page.ts
	let { data: pageData } = $props<{
		data: {
			mapData: ProvenanceMapData | null;
			error: string | null;
		};
	}>();

	const mapData = $derived(pageData.mapData);
	const error = $derived(pageData.error);

	// Map state
	let mapElement: HTMLDivElement | null = $state(null);
	let map: L.Map | null = $state(null);
	let L: typeof import('leaflet') | null = null;
	let markersLayer: L.LayerGroup | null = null;
	let mapLoading = $state(true);

	// Build islam.zmo.de URL based on current language
	function getItemUrl(oId: string): string {
		const lang = languageStore.current;
		const path = lang === 'fr' ? 'afrique_ouest' : 'westafrica';
		return `https://islam.zmo.de/s/${path}/item/${oId}`;
	}

	// Tile layer configuration
	const tileLayerOptions = {
		light: {
			url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
			attribution:
				'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
		},
		dark: {
			url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
			attribution:
				'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
		}
	};

	function isDarkActive(): boolean {
		if (!browser) return false;
		return document.documentElement.classList.contains('dark');
	}

	async function initMap() {
		if (!browser || !mapElement || !mapData) return;

		try {
			L = await import('leaflet');
			await import('leaflet/dist/leaflet.css');

			// Clean up existing map
			if (map) {
				map.remove();
				map = null;
			}

			// Create map
			const isDark = isDarkActive();
			const tileOptions = isDark ? tileLayerOptions.dark : tileLayerOptions.light;

			map = L.map(mapElement, {
				zoomControl: true,
				scrollWheelZoom: true
			});

			// Add tile layer
			L.tileLayer(tileOptions.url, {
				attribution: tileOptions.attribution,
				maxZoom: 18
			}).addTo(map);

			// Set initial view
			if (mapData.bounds) {
				const bounds = L.latLngBounds(
					[mapData.bounds.south, mapData.bounds.west],
					[mapData.bounds.north, mapData.bounds.east]
				);
				map.fitBounds(bounds, { padding: [50, 50] });
			} else {
				// Default to West Africa
				map.setView([12, 0], 5);
			}

			// Create markers layer
			markersLayer = L.layerGroup().addTo(map);

			// Add markers
			addMarkers();

			mapLoading = false;
		} catch (e) {
			console.error('Failed to initialize map:', e);
			mapLoading = false;
		}
	}

	function addMarkers() {
		if (!L || !map || !markersLayer || !mapData) return;

		markersLayer.clearLayers();

		// Create size scale
		const sizeScale = scaleSqrt()
			.domain([1, mapData.meta.maxCount])
			.range([8, 40]);

		const isDark = isDarkActive();
		const fillColor = isDark ? '#f97316' : '#ea580c';
		const strokeColor = isDark ? '#fed7aa' : '#9a3412';

		for (const location of mapData.locations) {
			const radius = sizeScale(location.count);

			const marker = L.circleMarker([location.lat, location.lng], {
				radius: radius,
				fillColor: fillColor,
				color: strokeColor,
				weight: 2,
				opacity: 0.9,
				fillOpacity: 0.6
			});

			// Create popup content
			const popupContent = createPopupContent(location);
			marker.bindPopup(popupContent, {
				maxWidth: 350,
				maxHeight: 400,
				className: 'provenance-popup'
			});

			marker.addTo(markersLayer);
		}
	}

	function createPopupContent(location: ProvenanceMapData['locations'][0]): string {
		const lang = languageStore.current;
		const linkHtml = location.o_id
			? `<a href="${getItemUrl(location.o_id)}" target="_blank" rel="noopener noreferrer" class="text-primary hover:underline inline-flex items-center gap-1">
				${location.name}
				<svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
					<polyline points="15 3 21 3 21 9"></polyline>
					<line x1="10" y1="14" x2="21" y2="3"></line>
				</svg>
			</a>`
			: location.name;

		const yearRange =
			location.earliestYear && location.latestYear
				? `${location.earliestYear}–${location.latestYear}`
				: '';

		let html = `
			<div class="provenance-popup-content">
				<h3 class="font-semibold text-base mb-2">${linkHtml}</h3>
				<div class="text-sm text-muted-foreground mb-2">
					<strong>${location.count}</strong> ${lang === 'fr' ? 'publication(s)' : 'publication(s)'}
					${yearRange ? `<span class="ml-2">(${yearRange})</span>` : ''}
				</div>
				<div class="max-h-48 overflow-y-auto">
					<ul class="space-y-1.5">
		`;

		for (const pub of location.publications.slice(0, 15)) {
			const authors = pub.authors.length > 0 ? pub.authors.join(', ') : '';
			html += `
				<li class="text-xs border-l-2 border-primary/30 pl-2">
					<div class="font-medium line-clamp-2">${pub.title || 'Untitled'}</div>
					${authors ? `<div class="text-muted-foreground">${authors}</div>` : ''}
					<div class="text-muted-foreground">${pub.type}${pub.year ? ` (${pub.year})` : ''}</div>
				</li>
			`;
		}

		if (location.publications.length > 15) {
			html += `<li class="text-xs text-muted-foreground italic">...${lang === 'fr' ? 'et' : 'and'} ${location.publications.length - 15} ${lang === 'fr' ? 'autres' : 'more'}</li>`;
		}

		html += `
					</ul>
				</div>
			</div>
		`;

		return html;
	}

	// Watch for theme changes
	$effect(() => {
		if (browser && map && L && mapData) {
			const isDark = isDarkActive();
			const tileOptions = isDark ? tileLayerOptions.dark : tileLayerOptions.light;

			// Update tile layer
			map.eachLayer((layer: L.Layer) => {
				if ((layer as L.TileLayer).setUrl) {
					(layer as L.TileLayer).setUrl(tileOptions.url);
				}
			});

			// Refresh markers with new colors
			addMarkers();
		}
	});

	onMount(() => {
		if (mapData) {
			initMap();
		}

		// Theme observer
		const observer = new MutationObserver(() => {
			if (map && L) {
				const isDark = isDarkActive();
				const tileOptions = isDark ? tileLayerOptions.dark : tileLayerOptions.light;

				map.eachLayer((layer: L.Layer) => {
					if ((layer as L.TileLayer).setUrl) {
						(layer as L.TileLayer).setUrl(tileOptions.url);
					}
				});

				addMarkers();
			}
		});

		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['class']
		});

		return () => {
			observer.disconnect();
			if (map) {
				map.remove();
			}
		};
	});
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
				<div class="relative h-[600px]" bind:this={mapElement}>
					{#if mapLoading}
						<div class="absolute inset-0 flex items-center justify-center bg-muted/50">
							<Skeleton class="h-full w-full" />
						</div>
					{/if}
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

<style>
	:global(.provenance-popup .leaflet-popup-content-wrapper) {
		border-radius: 0.5rem;
		padding: 0;
	}

	:global(.provenance-popup .leaflet-popup-content) {
		margin: 0.75rem;
		font-family: inherit;
	}

	:global(.provenance-popup-content) {
		font-size: 0.875rem;
	}

	:global(.dark .provenance-popup .leaflet-popup-content-wrapper) {
		background-color: hsl(var(--card));
		color: hsl(var(--card-foreground));
	}

	:global(.dark .provenance-popup .leaflet-popup-tip) {
		background-color: hsl(var(--card));
	}
</style>

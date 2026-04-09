<script lang="ts">
	import { fetchData } from '$lib/utils/dataFetcher.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { StatsCard } from '$lib/components/dashboard/index.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { SemanticMapCanvas } from '$lib/components/visualizations/semantic-map/index.js';
	import type {
		SemanticMapPoint,
		SemanticMapRawData,
		SemanticMapColumnar,
		SemanticMapIndex,
		ColorByOption,
		LegendEntry
	} from '$lib/types/semanticMap.js';
	import { buildColumnar, hydratePoint, computeColorIndices } from '$lib/types/semanticMap.js';
	import { ZoomIn, ZoomOut, Maximize2, ExternalLink } from '@lucide/svelte';

	// Data state
	let columnar = $state<SemanticMapColumnar | null>(null);
	let meta = $state<SemanticMapRawData['meta'] | null>(null);
	let countries = $state<string[]>([]);
	let topics = $state<{ id: number; label: string }[]>([]);
	let loading = $state(true);
	let loadingCountry = $state(false);
	let error = $state<string | null>(null);

	// Country filter
	let countryIndex = $state<SemanticMapIndex | null>(null);
	let selectedCountry = $state<string>('all'); // 'all' or country slug

	// View state
	let colorBy = $state<ColorByOption>('country');
	let highlightedGroup = $state<number | null>(null);
	let hoveredPoint = $state<SemanticMapPoint | null>(null);
	let tooltipX = $state(0);
	let tooltipY = $state(0);
	let selectedPoint = $state<SemanticMapPoint | null>(null);

	let canvasComponent: ReturnType<typeof SemanticMapCanvas> | undefined = $state();

	// ═══════════════════════════════════════════════════
	// Color palettes
	// ═══════════════════════════════════════════════════

	const COUNTRY_PALETTE = [
		'#4a9960',
		'#b8652a',
		'#c49a2e',
		'#c4b840',
		'#4a88b0',
		'#3a8060',
		'#888888'
	];
	const SENTIMENT_PALETTE = ['#22c55e', '#ef4444', '#94a3b8', '#666666'];
	const POLARITY_PALETTE = ['#15803d', '#22c55e', '#94a3b8', '#ef4444', '#991b1b', '#666666'];
	const CHART_PALETTE = [
		'#c47f35',
		'#3d72b0',
		'#3d9070',
		'#7d50c4',
		'#b0a030',
		'#c44040',
		'#3890a0',
		'#b050a0',
		'#60a040',
		'#a06040',
		'#5060c0',
		'#c08040',
		'#4090c0',
		'#a04070',
		'#70b060',
		'#806890',
		'#c0a060',
		'#5080a0',
		'#a08050',
		'#609060',
		'#8060b0',
		'#b07050',
		'#4070b0',
		'#908040',
		'#607090',
		'#b06080',
		'#50a080',
		'#a06090',
		'#7090a0',
		'#c06050'
	];

	const paletteForColorBy = $derived(
		colorBy === 'country'
			? COUNTRY_PALETTE
			: colorBy === 'sentiment'
				? SENTIMENT_PALETTE
				: colorBy === 'polarity'
					? POLARITY_PALETTE
					: CHART_PALETTE
	);

	// ═══════════════════════════════════════════════════
	// Derived: color indices + legend (typed array, no string ops)
	// ═══════════════════════════════════════════════════

	const colorResult = $derived.by(() => {
		if (!columnar) return null;
		const _ = languageStore.current; // for i18n legend labels
		return computeColorIndices(columnar, colorBy, paletteForColorBy);
	});

	// Polarity label → translation key mapping
	const POLARITY_KEY_MAP: Record<string, string> = {
		'Très positif': 'semantic_map.polarity_very_positive',
		Positif: 'semantic_map.polarity_positive',
		Neutre: 'semantic_map.polarity_neutral',
		Négatif: 'semantic_map.polarity_negative',
		'Très négatif': 'semantic_map.polarity_very_negative',
		'Non applicable': 'semantic_map.polarity_not_applicable'
	};

	const legendItems = $derived.by((): LegendEntry[] => {
		if (!colorResult) return [];
		const _ = languageStore.current;

		if (colorBy === 'sentiment') {
			return colorResult.legend.map((e) => ({
				...e,
				label: t(`semantic_map.sentiment_${e.label.toLowerCase()}`)
			}));
		}
		if (colorBy === 'polarity') {
			return colorResult.legend.map((e) => ({
				...e,
				label: t(POLARITY_KEY_MAP[e.label] || 'semantic_map.unknown')
			}));
		}
		return colorResult.legend;
	});

	// ═══════════════════════════════════════════════════
	// Color-by UI options
	// ═══════════════════════════════════════════════════

	const colorByOptions: { value: ColorByOption; labelKey: string }[] = [
		{ value: 'country', labelKey: 'semantic_map.color_country' },
		{ value: 'topic', labelKey: 'semantic_map.color_topic' },
		{ value: 'newspaper', labelKey: 'semantic_map.color_newspaper' },
		{ value: 'sentiment', labelKey: 'semantic_map.color_sentiment' },
		{ value: 'polarity', labelKey: 'semantic_map.color_polarity' },
		{ value: 'decade', labelKey: 'semantic_map.color_decade' }
	];

	// ═══════════════════════════════════════════════════
	// Data loading — two-phase: UI first, then typed arrays
	// ═══════════════════════════════════════════════════

	async function loadInitialData() {
		try {
			loading = true;
			error = null;

			// Load main data + country index in parallel
			const [raw, idx] = await Promise.all([
				fetchData<SemanticMapRawData>('semantic-map.json'),
				fetchData<SemanticMapIndex>('semantic-map/index.json').catch(() => null)
			]);

			// Parse country index if available
			if (idx) {
				countryIndex = idx;
			}

			// Phase 1: show stats immediately
			meta = raw.meta;
			countries = raw.c;
			topics = raw.t;
			loading = false;

			// Phase 2: build typed arrays after paint
			await new Promise((r) => requestAnimationFrame(r));
			columnar = buildColumnar(raw);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
			loading = false;
		}
	}

	async function loadCountryData(slug: string) {
		try {
			loadingCountry = true;
			selectedPoint = null;
			hoveredPoint = null;

			const raw = await fetchData<SemanticMapRawData>(`semantic-map/${slug}.json`, {
				cache: false
			});

			meta = raw.meta;
			// Keep original country/topic lists for UI
			await new Promise((r) => requestAnimationFrame(r));
			columnar = buildColumnar(raw);
			canvasComponent?.resetView();
		} catch (e) {
			error = e instanceof Error ? e.message : `Failed to load data for ${slug}`;
		} finally {
			loadingCountry = false;
		}
	}

	async function loadAllData() {
		try {
			loadingCountry = true;
			selectedPoint = null;
			hoveredPoint = null;

			const raw = await fetchData<SemanticMapRawData>('semantic-map.json');
			meta = raw.meta;

			await new Promise((r) => requestAnimationFrame(r));
			columnar = buildColumnar(raw);
			canvasComponent?.resetView();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
		} finally {
			loadingCountry = false;
		}
	}

	$effect(() => {
		loadInitialData();
	});

	function handleCountryChange(value: string | undefined) {
		if (!value || value === selectedCountry) return;
		selectedCountry = value;
		highlightedGroup = null;
		if (value === 'all') {
			loadAllData();
		} else {
			loadCountryData(value);
		}
	}

	// ═══════════════════════════════════════════════════
	// Event handlers — hydrate single point on demand
	// ═══════════════════════════════════════════════════

	function handlePointHover(index: number | null, x: number, y: number) {
		hoveredPoint = index !== null && columnar ? hydratePoint(columnar, index) : null;
		tooltipX = x;
		tooltipY = y;
	}

	function handlePointClick(index: number | null) {
		selectedPoint = index !== null && columnar ? hydratePoint(columnar, index) : null;
	}

	function handleColorByChange(value: string | undefined) {
		if (value) {
			colorBy = value as ColorByOption;
			highlightedGroup = null;
		}
	}

	function handleLegendHover(key: number | null) {
		highlightedGroup = key;
	}
</script>

<svelte:head>
	<title>{t('semantic_map.title')} | {t('app.title')}</title>
</svelte:head>

<div class="container mx-auto space-y-6 py-6">
	<div class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight text-foreground">{t('semantic_map.title')}</h1>
		<p class="text-muted-foreground">{t('semantic_map.description')}</p>
	</div>

	{#if loading}
		<div class="space-y-4">
			<div class="grid gap-4 md:grid-cols-4">
				{#each Array(4) as _, i (i)}
					<Skeleton class="h-24" />
				{/each}
			</div>
			<Skeleton class="h-150" />
		</div>
	{:else if error}
		<Card.Root class="p-6">
			<div class="py-12 text-center">
				<h3 class="mb-2 text-xl font-semibold text-destructive">{t('common.error')}</h3>
				<p class="text-muted-foreground">{error}</p>
				<p class="mt-4 text-sm text-muted-foreground">
					{t('semantic_map.run_script_hint')}
				</p>
			</div>
		</Card.Root>
	{:else if meta}
		<!-- Stats -->
		<div class="grid gap-4 md:grid-cols-4">
			<StatsCard
				title={t('semantic_map.total_articles')}
				value={columnar?.length ?? meta.totalRecords}
			/>
			<StatsCard title={t('semantic_map.countries')} value={countries.length} />
			<StatsCard title={t('semantic_map.topics')} value={topics.length} />
			<StatsCard title={t('semantic_map.embedding_dim')} value={`${meta.embeddingDim}D`} />
		</div>

		<!-- Controls -->
		<Card.Root>
			<Card.Content class="py-4">
				<div class="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center">
					<!-- Country filter -->
					{#if countryIndex && countryIndex.countries.length > 0}
						<div class="flex items-center gap-2">
							<Label class="text-sm font-medium whitespace-nowrap"
								>{t('semantic_map.filter_country')}:</Label
							>
							<Select.Root
								type="single"
								value={selectedCountry}
								onValueChange={handleCountryChange}
								disabled={loadingCountry}
							>
								<Select.Trigger class="w-48">
									{#if loadingCountry}
										{t('semantic_map.loading_country')}
									{:else if selectedCountry === 'all'}
										{t('semantic_map.all_countries')}
									{:else}
										{countryIndex.countries.find((c) => c.slug === selectedCountry)?.name ||
											selectedCountry}
									{/if}
								</Select.Trigger>
								<Select.Content>
									<Select.Item value="all">
										{t('semantic_map.all_countries')} ({countryIndex.total})
									</Select.Item>
									{#each countryIndex.countries as country (country.slug)}
										<Select.Item value={country.slug}>
											{country.name} ({country.count})
										</Select.Item>
									{/each}
								</Select.Content>
							</Select.Root>
						</div>
					{/if}

					<!-- Color by -->
					<div class="flex items-center gap-2">
						<Label class="text-sm font-medium whitespace-nowrap"
							>{t('semantic_map.color_by')}:</Label
						>
						<Select.Root type="single" value={colorBy} onValueChange={handleColorByChange}>
							<Select.Trigger class="w-48">
								{t(colorByOptions.find((o) => o.value === colorBy)?.labelKey || '')}
							</Select.Trigger>
							<Select.Content>
								{#each colorByOptions as option (option.value)}
									<Select.Item value={option.value}>{t(option.labelKey)}</Select.Item>
								{/each}
							</Select.Content>
						</Select.Root>
					</div>

					<div class="flex items-center gap-1 sm:ml-auto">
						<Button
							variant="outline"
							size="icon"
							onclick={() => canvasComponent?.zoomIn()}
							title={t('network.zoom_in')}
						>
							<ZoomIn class="h-4 w-4" />
						</Button>
						<Button
							variant="outline"
							size="icon"
							onclick={() => canvasComponent?.zoomOut()}
							title={t('network.zoom_out')}
						>
							<ZoomOut class="h-4 w-4" />
						</Button>
						<Button
							variant="outline"
							size="icon"
							onclick={() => canvasComponent?.resetView()}
							title={t('network.reset_view')}
						>
							<Maximize2 class="h-4 w-4" />
						</Button>
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Main visualization -->
		<Card.Root class="relative overflow-hidden">
			<div class="h-150">
				{#if columnar && colorResult}
					<SemanticMapCanvas
						bind:this={canvasComponent}
						positions={columnar.positions}
						pointCount={columnar.length}
						groupPerPoint={colorResult.groupPerPoint}
						palette={paletteForColorBy}
						{highlightedGroup}
						onPointHover={handlePointHover}
						onPointClick={handlePointClick}
					/>
				{:else}
					<div class="flex h-full items-center justify-center">
						<div class="text-muted-foreground">{t('common.loading')}...</div>
					</div>
				{/if}

				<!-- Legend overlay -->
				{#if legendItems.length > 0}
					<div
						class="absolute bottom-4 left-4 z-10 max-h-80 overflow-y-auto rounded-lg border bg-card/95 p-3 text-sm shadow-sm backdrop-blur-sm"
					>
						<div class="mb-2 font-medium">{t('network.legend')}</div>
						<div class="flex flex-col gap-1">
							{#each legendItems as item (item.key)}
								<button
									class="flex items-center gap-2 rounded px-1 py-0.5 text-left transition-opacity hover:bg-muted/50"
									class:opacity-40={highlightedGroup !== null && highlightedGroup !== item.key}
									onmouseenter={() => handleLegendHover(item.key)}
									onmouseleave={() => handleLegendHover(null)}
								>
									<div
										class="h-3 w-3 shrink-0 rounded-full"
										style="background-color: {item.color}"
									></div>
									<span class="truncate text-xs text-muted-foreground">{item.label}</span>
								</button>
							{/each}
						</div>
						{#if columnar}
							<div class="mt-2 border-t pt-2 text-xs text-muted-foreground">
								{t('semantic_map.total_points')}: {columnar.length}
							</div>
						{/if}
					</div>
				{/if}

				<!-- Selected article panel -->
				{#if selectedPoint}
					<div
						class="absolute top-4 right-4 z-20 w-72 rounded-lg border bg-card/95 p-4 shadow-lg backdrop-blur-sm lg:w-80"
					>
						<div class="mb-3 flex items-start justify-between gap-2">
							<h3 class="text-sm leading-tight font-semibold">{selectedPoint.title}</h3>
							<button
								class="shrink-0 rounded p-1 hover:bg-muted"
								onclick={() => (selectedPoint = null)}
							>
								<span class="sr-only">{t('topic_network.close')}</span>
								<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M6 18L18 6M6 6l12 12"
									/>
								</svg>
							</button>
						</div>
						<div class="space-y-2 text-sm">
							{#if selectedPoint.country}
								<div class="flex justify-between">
									<span class="text-muted-foreground">{t('topic_network.country')}</span>
									<span>{selectedPoint.country}</span>
								</div>
							{/if}
							{#if selectedPoint.newspaper}
								<div class="flex justify-between">
									<span class="text-muted-foreground">{t('topic_network.newspaper')}</span>
									<span class="text-right">{selectedPoint.newspaper}</span>
								</div>
							{/if}
							{#if selectedPoint.year}
								<div class="flex justify-between">
									<span class="text-muted-foreground">{t('topic_network.pub_date')}</span>
									<span>{selectedPoint.year}</span>
								</div>
							{/if}
							{#if selectedPoint.topicLabel}
								<div>
									<span class="text-muted-foreground">{t('semantic_map.topic')}</span>
									<div class="mt-1">
										<Badge variant="secondary" class="text-xs">{selectedPoint.topicLabel}</Badge>
									</div>
								</div>
							{/if}
							{#if selectedPoint.sentiment}
								<div class="flex justify-between">
									<span class="text-muted-foreground">{t('semantic_map.sentiment')}</span>
									<Badge
										variant={selectedPoint.sentiment === 'POSITIVE'
											? 'default'
											: selectedPoint.sentiment === 'NEGATIVE'
												? 'destructive'
												: 'secondary'}
										class="text-xs"
									>
										{t(`semantic_map.sentiment_${selectedPoint.sentiment.toLowerCase()}`)}
									</Badge>
								</div>
							{/if}
							{#if selectedPoint.polarity}
								<div class="flex justify-between">
									<span class="text-muted-foreground">{t('semantic_map.polarity')}</span>
									<span class="text-xs"
										>{t(POLARITY_KEY_MAP[selectedPoint.polarity] || 'semantic_map.unknown')}</span
									>
								</div>
							{/if}
						</div>
						{#if selectedPoint.id}
							<div class="mt-3 border-t pt-3">
								<a
									href="https://islam.zmo.de/s/westafrica/item/{selectedPoint.id}"
									target="_blank"
									rel="noopener noreferrer"
									class="inline-flex items-center gap-1 text-xs text-primary hover:underline"
								>
									{t('semantic_map.view_in_iwac')}
									<ExternalLink class="h-3 w-3" />
								</a>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</Card.Root>

		<!-- Tooltip -->
		{#if hoveredPoint && !selectedPoint}
			<div
				class="pointer-events-none fixed z-50 max-w-xs rounded-lg border bg-card p-3 text-sm shadow-lg"
				style="left: {tooltipX + 12}px; top: {tooltipY - 12}px; transform: translateY(-100%);"
			>
				<p class="leading-tight font-medium">{hoveredPoint.title}</p>
				<div class="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
					{#if hoveredPoint.country}
						<span>{hoveredPoint.country}</span>
					{/if}
					{#if hoveredPoint.newspaper}
						<span>{hoveredPoint.newspaper}</span>
					{/if}
					{#if hoveredPoint.year}
						<span>{hoveredPoint.year}</span>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Instructions -->
		<Card.Root>
			<Card.Content class="py-4">
				<p class="text-sm text-muted-foreground">
					<strong>{t('network.tip')}:</strong>
					{t('semantic_map.instructions')}
				</p>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

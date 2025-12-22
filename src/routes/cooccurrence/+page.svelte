<script lang="ts">
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import CooccurrenceMatrix from '$lib/components/charts/CooccurrenceMatrix.svelte';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import {
		FileText,
		Tags,
		Hash,
		Globe,
		MapPin,
		Download,
		Info
	} from '@lucide/svelte';

	// Use URL sync hook
	const urlSync = useUrlSync();

	// Data interfaces
	interface CooccurrenceData {
		terms: string[];
		matrix: number[][];
		term_counts: Record<string, number>;
		max_cooccurrence: number;
		total_articles?: number;
	}

	interface MetadataType {
		generated_at: string;
		total_articles: number;
		term_families: string[];
		term_families_count: number;
		window_size: number;
		countries: string[];
	}

	// State using Svelte 5 runes
	let globalData = $state<CooccurrenceData | null>(null);
	let countryData = $state<Record<string, CooccurrenceData>>({});
	let metadata = $state<MetadataType | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Filter states from URL
	const selectedCountry = $derived(urlSync.filters.country);
	const orderBy = $derived((urlSync.filters.order as 'name' | 'count' | 'cluster') || 'name');

	// Get active data based on filters
	const activeData = $derived.by((): CooccurrenceData | null => {
		if (selectedCountry && countryData[selectedCountry]) {
			return countryData[selectedCountry];
		}
		return globalData;
	});

	const availableCountries = $derived(metadata?.countries || []);

	async function loadData() {
		try {
			loading = true;
			error = null;

			const [globalResponse, countryResponse, metadataResponse] = await Promise.all([
				fetch(`${base}/data/cooccurrence-global.json`),
				fetch(`${base}/data/cooccurrence-countries.json`),
				fetch(`${base}/data/cooccurrence-metadata.json`)
			]);

			if (!globalResponse.ok) throw new Error('Failed to load global data');
			if (!countryResponse.ok) throw new Error('Failed to load country data');
			if (!metadataResponse.ok) throw new Error('Failed to load metadata');

			globalData = await globalResponse.json();
			countryData = await countryResponse.json();
			metadata = await metadataResponse.json();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load co-occurrence data';
			console.error('Error loading co-occurrence data:', err);
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		loadData();
	});

	function handleCountryChange(value: string | undefined) {
		if (value && value !== 'global') {
			urlSync.setFilter('country', value);
		} else {
			urlSync.clearFilter('country');
		}
	}

	function handleOrderChange(value: string | undefined) {
		if (value && value !== 'name') {
			urlSync.setFilter('order', value);
		} else {
			urlSync.clearFilter('order');
		}
	}

	function clearFilters() {
		urlSync.clearFilters();
	}

	const hasActiveFilters = $derived(selectedCountry || orderBy !== 'name');

	// Stats for the current view
	const stats = $derived.by(() => {
		if (!activeData) return { terms: 0, maxCooccurrence: 0, totalConnections: 0 };

		let totalConnections = 0;
		const n = activeData.terms.length;
		for (let i = 0; i < n; i++) {
			for (let j = i + 1; j < n; j++) {
				if (activeData.matrix[i][j] > 0) {
					totalConnections++;
				}
			}
		}

		return {
			terms: activeData.terms.length,
			maxCooccurrence: activeData.max_cooccurrence,
			totalConnections
		};
	});

	// Download SVG functionality
	function downloadSVG() {
		const svg = document.querySelector('.cooccurrence-matrix');
		if (!svg) return;

		const serializer = new XMLSerializer();
		const svgString = serializer.serializeToString(svg);
		const blob = new Blob([svgString], { type: 'image/svg+xml' });
		const url = URL.createObjectURL(blob);

		const link = document.createElement('a');
		link.href = url;
		link.download = `cooccurrence-matrix-${selectedCountry || 'global'}.svg`;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);
	}
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{t('cooccurrence.title')}</h2>
		<p class="text-muted-foreground">{t('cooccurrence.description')}</p>
	</div>

	{#if loading}
		<Card.Root class="p-6">
			<div class="space-y-4">
				<Skeleton class="h-8 w-64" />
				<Skeleton class="h-[500px] w-full" />
			</div>
		</Card.Root>
	{:else if error}
		<Card.Root class="p-6">
			<div class="py-12 text-center">
				<h3 class="mb-2 text-xl font-semibold text-destructive">{t('common.error')}</h3>
				<p class="text-muted-foreground">{error}</p>
				<Button variant="secondary" class="mt-4" onclick={() => loadData()}>
					{t('words.retry')}
				</Button>
			</div>
		</Card.Root>
	{:else if activeData}
		<!-- Explanation Card -->
		<Card.Root>
			<Card.Header class="pb-3">
				<div class="flex items-center gap-2">
					<Info class="h-5 w-5 text-muted-foreground" />
					<Card.Title class="text-base">{t('cooccurrence.how_it_works')}</Card.Title>
				</div>
			</Card.Header>
			<Card.Content>
				<p class="text-sm text-muted-foreground">
					{t('cooccurrence.explanation', [metadata?.window_size?.toString() || '50'])}
				</p>
			</Card.Content>
		</Card.Root>

		<!-- Filters -->
		<Card.Root>
			<Card.Header>
				<Card.Title>{t('filters.title')}</Card.Title>
				<Card.Description>{t('filters.description')}</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="flex flex-wrap items-center gap-4">
					<!-- Country Filter -->
					<div class="flex items-center gap-2">
						<label for="countrySelect" class="text-sm font-medium">{t('filters.country')}:</label>
						<Select.Root
							type="single"
							value={selectedCountry ?? 'global'}
							onValueChange={(v) => handleCountryChange(v === 'global' ? undefined : v)}
						>
							<Select.Trigger class="w-[200px]" id="countrySelect">
								{selectedCountry || t('cooccurrence.global')}
							</Select.Trigger>
							<Select.Content>
								<Select.Item value="global">{t('cooccurrence.global')}</Select.Item>
								{#each availableCountries as country (country)}
									<Select.Item value={country}>{country}</Select.Item>
								{/each}
							</Select.Content>
						</Select.Root>
					</div>

					<!-- Order By Filter -->
					<div class="flex items-center gap-2">
						<label for="orderSelect" class="text-sm font-medium">{t('cooccurrence.order_by')}:</label>
						<Select.Root
							type="single"
							value={orderBy}
							onValueChange={(v) => handleOrderChange(v)}
						>
							<Select.Trigger class="w-[150px]" id="orderSelect">
								{t(`cooccurrence.order_${orderBy}`)}
							</Select.Trigger>
							<Select.Content>
								<Select.Item value="name">{t('cooccurrence.order_name')}</Select.Item>
								<Select.Item value="count">{t('cooccurrence.order_count')}</Select.Item>
								<Select.Item value="cluster">{t('cooccurrence.order_cluster')}</Select.Item>
							</Select.Content>
						</Select.Root>
					</div>

					{#if hasActiveFilters}
						<Button variant="secondary" size="sm" onclick={clearFilters}>
							{t('filters.clear')}
						</Button>
					{/if}

					<!-- Download Button -->
					<div class="ml-auto">
						<Button variant="outline" size="sm" onclick={downloadSVG}>
							<Download class="mr-2 h-4 w-4" />
							{t('cooccurrence.download_svg')}
						</Button>
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Stats Cards -->
		<div class="grid gap-4 md:grid-cols-4">
			<Card.Root>
				<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
					<Card.Title class="text-sm font-medium text-muted-foreground">
						{t('cooccurrence.term_families')}
					</Card.Title>
					<Tags class="h-4 w-4 text-muted-foreground" />
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">{stats.terms}</div>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
					<Card.Title class="text-sm font-medium text-muted-foreground">
						{t('cooccurrence.connections')}
					</Card.Title>
					<Hash class="h-4 w-4 text-muted-foreground" />
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">{stats.totalConnections}</div>
					<p class="text-xs text-muted-foreground">{t('cooccurrence.term_pairs')}</p>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
					<Card.Title class="text-sm font-medium text-muted-foreground">
						{t('cooccurrence.max_cooccurrence')}
					</Card.Title>
					<Globe class="h-4 w-4 text-muted-foreground" />
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">{stats.maxCooccurrence.toLocaleString()}</div>
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
					<Card.Title class="text-sm font-medium text-muted-foreground">
						{t('cooccurrence.articles_analyzed')}
					</Card.Title>
					<FileText class="h-4 w-4 text-muted-foreground" />
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">
						{(activeData.total_articles || metadata?.total_articles || 0).toLocaleString()}
					</div>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Matrix Visualization -->
		<Card.Root class="p-6">
			<Card.Header>
				<Card.Title>
					{#if selectedCountry}
						{t('cooccurrence.matrix_title')} - {selectedCountry}
					{:else}
						{t('cooccurrence.matrix_title')}
					{/if}
				</Card.Title>
				<Card.Description>{t('cooccurrence.matrix_description')}</Card.Description>
			</Card.Header>
			<Card.Content>
				<CooccurrenceMatrix
					data={activeData}
					{orderBy}
					showDiagonal={false}
					cellSize={45}
				/>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

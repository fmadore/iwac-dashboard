<script lang="ts">
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import CooccurrenceMatrix from '$lib/components/charts/CooccurrenceMatrix.svelte';
	import WordAssociations from '$lib/components/charts/WordAssociations.svelte';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import {
		FileText,
		Tags,
		Hash,
		Globe,
		MapPin,
		Download,
		Info,
		Grid3X3,
		BookOpen
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

	interface WordData {
		word: string;
		count: number;
	}

	interface TermWordData {
		term: string;
		total_occurrences: number;
		articles_with_term: number;
		unique_words: number;
		max_word_count: number;
		words: WordData[];
	}

	interface MetadataType {
		generated_at: string;
		total_articles: number;
		term_families: string[];
		term_families_count: number;
		window_size: number;
		top_words_limit?: number;
		countries: string[];
	}

	// State using Svelte 5 runes
	let globalMatrixData = $state<CooccurrenceData | null>(null);
	let countryMatrixData = $state<Record<string, CooccurrenceData>>({});
	let globalWordData = $state<Record<string, TermWordData>>({});
	let countryWordData = $state<Record<string, Record<string, TermWordData>>>({});
	let metadata = $state<MetadataType | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// View mode: 'matrix' or 'words'
	type ViewMode = 'matrix' | 'words';
	const viewMode = $derived((urlSync.filters.view as ViewMode) || 'matrix');

	// Filter states from URL
	const selectedCountry = $derived(urlSync.filters.country);
	const orderBy = $derived((urlSync.filters.order as 'name' | 'count' | 'cluster') || 'name');
	const selectedTerm = $derived(urlSync.filters.term);

	// Get active matrix data based on filters
	const activeMatrixData = $derived.by((): CooccurrenceData | null => {
		if (selectedCountry && countryMatrixData[selectedCountry]) {
			return countryMatrixData[selectedCountry];
		}
		return globalMatrixData;
	});

	// Get active word data for selected term
	const activeWordData = $derived.by((): TermWordData | null => {
		if (!selectedTerm) return null;

		if (selectedCountry && countryWordData[selectedCountry]) {
			return countryWordData[selectedCountry][selectedTerm] || null;
		}
		return globalWordData[selectedTerm] || null;
	});

	// Available terms for word associations
	const availableTerms = $derived(metadata?.term_families || []);
	const availableCountries = $derived(metadata?.countries || []);

	async function loadData() {
		try {
			loading = true;
			error = null;

			const [matrixGlobalRes, matrixCountryRes, wordsGlobalRes, wordsCountryRes, metadataRes] =
				await Promise.all([
					fetch(`${base}/data/cooccurrence/matrix-global.json`),
					fetch(`${base}/data/cooccurrence/matrix-countries.json`),
					fetch(`${base}/data/cooccurrence/words-global.json`),
					fetch(`${base}/data/cooccurrence/words-countries.json`),
					fetch(`${base}/data/cooccurrence/metadata.json`)
				]);

			if (!matrixGlobalRes.ok) throw new Error('Failed to load matrix data');
			if (!metadataRes.ok) throw new Error('Failed to load metadata');

			globalMatrixData = await matrixGlobalRes.json();
			metadata = await metadataRes.json();

			if (matrixCountryRes.ok) {
				countryMatrixData = await matrixCountryRes.json();
			}

			if (wordsGlobalRes.ok) {
				globalWordData = await wordsGlobalRes.json();
			}

			if (wordsCountryRes.ok) {
				countryWordData = await wordsCountryRes.json();
			}
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

	function handleViewChange(value: string | undefined) {
		if (value === 'words') {
			urlSync.setFilter('view', value);
			// Auto-select first term if none selected
			if (!selectedTerm && availableTerms.length > 0) {
				urlSync.setFilter('term', availableTerms[0]);
			}
		} else {
			urlSync.clearFilter('view');
			urlSync.clearFilter('term');
		}
	}

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

	function handleTermChange(value: string | undefined) {
		if (value) {
			urlSync.setFilter('term', value);
		} else {
			urlSync.clearFilter('term');
		}
	}

	function clearFilters() {
		urlSync.clearFilters();
	}

	const hasActiveFilters = $derived(
		selectedCountry || orderBy !== 'name' || viewMode !== 'matrix' || selectedTerm
	);

	// Stats for the matrix view
	const matrixStats = $derived.by(() => {
		if (!activeMatrixData) return { terms: 0, maxCooccurrence: 0, totalConnections: 0 };

		let totalConnections = 0;
		const n = activeMatrixData.terms.length;
		for (let i = 0; i < n; i++) {
			for (let j = i + 1; j < n; j++) {
				if (activeMatrixData.matrix[i][j] > 0) {
					totalConnections++;
				}
			}
		}

		return {
			terms: activeMatrixData.terms.length,
			maxCooccurrence: activeMatrixData.max_cooccurrence,
			totalConnections
		};
	});

	// Stats for the word associations view
	const wordStats = $derived.by(() => {
		if (!activeWordData) return { totalOccurrences: 0, articlesWithTerm: 0, uniqueWords: 0 };

		return {
			totalOccurrences: activeWordData.total_occurrences,
			articlesWithTerm: activeWordData.articles_with_term,
			uniqueWords: activeWordData.unique_words
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
				<Skeleton class="h-125 w-full" />
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
	{:else}
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
					{#if viewMode === 'matrix'}
						{t('cooccurrence.explanation')}
					{:else}
						{t('cooccurrence.word_associations_explanation', [
							metadata?.window_size?.toString() || '50'
						])}
					{/if}
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
					<!-- View Mode Toggle -->
					<div class="flex items-center gap-2">
						<label for="viewSelect" class="text-sm font-medium"
							>{t('cooccurrence.view_mode')}:</label
						>
						<Select.Root type="single" value={viewMode} onValueChange={(v) => handleViewChange(v)}>
							<Select.Trigger class="w-45" id="viewSelect">
								<div class="flex items-center gap-2">
									{#if viewMode === 'matrix'}
										<Grid3X3 class="h-4 w-4" />
										{t('cooccurrence.view_matrix')}
									{:else}
										<BookOpen class="h-4 w-4" />
										{t('cooccurrence.view_words')}
									{/if}
								</div>
							</Select.Trigger>
							<Select.Content>
								<Select.Item value="matrix">
									<div class="flex items-center gap-2">
										<Grid3X3 class="h-4 w-4" />
										{t('cooccurrence.view_matrix')}
									</div>
								</Select.Item>
								<Select.Item value="words">
									<div class="flex items-center gap-2">
										<BookOpen class="h-4 w-4" />
										{t('cooccurrence.view_words')}
									</div>
								</Select.Item>
							</Select.Content>
						</Select.Root>
					</div>

					<!-- Term Selector (only for words view) -->
					{#if viewMode === 'words'}
						<div class="flex items-center gap-2">
							<label for="termSelect" class="text-sm font-medium"
								>{t('cooccurrence.select_term')}:</label
							>
							<Select.Root
								type="single"
								value={selectedTerm || ''}
								onValueChange={(v) => handleTermChange(v)}
							>
								<Select.Trigger class="w-45" id="termSelect">
									{selectedTerm || t('cooccurrence.select_term')}
								</Select.Trigger>
								<Select.Content>
									{#each availableTerms as term (term)}
										<Select.Item value={term}>{term}</Select.Item>
									{/each}
								</Select.Content>
							</Select.Root>
						</div>
					{/if}

					<!-- Country Filter -->
					<div class="flex items-center gap-2">
						<label for="countrySelect" class="text-sm font-medium">{t('filters.country')}:</label>
						<Select.Root
							type="single"
							value={selectedCountry ?? 'global'}
							onValueChange={(v) => handleCountryChange(v === 'global' ? undefined : v)}
						>
							<Select.Trigger class="w-50" id="countrySelect">
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

					<!-- Order By Filter (only for matrix view) -->
					{#if viewMode === 'matrix'}
						<div class="flex items-center gap-2">
							<label for="orderSelect" class="text-sm font-medium"
								>{t('cooccurrence.order_by')}:</label
							>
							<Select.Root
								type="single"
								value={orderBy}
								onValueChange={(v) => handleOrderChange(v)}
							>
								<Select.Trigger class="w-37.5" id="orderSelect">
									{t(`cooccurrence.order_${orderBy}`)}
								</Select.Trigger>
								<Select.Content>
									<Select.Item value="name">{t('cooccurrence.order_name')}</Select.Item>
									<Select.Item value="count">{t('cooccurrence.order_count')}</Select.Item>
									<Select.Item value="cluster">{t('cooccurrence.order_cluster')}</Select.Item>
								</Select.Content>
							</Select.Root>
						</div>
					{/if}

					{#if hasActiveFilters}
						<Button variant="secondary" size="sm" onclick={clearFilters}>
							{t('filters.clear')}
						</Button>
					{/if}

					<!-- Download Button (only for matrix view) -->
					{#if viewMode === 'matrix'}
						<div class="ml-auto">
							<Button variant="outline" size="sm" onclick={downloadSVG}>
								<Download class="mr-2 h-4 w-4" />
								{t('cooccurrence.download_svg')}
							</Button>
						</div>
					{/if}
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Stats Cards for Matrix View -->
		{#if viewMode === 'matrix' && activeMatrixData}
			<div class="grid gap-4 md:grid-cols-4">
				<Card.Root>
					<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
						<Card.Title class="text-sm font-medium text-muted-foreground">
							{t('cooccurrence.term_families')}
						</Card.Title>
						<Tags class="h-4 w-4 text-muted-foreground" />
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">{matrixStats.terms}</div>
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
						<div class="text-2xl font-bold">{matrixStats.totalConnections}</div>
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
						<div class="text-2xl font-bold">{matrixStats.maxCooccurrence.toLocaleString()}</div>
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
							{(activeMatrixData.total_articles || metadata?.total_articles || 0).toLocaleString()}
						</div>
					</Card.Content>
				</Card.Root>
			</div>
		{/if}

		<!-- Stats Cards for Words View -->
		{#if viewMode === 'words' && activeWordData}
			<div class="grid gap-4 md:grid-cols-4">
				<Card.Root>
					<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
						<Card.Title class="text-sm font-medium text-muted-foreground">
							{t('cooccurrence.total_word_occurrences')}
						</Card.Title>
						<Hash class="h-4 w-4 text-muted-foreground" />
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">{wordStats.totalOccurrences.toLocaleString()}</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
						<Card.Title class="text-sm font-medium text-muted-foreground">
							{t('cooccurrence.articles_with_term')}
						</Card.Title>
						<FileText class="h-4 w-4 text-muted-foreground" />
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">{wordStats.articlesWithTerm.toLocaleString()}</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
						<Card.Title class="text-sm font-medium text-muted-foreground">
							{t('cooccurrence.unique_words_found')}
						</Card.Title>
						<Tags class="h-4 w-4 text-muted-foreground" />
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">{wordStats.uniqueWords.toLocaleString()}</div>
					</Card.Content>
				</Card.Root>

				<Card.Root>
					<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
						<Card.Title class="text-sm font-medium text-muted-foreground">
							{t('cooccurrence.articles_analyzed')}
						</Card.Title>
						<Globe class="h-4 w-4 text-muted-foreground" />
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">
							{(metadata?.total_articles || 0).toLocaleString()}
						</div>
					</Card.Content>
				</Card.Root>
			</div>
		{/if}

		<!-- Matrix Visualization -->
		{#if viewMode === 'matrix' && activeMatrixData}
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
					{#key `${selectedCountry || 'global'}-${orderBy}`}
						<CooccurrenceMatrix
							data={activeMatrixData}
							{orderBy}
							showDiagonal={false}
							cellSize={45}
						/>
					{/key}
				</Card.Content>
			</Card.Root>
		{/if}

		<!-- Word Associations View -->
		{#if viewMode === 'words'}
			{#if activeWordData}
				<Card.Root>
					<Card.Header>
						<Card.Title>
							{t('cooccurrence.words_title')} "{selectedTerm}"
							{#if selectedCountry}
								- {selectedCountry}
							{/if}
						</Card.Title>
						<Card.Description>{t('cooccurrence.words_description')}</Card.Description>
					</Card.Header>
					<Card.Content>
						<WordAssociations data={activeWordData} maxDisplayed={50} />
					</Card.Content>
				</Card.Root>
			{:else if selectedTerm}
				<Card.Root class="p-6">
					<div class="py-12 text-center">
						<p class="text-muted-foreground">
							No word associations found for "{selectedTerm}"
							{#if selectedCountry}
								in {selectedCountry}
							{/if}
						</p>
					</div>
				</Card.Root>
			{:else}
				<Card.Root class="p-6">
					<div class="py-12 text-center">
						<p class="text-muted-foreground">{t('cooccurrence.select_term')}</p>
					</div>
				</Card.Root>
			{/if}
		{/if}
	{/if}
</div>

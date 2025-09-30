<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { Card } from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { t } from '$lib/stores/translationStore.js';
	import WordCloud from '$lib/components/wordcloud.svelte';

	// Data interfaces
	interface WordCloudData {
		data: [string, number][];
		total_articles: number;
		total_words: number;
		unique_words: number;
	}

	interface WordCloudMetadata {
		generated_at: string;
		total_articles: number;
		countries: string[];
		years: number[];
		language_filter: string;
		min_word_length: number;
		min_frequency: number;
	}

	// State using Svelte 5 runes
	let globalData = $state<WordCloudData | null>(null);
	let countryData = $state<Record<string, WordCloudData>>({});
	let temporalData = $state<Record<string, WordCloudData>>({});
	let metadata = $state<WordCloudMetadata | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Controls
	let viewMode = $state<'global' | 'country' | 'temporal'>('global');
	let selectedCountry = $state('');
	let selectedYear = $state('');

	// Computed values using $derived
	let currentData = $derived(
		viewMode === 'country' && selectedCountry && countryData[selectedCountry] 
			? countryData[selectedCountry].data 
			: viewMode === 'temporal' && selectedYear && temporalData[selectedYear]
			? temporalData[selectedYear].data
			: globalData?.data || []
	);
	
	let currentMetrics = $derived(
		viewMode === 'country' && selectedCountry && countryData[selectedCountry] 
			? countryData[selectedCountry]
			: viewMode === 'temporal' && selectedYear && temporalData[selectedYear]
			? temporalData[selectedYear]
			: globalData
	);
	
	let availableCountries = $derived(metadata?.countries || []);
	let availableYears = $derived(metadata?.years || []);

	function getCurrentData(): [string, number][] {
		switch (viewMode) {
			case 'country':
				return selectedCountry && countryData[selectedCountry] ? countryData[selectedCountry].data : [];
			case 'temporal':
				return selectedYear && temporalData[selectedYear] ? temporalData[selectedYear].data : [];
			default:
				return globalData ? globalData.data : [];
		}
	}

	function getCurrentMetrics() {
		switch (viewMode) {
			case 'country':
				return selectedCountry && countryData[selectedCountry] ? countryData[selectedCountry] : null;
			case 'temporal':
				return selectedYear && temporalData[selectedYear] ? temporalData[selectedYear] : null;
			default:
				return globalData;
		}
	}

	async function loadWordCloudData() {
		try {
			loading = true;
			error = null;

			// Load all data files
			const [globalResponse, countryResponse, temporalResponse, metadataResponse] = await Promise.all([
				fetch(`${base}/data/wordcloud-global.json`),
				fetch(`${base}/data/wordcloud-countries.json`),
				fetch(`${base}/data/wordcloud-temporal.json`),
				fetch(`${base}/data/wordcloud-metadata.json`)
			]);

			if (!globalResponse.ok) throw new Error('Failed to load global wordcloud data');
			if (!countryResponse.ok) throw new Error('Failed to load country wordcloud data');
			if (!temporalResponse.ok) throw new Error('Failed to load temporal wordcloud data');
			if (!metadataResponse.ok) throw new Error('Failed to load wordcloud metadata');

			globalData = await globalResponse.json();
			countryData = await countryResponse.json();
			temporalData = await temporalResponse.json();
			metadata = await metadataResponse.json();

			// Set default selections
			if (availableCountries.length > 0) {
				selectedCountry = availableCountries[0];
			}
			if (availableYears.length > 0) {
				selectedYear = String(availableYears[availableYears.length - 1]); // Most recent year
			}

		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load wordcloud data';
			console.error('Error loading wordcloud data:', err);
		} finally {
			loading = false;
		}
	}

	onMount(loadWordCloudData);
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{$t('nav.words')}</h2>
		<p class="text-muted-foreground">
			Explore word frequencies from French articles in the Islam West Africa Collection
		</p>
	</div>

	{#if loading}
		<Card class="p-6">
			<div class="text-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
				<p class="text-muted-foreground">Loading word cloud data...</p>
			</div>
		</Card>
	{:else if error}
		<Card class="p-6">
			<div class="text-center py-12">
				<p class="text-destructive mb-4">Error loading data: {error}</p>
				<Button onclick={loadWordCloudData}>Retry</Button>
			</div>
		</Card>
	{:else}
		<!-- Controls -->
		<Card class="p-6">
			<div class="flex flex-wrap gap-4 items-center">
				<div class="flex gap-2">
					<Button
						variant={viewMode === 'global' ? 'default' : 'outline'}
						size="sm"
						onclick={() => viewMode = 'global'}
					>
						Global
					</Button>
					<Button
						variant={viewMode === 'country' ? 'default' : 'outline'}
						size="sm"
						onclick={() => viewMode = 'country'}
					>
						By Country
					</Button>
					<Button
						variant={viewMode === 'temporal' ? 'default' : 'outline'}
						size="sm"
						onclick={() => viewMode = 'temporal'}
					>
						By Year
					</Button>
				</div>

				{#if viewMode === 'country' && availableCountries.length > 0}
					<Select.Root type="single" bind:value={selectedCountry}>
						<Select.Trigger class="w-48">
							{selectedCountry || 'Select country'}
						</Select.Trigger>
						<Select.Content>
							{#each availableCountries as country}
								<Select.Item value={country}>{country}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				{/if}

				{#if viewMode === 'temporal' && availableYears.length > 0}
					<Select.Root type="single" bind:value={selectedYear}>
						<Select.Trigger class="w-32">
							{selectedYear || 'Select year'}
						</Select.Trigger>
						<Select.Content>
							{#each availableYears as year}
								<Select.Item value={String(year)}>{year}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				{/if}
			</div>
		</Card>

		<!-- Metrics -->
		{#if currentMetrics}
			<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
				<Card class="p-4">
					<div class="text-2xl font-bold">{currentMetrics.total_articles.toLocaleString()}</div>
					<p class="text-xs text-muted-foreground">Articles</p>
				</Card>
				<Card class="p-4">
					<div class="text-2xl font-bold">{currentMetrics.total_words.toLocaleString()}</div>
					<p class="text-xs text-muted-foreground">Total Words</p>
				</Card>
				<Card class="p-4">
					<div class="text-2xl font-bold">{currentMetrics.unique_words.toLocaleString()}</div>
					<p class="text-xs text-muted-foreground">Unique Words</p>
				</Card>
				<Card class="p-4">
					<div class="text-2xl font-bold">{currentData.length}</div>
					<p class="text-xs text-muted-foreground">Displayed Words</p>
				</Card>
			</div>
		{/if}

		<!-- Word Cloud -->
		<Card class="p-6">
			<div class="space-y-4">
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-lg font-semibold">Word Cloud</h3>
						<p class="text-sm text-muted-foreground">
							{#if viewMode === 'global'}
								Overall word frequencies across all French articles
							{:else if viewMode === 'country'}
								Word frequencies for {selectedCountry}
							{:else if viewMode === 'temporal'}
								Word frequencies for {selectedYear}
							{/if}
						</p>
					</div>
					{#if metadata}
						<Badge variant="secondary">
							Updated: {new Date(metadata.generated_at).toLocaleDateString()}
						</Badge>
					{/if}
				</div>

				<div class="flex justify-center">
					<WordCloud
						data={currentData}
						width={800}
						height={400}
						backgroundColor="#ffffff"
						colorScheme="category10"
						fontFamily="Inter, sans-serif"
						minFontSize={12}
						maxFontSize={60}
						padding={1}
						hover={(word, event) => {
							// Add hover tooltip functionality here if needed
							console.log('Hovered word:', word);
						}}
						click={(word, event) => {
							// Add click functionality here if needed
							console.log('Clicked word:', word);
						}}
					/>
				</div>

				{#if currentData.length > 0}
					<div class="mt-6">
						<h4 class="text-sm font-medium mb-3">Top Words</h4>
						<div class="flex flex-wrap gap-2">
							{#each currentData.slice(0, 20) as [word, frequency]}
								<Badge variant="outline" class="text-xs">
									{word} ({frequency})
								</Badge>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</Card>

		<!-- Data Info -->
		{#if metadata}
			<Card class="p-6">
				<h3 class="text-lg font-semibold mb-4">Dataset Information</h3>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
					<div>
						<p><span class="font-medium">Language Filter:</span> {metadata.language_filter}</p>
						<p><span class="font-medium">Min Word Length:</span> {metadata.min_word_length} characters</p>
						<p><span class="font-medium">Min Frequency:</span> {metadata.min_frequency} occurrences</p>
					</div>
					<div>
						<p><span class="font-medium">Countries:</span> {metadata.countries.length}</p>
						<p><span class="font-medium">Years:</span> {metadata.years.length} ({Math.min(...metadata.years)}-{Math.max(...metadata.years)})</p>
						<p><span class="font-medium">Total Articles:</span> {metadata.total_articles.toLocaleString()}</p>
					</div>
				</div>
			</Card>
		{/if}
	{/if}
</div>
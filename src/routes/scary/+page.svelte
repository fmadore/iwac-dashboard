<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { browser } from '$app/environment';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import BarChartRace from '$lib/components/charts/BarChartRace.svelte';

	// Use URL sync hook
	const urlSync = useUrlSync();

	// Data interfaces
	interface TermData {
		year?: number;
		country?: string;
		data: [string, number][];
		total_articles?: number;
		total_occurrences?: number;
	}

	interface MetadataType {
		generated_at: string;
		total_articles: number;
		term_families: string[];
		term_families_count: number;
		total_variants: number;
		countries: string[];
		year_range: [number, number];
		term_definitions: Record<string, string[]>;
	}

	// State using Svelte 5 runes
	let temporalData = $state<Record<string, TermData>>({});
	let countryData = $state<Record<string, TermData>>({});
	let globalData = $state<TermData | null>(null);
	let metadata = $state<MetadataType | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Chart state
	let chartInstance: any = null;
	let isPlaying = $state(false);
	let currentYearIndex = $state(0);
	let height = 600;

	// Non-reactive references (bind:this doesn't need $state)
	let chartContainer = $state<HTMLDivElement | null>(null);
	let barChartRace = $state<any>(null);

	// Color management for consistent term colors
	const termColorMap = new Map<string, string>();
	const chartColors = [
		'--chart-1',
		'--chart-2',
		'--chart-3',
		'--chart-4',
		'--chart-5',
		'--chart-6',
		'--chart-7',
		'--chart-8',
		'--chart-9',
		'--chart-10',
		'--chart-11',
		'--chart-12',
		'--chart-13',
		'--chart-14',
		'--chart-15',
		'--chart-16'
	];

	// Canvas for parsing CSS colors
	const colorParsingCanvas = browser ? document.createElement('canvas') : null;
	const colorParsingContext = colorParsingCanvas?.getContext('2d', { willReadFrequently: false });

	function parseColor(value: string): string | null {
		if (!colorParsingContext) return null;
		try {
			colorParsingContext.fillStyle = '#000000';
			colorParsingContext.fillStyle = value;
			return colorParsingContext.fillStyle || null;
		} catch (error) {
			return null;
		}
	}

	function getCSSVariable(variable: string): string {
		if (!browser) return '#000000';
		const root = document.documentElement;
		const value = getComputedStyle(root).getPropertyValue(variable).trim();

		if (value) {
			const parsed = parseColor(value);
			if (parsed) {
				return parsed;
			}
		}

		const fallbackMap: Record<string, string> = {
			'--chart-1': '#e8590c',
			'--chart-2': '#2563eb',
			'--chart-3': '#16a34a',
			'--chart-4': '#f59e0b',
			'--chart-5': '#dc2626',
			'--foreground': '#09090b',
			'--muted-foreground': '#71717a',
			'--background': '#ffffff',
			'--popover': '#ffffff',
			'--popover-foreground': '#09090b',
			'--border': '#e4e4e7'
		};

		return fallbackMap[variable] || value || '#666666';
	}

	function getColorForTerm(term: string): string {
		if (termColorMap.has(term)) {
			return termColorMap.get(term)!;
		}

		const colorVar = chartColors[termColorMap.size % chartColors.length];
		const resolvedColor = getCSSVariable(colorVar);
		termColorMap.set(term, resolvedColor);

		return resolvedColor;
	}

	// Controls from URL
	const viewMode = $derived((urlSync.filters.view as 'race' | 'country' | 'global') || 'race');
	const selectedCountry = $derived(urlSync.filters.country);

	// Helper function to get correct French preposition for country names
	function getCountryPreposition(country: string | undefined): string {
		if (!country) return 'en';
		// Only Côte d'Ivoire uses "en", all others use "au"
		return country === "Côte d'Ivoire" ? 'en' : 'au';
	}

	// Get localized country title
	function getCountryChartTitle(country: string | undefined): string {
		if (!country) return t('scary.country_chart_title', ['']);

		if (languageStore.current === 'fr') {
			const prep = getCountryPreposition(country);
			return `Termes "inquiétants" ${prep} ${country}`;
		}

		return t('scary.country_chart_title', [country]);
	}

	// Computed values
	const availableYears = $derived(
		metadata?.year_range
			? Array.from(
					{ length: metadata.year_range[1] - metadata.year_range[0] + 1 },
					(_, i) => (metadata?.year_range?.[0] ?? 0) + i
				)
			: []
	);
	const availableCountries = $derived(metadata?.countries || []);

	async function loadScaryTermsData() {
		try {
			loading = true;
			error = null;

			// Load all data files
			const [temporalResponse, countryResponse, globalResponse, metadataResponse] =
				await Promise.all([
					fetch(`${base}/data/scary-terms-temporal.json`),
					fetch(`${base}/data/scary-terms-countries.json`),
					fetch(`${base}/data/scary-terms-global.json`),
					fetch(`${base}/data/scary-terms-metadata.json`)
				]);

			if (!temporalResponse.ok) throw new Error('Failed to load temporal data');
			if (!countryResponse.ok) throw new Error('Failed to load country data');
			if (!globalResponse.ok) throw new Error('Failed to load global data');
			if (!metadataResponse.ok) throw new Error('Failed to load metadata');

			temporalData = await temporalResponse.json();
			countryData = await countryResponse.json();
			globalData = await globalResponse.json();
			metadata = await metadataResponse.json();

			// Set default selections
			if (availableCountries.length > 0 && !urlSync.hasFilter('country')) {
				urlSync.setFilter('country', availableCountries[0]);
			}
			if (!urlSync.hasFilter('view')) {
				urlSync.setFilter('view', 'race');
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load scary terms data';
			console.error('Error loading scary terms data:', err);
		} finally {
			loading = false;
		}
	}

	async function initializeChart() {
		if (!browser || !chartContainer) return;

		try {
			// Dynamically import ECharts
			const echarts = await import('echarts');

			// Dispose existing chart if any
			if (chartInstance) {
				chartInstance.dispose();
			}

			// Initialize chart
			chartInstance = echarts.init(chartContainer);

			// Render based on view mode
			if (viewMode === 'race') {
				renderBarChartRace();
			} else if (viewMode === 'country' && selectedCountry) {
				renderCountryChart();
			} else if (viewMode === 'global') {
				renderGlobalChart();
			}

			// Handle window resize
			const handleResize = () => {
				if (chartInstance) {
					chartInstance.resize();
				}
			};
			window.addEventListener('resize', handleResize);

			return () => {
				window.removeEventListener('resize', handleResize);
				if (chartInstance) {
					chartInstance.dispose();
					chartInstance = null;
				}
			};
		} catch (err) {
			console.error('Error initializing chart:', err);
			error = 'Failed to initialize chart';
		}
	}

	function renderBarChartRace() {
		if (!chartInstance || availableYears.length === 0) return;

		const year = availableYears[currentYearIndex];
		const yearData = temporalData[String(year)];

		if (!yearData || !yearData.data || yearData.data.length === 0) {
			// No data for this year, skip
			return;
		}

		// Get top 10 terms for this year
		const topTerms = yearData.data.slice(0, 10);
		const terms = topTerms.map(([term]) => term);
		const values = topTerms.map(([, count]) => count);

		const option = {
			title: {
				text: `${t('scary.chart_title')} - ${year}`,
				left: 'center',
				textStyle: {
					color: 'var(--foreground)'
				}
			},
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'shadow'
				},
				backgroundColor: 'var(--popover)',
				borderColor: 'var(--border)',
				textStyle: {
					color: 'var(--popover-foreground)'
				}
			},
			grid: {
				left: '15%',
				right: '10%',
				bottom: '10%',
				top: '15%',
				containLabel: true
			},
			xAxis: {
				type: 'value',
				axisLine: {
					lineStyle: {
						color: 'var(--border)'
					}
				},
				axisLabel: {
					color: 'var(--foreground)'
				}
			},
			yAxis: {
				type: 'category',
				data: terms,
				inverse: true,
				axisLine: {
					lineStyle: {
						color: 'var(--border)'
					}
				},
				axisLabel: {
					color: 'var(--foreground)'
				}
			},
			series: [
				{
					type: 'bar',
					data: values,
					itemStyle: {
						color: 'var(--chart-1)'
					},
					label: {
						show: true,
						position: 'right',
						color: 'var(--foreground)'
					},
					animationDuration: 500,
					animationEasing: 'linear'
				}
			]
		};

		chartInstance.setOption(option, true);
	}

	function renderCountryChart() {
		if (!chartInstance || !selectedCountry || !countryData[selectedCountry]) return;

		const data = countryData[selectedCountry];
		const terms = data.data.map(([term]) => term);
		const values = data.data.map(([, count]) => count);

		// Resolve CSS variables
		const foregroundColor = getCSSVariable('--foreground');
		const borderColor = getCSSVariable('--border');
		const popoverBg = getCSSVariable('--popover');
		const popoverFg = getCSSVariable('--popover-foreground');

		// Create data array with individual colors
		const barData = data.data.map(([term, count]) => ({
			value: count,
			itemStyle: {
				color: getColorForTerm(term),
				borderRadius: [0, 4, 4, 0]
			}
		}));

		const option = {
			title: {
				text: getCountryChartTitle(selectedCountry),
				left: 'center',
				textStyle: {
					color: foregroundColor
				}
			},
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'shadow'
				},
				backgroundColor: popoverBg,
				borderColor: borderColor,
				textStyle: {
					color: popoverFg
				}
			},
			grid: {
				left: '15%',
				right: '10%',
				bottom: '10%',
				top: '15%',
				containLabel: true
			},
			xAxis: {
				type: 'value',
				axisLine: {
					lineStyle: {
						color: borderColor,
						opacity: 1
					}
				},
				axisLabel: {
					color: foregroundColor
				},
				splitLine: {
					lineStyle: {
						color: borderColor,
						opacity: 0.3
					}
				}
			},
			yAxis: {
				type: 'category',
				data: terms,
				inverse: true,
				axisLine: {
					lineStyle: {
						color: borderColor,
						opacity: 1
					}
				},
				axisLabel: {
					color: foregroundColor
				}
			},
			series: [
				{
					type: 'bar',
					data: barData,
					label: {
						show: true,
						position: 'right',
						color: foregroundColor,
						formatter: '{c}'
					},
					emphasis: {
						disabled: true
					}
				}
			]
		};

		chartInstance.setOption(option);
	}

	function renderGlobalChart() {
		if (!chartInstance || !globalData) return;

		const terms = globalData.data.map(([term]) => term);
		const values = globalData.data.map(([, count]) => count);

		// Resolve CSS variables
		const foregroundColor = getCSSVariable('--foreground');
		const borderColor = getCSSVariable('--border');
		const popoverBg = getCSSVariable('--popover');
		const popoverFg = getCSSVariable('--popover-foreground');

		// Create data array with individual colors
		const barData = globalData.data.map(([term, count]) => ({
			value: count,
			itemStyle: {
				color: getColorForTerm(term),
				borderRadius: [0, 4, 4, 0]
			}
		}));

		const option = {
			title: {
				text: t('scary.global_chart_title'),
				left: 'center',
				textStyle: {
					color: foregroundColor
				}
			},
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'shadow'
				},
				backgroundColor: popoverBg,
				borderColor: borderColor,
				textStyle: {
					color: popoverFg
				}
			},
			grid: {
				left: '15%',
				right: '10%',
				bottom: '10%',
				top: '15%',
				containLabel: true
			},
			xAxis: {
				type: 'value',
				axisLine: {
					lineStyle: {
						color: borderColor,
						opacity: 1
					}
				},
				axisLabel: {
					color: foregroundColor
				},
				splitLine: {
					lineStyle: {
						color: borderColor,
						opacity: 0.3
					}
				}
			},
			yAxis: {
				type: 'category',
				data: terms,
				inverse: true,
				axisLine: {
					lineStyle: {
						color: borderColor,
						opacity: 1
					}
				},
				axisLabel: {
					color: foregroundColor
				}
			},
			series: [
				{
					type: 'bar',
					data: barData,
					label: {
						show: true,
						position: 'right',
						color: foregroundColor,
						formatter: '{c}'
					},
					emphasis: {
						disabled: true
					}
				}
			]
		};

		chartInstance.setOption(option);
	}

	function play() {
		if (barChartRace && viewMode === 'race') {
			barChartRace.play();
			isPlaying = true;
		}
	}

	function pause() {
		if (barChartRace) {
			barChartRace.pause();
			isPlaying = false;
		}
	}

	function reset() {
		if (barChartRace) {
			barChartRace.reset();
			isPlaying = false;
		}
	}

	function handleViewModeChange(value: string | undefined) {
		pause();
		urlSync.setFilter('view', value || 'race');
	}

	function handleCountryChange(value: string | undefined) {
		if (value && value !== 'select-country') {
			urlSync.setFilter('country', value);
		}
	}

	// Effects
	$effect(() => {
		loadScaryTermsData();
	});

	$effect(() => {
		// Re-initialize chart when view mode, country, language, or data changes
		const _ = viewMode;
		const _country = selectedCountry;
		const _lang = languageStore.current;
		const _data = temporalData;

		// Only initialize for non-race views
		if (!loading && chartContainer && viewMode !== 'race') {
			initializeChart();
		}
	});

	// Cleanup on unmount
	onMount(() => {
		return () => {
			pause();
			if (chartInstance) {
				chartInstance.dispose();
			}
		};
	});

	// Computed chart title based on language
	const raceChartTitle = $derived(() => {
		const _ = languageStore.current; // Track language changes
		return t('scary.chart_title') + ' - {0}';
	});
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{t('scary.title')}</h2>
		<p class="text-muted-foreground">
			{t('scary.description')}
		</p>
	</div>

	{#if loading}
		<Card.Root class="p-6">
			<div class="py-12 text-center">
				<div class="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
				<p class="text-muted-foreground">{t('common.loading')}</p>
			</div>
		</Card.Root>
	{:else if error}
		<Card.Root class="p-6">
			<div class="py-12 text-center">
				<p class="mb-4 text-destructive">{t('common.error')}: {error}</p>
				<Button onclick={loadScaryTermsData}>{t('words.retry')}</Button>
			</div>
		</Card.Root>
	{:else}
		<!-- Controls -->
		<Card.Root class="p-6">
			<div class="flex flex-wrap items-center gap-4">
				<div class="flex gap-2">
					<Button
						variant={viewMode === 'race' ? 'default' : 'outline'}
						size="sm"
						onclick={() => handleViewModeChange('race')}
					>
						{t('scary.bar_race')}
					</Button>
					<Button
						variant={viewMode === 'country' ? 'default' : 'outline'}
						size="sm"
						onclick={() => handleViewModeChange('country')}
					>
						{t('scary.by_country')}
					</Button>
					<Button
						variant={viewMode === 'global' ? 'default' : 'outline'}
						size="sm"
						onclick={() => handleViewModeChange('global')}
					>
						{t('scary.global')}
					</Button>
				</div>

				{#if viewMode === 'country' && availableCountries.length > 0}
					<Select.Root
						type="single"
						value={selectedCountry ?? 'select-country'}
						onValueChange={handleCountryChange}
					>
						<Select.Trigger class="w-48">
							{selectedCountry || t('words.select_country')}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="select-country">{t('words.select_country')}</Select.Item>
							{#each availableCountries as country}
								<Select.Item value={country}>{country}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				{/if}

				{#if viewMode === 'race'}
					<div class="ml-auto flex gap-2">
						<Button variant="outline" size="sm" onclick={play} disabled={isPlaying}>
							{t('scary.play')}
						</Button>
						<Button variant="outline" size="sm" onclick={pause} disabled={!isPlaying}>
							{t('scary.pause')}
						</Button>
						<Button variant="outline" size="sm" onclick={reset}>
							{t('scary.reset')}
						</Button>
					</div>
				{/if}
			</div>
		</Card.Root>

		<!-- Metrics -->
		{#if metadata}
			<div class="grid grid-cols-1 gap-4 md:grid-cols-4">
				<Card.Root class="p-4">
					<div class="text-2xl font-bold">{metadata.total_articles.toLocaleString()}</div>
					<p class="text-xs text-muted-foreground">{t('scary.total_articles')}</p>
				</Card.Root>
				<Card.Root class="p-4">
					<div class="text-2xl font-bold">{metadata.term_families_count}</div>
					<p class="text-xs text-muted-foreground">{t('scary.term_families')}</p>
				</Card.Root>
				<Card.Root class="p-4">
					<div class="text-2xl font-bold">{metadata.total_variants}</div>
					<p class="text-xs text-muted-foreground">{t('scary.term_variants')}</p>
				</Card.Root>
				<Card.Root class="p-4">
					<div class="text-2xl font-bold">
						{(globalData?.total_occurrences ?? 0).toLocaleString()}
					</div>
					<p class="text-xs text-muted-foreground">{t('scary.total_occurrences')}</p>
				</Card.Root>
			</div>
		{/if}

		<!-- Chart -->
		<Card.Root class="p-6">
			<div class="space-y-4">
				<div>
					<h3 class="text-lg font-semibold">
						{#if viewMode === 'race'}
							{t('scary.chart_title')}
						{:else if viewMode === 'country'}
							{getCountryChartTitle(selectedCountry)}
						{:else}
							{t('scary.global_chart_title')}
						{/if}
					</h3>
					<p class="text-sm text-muted-foreground">
						{#if viewMode === 'race'}
							{t('scary.chart_description')}
						{:else if viewMode === 'country'}
							{t('scary.country_chart_description')}
						{:else}
							{t('scary.global_chart_description')}
						{/if}
					</p>
				</div>

				{#if viewMode === 'race'}
					<BarChartRace
						bind:this={barChartRace}
						data={temporalData}
						periods={availableYears}
						title={raceChartTitle()}
						maxBars={10}
						{height}
						useMultipleColors={true}
						cumulative={true}
						bind:currentIndex={currentYearIndex}
						onPeriodChange={(index, period) => {
							console.log(`Period changed to: ${period}`);
						}}
						onComplete={() => {
							isPlaying = false;
						}}
					/>
				{:else}
					<div bind:this={chartContainer} class="w-full" style="height: 600px;"></div>
				{/if}
			</div>
		</Card.Root>

		<!-- Term Definitions -->
		{#if metadata}
			<Card.Root class="p-6">
				<h3 class="mb-4 text-lg font-semibold">{t('scary.term_definitions')}</h3>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					{#each Object.entries(metadata.term_definitions) as [family, variants]}
						<div class="rounded-lg border border-border p-4">
							<h4 class="mb-2 font-medium">{family}</h4>
							<div class="flex flex-wrap gap-1">
								{#each variants as variant}
									<Badge variant="outline" class="text-xs">{variant}</Badge>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			</Card.Root>
		{/if}
	{/if}
</div>

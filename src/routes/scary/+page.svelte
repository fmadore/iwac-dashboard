<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { browser } from '$app/environment';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Slider } from '$lib/components/ui/slider/index.js';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { useUrlSync } from '$lib/hooks/useUrlSync.svelte.js';
	import { BarChartRace } from '$lib/components/visualizations/charts/d3/index.js';
	import {
		FileText,
		Tags,
		Hash,
		TrendingUp,
		Play,
		Pause,
		RotateCcw,
		SkipBack,
		SkipForward,
		BarChart3,
		Globe,
		MapPin
	} from '@lucide/svelte';

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

	// Track if initial data has been loaded
	let dataLoaded = $state(false);

	// Load data on mount (not in $effect to avoid infinite loop)
	onMount(() => {
		loadScaryTermsData()
			.then(() => {
				dataLoaded = true;
			})
			.catch((err) => {
				console.error('Failed to load scary terms data in onMount:', err);
				error = err instanceof Error ? err.message : 'Failed to load data';
				loading = false;
			});

		return () => {
			pause();
			if (chartInstance) {
				chartInstance.dispose();
			}
		};
	});

	$effect(() => {
		// Re-initialize chart when view mode, country, language, or data changes
		// Only run after initial data has loaded
		if (!dataLoaded) return;

		const _ = viewMode;
		const _country = selectedCountry;
		const _lang = languageStore.current;
		const _data = temporalData;

		// Only initialize for non-race views
		if (!loading && chartContainer && viewMode !== 'race') {
			initializeChart();
		}
	});

	// Computed chart title based on language
	const raceChartTitle = $derived(() => {
		const _ = languageStore.current; // Track language changes
		return t('scary.chart_title') + ' - {0}';
	});

	// Get the current year being displayed
	const currentYear = $derived(availableYears[currentYearIndex] ?? 0);

	// Calculate progress percentage
	const progressPercent = $derived(
		availableYears.length > 1 ? (currentYearIndex / (availableYears.length - 1)) * 100 : 0
	);

	// Get top term for current view
	const topTerm = $derived(() => {
		if (viewMode === 'race' && temporalData[String(currentYear)]) {
			return temporalData[String(currentYear)]?.data[0]?.[0] ?? null;
		} else if (viewMode === 'country' && selectedCountry && countryData[selectedCountry]) {
			return countryData[selectedCountry]?.data[0]?.[0] ?? null;
		} else if (viewMode === 'global' && globalData) {
			return globalData.data[0]?.[0] ?? null;
		}
		return null;
	});

	// Handle year slider change (single value slider returns number, not array)
	function handleYearChange(value: number) {
		if (availableYears.length > 0) {
			pause();
			const yearIndex = availableYears.indexOf(value);
			if (yearIndex >= 0) {
				currentYearIndex = yearIndex;
			}
		}
	}

	// Step navigation
	function stepForward() {
		if (currentYearIndex < availableYears.length - 1) {
			pause();
			currentYearIndex++;
		}
	}

	function stepBackward() {
		if (currentYearIndex > 0) {
			pause();
			currentYearIndex--;
		}
	}
</script>

<div class="space-y-6">
	<!-- Header -->
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
		<!-- Metrics Cards -->
		{#if metadata}
			<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
				<Card.Root class="relative overflow-hidden">
					<Card.Content class="p-6">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-sm font-medium text-muted-foreground">{t('scary.total_articles')}</p>
								<p class="text-2xl font-bold">{metadata.total_articles.toLocaleString()}</p>
							</div>
							<div class="rounded-full bg-primary/10 p-3">
								<FileText class="h-5 w-5 text-primary" />
							</div>
						</div>
					</Card.Content>
				</Card.Root>

				<Card.Root class="relative overflow-hidden">
					<Card.Content class="p-6">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-sm font-medium text-muted-foreground">{t('scary.term_families')}</p>
								<p class="text-2xl font-bold">{metadata.term_families_count}</p>
							</div>
							<div class="rounded-full bg-chart-2/10 p-3">
								<Tags class="h-5 w-5 text-chart-2" />
							</div>
						</div>
					</Card.Content>
				</Card.Root>

				<Card.Root class="relative overflow-hidden">
					<Card.Content class="p-6">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-sm font-medium text-muted-foreground">{t('scary.term_variants')}</p>
								<p class="text-2xl font-bold">{metadata.total_variants}</p>
							</div>
							<div class="rounded-full bg-chart-3/10 p-3">
								<Hash class="h-5 w-5 text-chart-3" />
							</div>
						</div>
					</Card.Content>
				</Card.Root>

				<Card.Root class="relative overflow-hidden">
					<Card.Content class="p-6">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-sm font-medium text-muted-foreground">
									{t('scary.total_occurrences')}
								</p>
								<p class="text-2xl font-bold">
									{(globalData?.total_occurrences ?? 0).toLocaleString()}
								</p>
							</div>
							<div class="rounded-full bg-chart-4/10 p-3">
								<TrendingUp class="h-5 w-5 text-chart-4" />
							</div>
						</div>
					</Card.Content>
				</Card.Root>
			</div>
		{/if}

		<!-- Controls Panel -->
		<Card.Root>
			<Card.Content class="p-4">
				<div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
					<!-- View Mode Toggle -->
					<div class="flex flex-wrap items-center gap-2">
						<span class="mr-2 text-sm font-medium text-muted-foreground"
							>{t('scary.view_mode')}:</span
						>
						<div class="inline-flex rounded-lg border border-border bg-muted/30 p-1">
							<Button
								variant={viewMode === 'race' ? 'default' : 'ghost'}
								size="sm"
								class="gap-2"
								onclick={() => handleViewModeChange('race')}
							>
								<BarChart3 class="h-4 w-4" />
								<span class="hidden sm:inline">{t('scary.bar_race')}</span>
							</Button>
							<Button
								variant={viewMode === 'country' ? 'default' : 'ghost'}
								size="sm"
								class="gap-2"
								onclick={() => handleViewModeChange('country')}
							>
								<MapPin class="h-4 w-4" />
								<span class="hidden sm:inline">{t('scary.by_country')}</span>
							</Button>
							<Button
								variant={viewMode === 'global' ? 'default' : 'ghost'}
								size="sm"
								class="gap-2"
								onclick={() => handleViewModeChange('global')}
							>
								<Globe class="h-4 w-4" />
								<span class="hidden sm:inline">{t('scary.global')}</span>
							</Button>
						</div>
					</div>

					<!-- Country Selector (for country view) -->
					{#if viewMode === 'country' && availableCountries.length > 0}
						<div class="flex items-center gap-2">
							<label for="country-select" class="text-sm font-medium text-muted-foreground">
								{t('filters.country')}:
							</label>
							<Select.Root
								type="single"
								value={selectedCountry ?? 'select-country'}
								onValueChange={handleCountryChange}
							>
								<Select.Trigger class="w-48" id="country-select">
									{selectedCountry || t('words.select_country')}
								</Select.Trigger>
								<Select.Content>
									{#each availableCountries as country}
										<Select.Item value={country}>{country}</Select.Item>
									{/each}
								</Select.Content>
							</Select.Root>
						</div>
					{/if}

					<!-- Playback Controls (for race view) -->
					{#if viewMode === 'race'}
						<div class="flex items-center gap-2">
							<Button
								variant="outline"
								size="icon"
								onclick={stepBackward}
								disabled={currentYearIndex === 0}
								title={t('scary.previous')}
							>
								<SkipBack class="h-4 w-4" />
							</Button>
							{#if isPlaying}
								<Button variant="default" size="icon" onclick={pause} title={t('scary.pause')}>
									<Pause class="h-4 w-4" />
								</Button>
							{:else}
								<Button
									variant="default"
									size="icon"
									onclick={play}
									disabled={currentYearIndex >= availableYears.length - 1}
									title={t('scary.play')}
								>
									<Play class="h-4 w-4" />
								</Button>
							{/if}
							<Button
								variant="outline"
								size="icon"
								onclick={stepForward}
								disabled={currentYearIndex >= availableYears.length - 1}
								title={t('scary.next')}
							>
								<SkipForward class="h-4 w-4" />
							</Button>
							<Button variant="outline" size="icon" onclick={reset} title={t('scary.reset')}>
								<RotateCcw class="h-4 w-4" />
							</Button>
							<span class="ml-2 min-w-16 text-center text-lg font-bold text-primary tabular-nums">
								{currentYear}
							</span>
						</div>
					{/if}
				</div>

				<!-- Year Slider (for race view) -->
				{#if viewMode === 'race' && metadata}
					<div class="mt-4 space-y-2">
						<div class="flex items-center justify-between text-xs text-muted-foreground">
							<span>{metadata.year_range[0]}</span>
							<span>{metadata.year_range[1]}</span>
						</div>
						<Slider
							type="single"
							value={currentYear}
							onValueChange={handleYearChange}
							min={metadata.year_range[0]}
							max={metadata.year_range[1]}
							step={1}
							class="w-full"
						/>
					</div>
				{/if}
			</Card.Content>
		</Card.Root>

		<!-- Chart -->
		<Card.Root>
			<Card.Header class="pb-2">
				<div class="flex items-start justify-between">
					<div>
						<Card.Title class="text-lg">
							{#if viewMode === 'race'}
								{t('scary.chart_title')}
							{:else if viewMode === 'country'}
								{getCountryChartTitle(selectedCountry)}
							{:else}
								{t('scary.global_chart_title')}
							{/if}
						</Card.Title>
						<Card.Description>
							{#if viewMode === 'race'}
								{t('scary.chart_description')}
							{:else if viewMode === 'country'}
								{t('scary.country_chart_description')}
							{:else}
								{t('scary.global_chart_description')}
							{/if}
						</Card.Description>
					</div>
					{#if topTerm()}
						<Badge variant="secondary" class="text-sm">
							{t('scary.top_term')}: <span class="ml-1 font-semibold">{topTerm()}</span>
						</Badge>
					{/if}
				</div>
			</Card.Header>
			<Card.Content>
				{#if viewMode === 'race'}
					<BarChartRace
						bind:this={barChartRace}
						data={temporalData}
						periods={availableYears}
						title={raceChartTitle()}
						maxBars={12}
						{height}
						useMultipleColors={true}
						cumulative={true}
						allTerms={metadata?.term_families || []}
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
			</Card.Content>
		</Card.Root>

		<!-- Term Definitions -->
		{#if metadata}
			<Card.Root>
				<Card.Header>
					<Card.Title class="flex items-center gap-2">
						<Tags class="h-5 w-5" />
						{t('scary.term_definitions')}
					</Card.Title>
					<Card.Description>{t('scary.term_definitions_desc')}</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
						{#each Object.entries(metadata.term_definitions) as [family, variants]}
							<div
								class="group rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent/50"
							>
								<h4 class="mb-2 font-semibold text-foreground capitalize">{family}</h4>
								<div class="flex flex-wrap gap-1.5">
									{#each variants as variant}
										<Badge variant="outline" class="text-xs font-normal">{variant}</Badge>
									{/each}
								</div>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		{/if}
	{/if}
</div>

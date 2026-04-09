<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { browser } from '$app/environment';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { useResizeObserver } from '$lib/hooks/index.js';

	interface Props {
		data?: [string, number][];
		backgroundColor?: string;
		fontFamily?: string;
		colorScheme?:
			| 'category10'
			| 'set3'
			| 'dark2'
			| 'accent'
			| 'pastel1'
			| 'pastel2'
			| 'set1'
			| 'set2'
			| 'tableau10';
		minRotation?: number;
		maxRotation?: number;
		minFontSize?: number;
		maxFontSize?: number;
		padding?: number;
		hover?: ((word: Word, event: Event) => void) | null;
		click?: ((word: Word, event: Event) => void) | null;
	}

	const {
		data = [],
		backgroundColor = 'transparent',
		fontFamily = 'Inter, sans-serif',
		colorScheme = 'category10',
		minRotation = -45,
		maxRotation = 45,
		minFontSize = 12,
		maxFontSize = 60,
		padding = 5,
		hover = null,
		click = null
	}: Props = $props();

	let containerElement: HTMLDivElement;
	let svgElement: SVGSVGElement;
	let d3: typeof import('d3-selection') | undefined;
	let colorScale: string[];
	let isRendering = $state(false);
	const containerSize = useResizeObserver(() => containerElement);
	const containerWidth = $derived(containerSize.width || 800);
	const containerHeight = $derived(containerSize.height || 400);

	onMount(() => {
		if (!browser) {
			return;
		}

		let active = true;

		const initialise = async () => {
			try {
				// Import d3-selection, d3-scale-chromatic, and d3-transition
				const [d3Module, chromatic, _transition] = await Promise.all([
					import('d3-selection'),
					import('d3-scale-chromatic'),
					import('d3-transition')
				]);

				if (!active) return;

				d3 = d3Module;
				colorScale = getColorScale(chromatic);

				// Load d3-cloud library
				await loadD3Cloud();

				if (!active) return;

				// Initial render
				renderWordCloud();
			} catch (error) {
				console.error('Failed to load d3 libraries:', error);
			}
		};

		initialise();

		// Cleanup on unmount
		return () => {
			active = false;
		};
	});

	// Type-safe access to the d3 global used by d3-cloud
	interface D3CloudGlobal {
		d3?: { layout?: { cloud?: (...args: unknown[]) => D3CloudLayout } };
	}

	interface D3CloudLayout {
		size: (size: [number, number]) => D3CloudLayout;
		words: (words: Word[]) => D3CloudLayout;
		padding: (padding: number) => D3CloudLayout;
		rotate: (fn: () => number) => D3CloudLayout;
		font: (font: string) => D3CloudLayout;
		fontSize: (fn: (d: Word) => number) => D3CloudLayout;
		on: (event: string, fn: (words: Word[]) => void) => D3CloudLayout;
		start: () => void;
	}

	function getD3CloudGlobal(): D3CloudGlobal {
		return window as unknown as D3CloudGlobal;
	}

	async function loadD3Cloud() {
		try {
			// Try to import d3-cloud and use it to set up the global d3.layout.cloud
			const cloudModule = await import('d3-cloud');

			// Ensure global d3 object exists
			if (typeof window !== 'undefined') {
				const g = getD3CloudGlobal();
				g.d3 = g.d3 || {};
				g.d3.layout = g.d3.layout || {};
				g.d3.layout.cloud = cloudModule.default || cloudModule;
			}
		} catch (error) {
			console.error('Failed to load d3-cloud:', error);
			// Try loading from CDN as fallback
			await loadD3CloudFromCDN();
		}
	}

	async function loadD3CloudFromCDN() {
		return new Promise((resolve, reject) => {
			const script = document.createElement('script');
			script.src = 'https://cdn.jsdelivr.net/gh/jasondavies/d3-cloud/build/d3.layout.cloud.js';
			script.onload = () => resolve(undefined);
			script.onerror = () => reject(new Error('Failed to load d3-cloud from CDN'));
			document.head.appendChild(script);
		});
	}

	function getColorScale(chromatic: typeof import('d3-scale-chromatic')): string[] {
		const schemes: Record<string, readonly string[]> = {
			category10: chromatic.schemeCategory10,
			set3: chromatic.schemeSet3,
			dark2: chromatic.schemeDark2,
			accent: chromatic.schemeAccent,
			pastel1: chromatic.schemePastel1,
			pastel2: chromatic.schemePastel2,
			set1: chromatic.schemeSet1,
			set2: chromatic.schemeSet2,
			tableau10: chromatic.schemeTableau10
		};
		return [...(schemes[colorScheme] || schemes.category10)];
	}

	function prepareWords(): Word[] {
		if (!data || data.length === 0) return [];

		// Calculate font size scale
		const maxWeight = Math.max(...data.map(([, weight]) => weight));
		const minWeight = Math.min(...data.map(([, weight]) => weight));
		const weightRange = maxWeight - minWeight || 1;

		return data.map(([text, weight], index) => ({
			text,
			size: minFontSize + ((weight - minWeight) / weightRange) * (maxFontSize - minFontSize),
			color: colorScale[index % colorScale.length]
		}));
	}

	function renderWordCloud() {
		if (!svgElement || !d3 || !data || data.length === 0) return;

		isRendering = true;

		// Clear previous content
		d3.select(svgElement).selectAll('*').remove();

		// Prepare word data
		const wordData = prepareWords();

		// Check if d3.layout.cloud is available
		const cloudLayout = getD3CloudGlobal().d3?.layout?.cloud;
		if (!cloudLayout) {
			console.error('d3.layout.cloud not available');
			isRendering = false;
			return;
		}

		// Create cloud layout using the correct d3.layout.cloud API with current container size
		const layout = cloudLayout()
			.size([containerWidth, containerHeight])
			.words(wordData)
			.padding(padding)
			.rotate(() => Math.random() * (maxRotation - minRotation) + minRotation)
			.font(fontFamily)
			.fontSize((d: Word) => d.size)
			.on('end', (placedWords: Word[]) => {
				drawWords(placedWords);
				isRendering = false;
			});

		layout.start();
	}

	function drawWords(placedWords: Word[]) {
		if (!d3) return;
		const d3Ref = d3;

		const svg = d3Ref
			.select(svgElement)
			.attr('viewBox', `0 0 ${containerWidth} ${containerHeight}`)
			.attr('preserveAspectRatio', 'xMidYMid meet')
			.style('background-color', backgroundColor);

		const g = svg
			.append('g')
			.attr('transform', `translate(${containerWidth / 2},${containerHeight / 2})`);

		const text = g
			.selectAll('text')
			.data(placedWords)
			.enter()
			.append('text')
			.style('font-size', (d: Word) => `${d.size}px`)
			.style('font-family', fontFamily)
			.style('fill', (d: Word) => d.color ?? '')
			.style('cursor', 'pointer')
			.attr('text-anchor', 'middle')
			.attr('transform', (d: Word) => `translate(${d.x || 0},${d.y || 0})rotate(${d.rotate || 0})`)
			.text((d: Word) => d.text)
			.on('mouseover', function (this: SVGTextElement, event: Event, d: Word) {
				d3Ref.select(this).style('opacity', 0.7);
				if (hover) hover(d, event);
			})
			.on('mouseout', function (this: SVGTextElement) {
				d3Ref.select(this).style('opacity', 1);
			})
			.on('click', function (event: Event, d: Word) {
				if (click) click(d, event);
			});

		// Add entrance animation
		const textSelection = text.style('opacity', 0);
		// d3-transition augments Selection with .transition() when imported
		const transitionable = textSelection as typeof textSelection & {
			transition?: () => {
				duration: (ms: number) => {
					delay: (fn: (d: Word, i: number) => number) => {
						style: (name: string, value: string) => void;
					};
				};
			};
		};
		if (typeof transitionable.transition === 'function') {
			transitionable
				.transition()
				.duration(600)
				.delay((_d: Word, i: number) => i * 50)
				.style('opacity', '1');
		} else {
			textSelection.style('opacity', 1);
		}
	}

	// Re-render when data or settings change, or container size changes
	$effect(() => {
		// Read all reactive dependencies synchronously to ensure tracking
		const _currentData = data;
		const _currentWidth = containerWidth;
		const _currentHeight = containerHeight;
		const _currentColorScheme = colorScheme;
		const _currentMinFontSize = minFontSize;
		const _currentMaxFontSize = maxFontSize;
		const _currentPadding = padding;
		const _currentMinRotation = minRotation;
		const _currentMaxRotation = maxRotation;
		const _currentFontFamily = fontFamily;

		if (svgElement && d3 && _currentData && colorScale && getD3CloudGlobal().d3?.layout?.cloud) {
			// Use untrack to prevent state updates within renderWordCloud from triggering this effect again
			untrack(() => {
				renderWordCloud();
			});
		}
	});

	// Export function to manually trigger re-render
	export function refresh() {
		renderWordCloud();
	}
</script>

<div class="wordcloud-container" bind:this={containerElement}>
	<svg bind:this={svgElement} class="wordcloud-svg" style="background-color: {backgroundColor};"
	></svg>

	{#if isRendering}
		<div class="loading-overlay">
			<div class="loading-spinner"></div>
			<p class="text-sm text-muted-foreground">{t('words.generating')}</p>
		</div>
	{/if}

	{#if data.length === 0}
		<div class="empty-state">
			<p class="text-muted-foreground">{t('words.no_data')}</p>
		</div>
	{/if}
</div>

<style>
	.wordcloud-container {
		position: relative;
		width: 100%;
		aspect-ratio: 2 / 1;
		min-height: 300px;
		border: 1px solid hsl(var(--border));
		border-radius: 0.5rem;
		overflow: hidden;
		background: var(--background);
	}

	.wordcloud-svg {
		display: block;
		width: 100%;
		height: 100%;
	}

	.loading-overlay {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(255, 255, 255, 0.8);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}

	.loading-spinner {
		width: 2rem;
		height: 2rem;
		border: 2px solid hsl(var(--muted));
		border-top: 2px solid hsl(var(--primary));
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	.empty-state {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		display: flex;
		align-items: center;
		justify-content: center;
	}
</style>

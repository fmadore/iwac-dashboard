<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import type { Word } from '$lib/types/index.js';

	interface Props {
		data?: [string, number][];
		width?: number;
		height?: number;
		backgroundColor?: string;
		fontFamily?: string;
		colorScheme?: 'category10' | 'set3' | 'dark2' | 'accent' | 'pastel1' | 'pastel2' | 'set1' | 'set2' | 'tableau10';
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
		width = 800,
		height = 400,
		backgroundColor = '#ffffff',
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

	let svgElement: SVGSVGElement;
	let d3: any;
	let colorScale: string[];
	let isRendering = $state(false);
	let words = $state<Word[]>([]);

	onMount(async () => {
		if (browser) {
			try {
				// Import d3-selection, d3-scale-chromatic, and d3-transition
				const [d3Module, chromatic, transition] = await Promise.all([
					import('d3-selection'),
					import('d3-scale-chromatic'),
					import('d3-transition')
				]);
				
				d3 = d3Module;
				colorScale = getColorScale(chromatic);
				
				// Load d3-cloud library
				await loadD3Cloud();
				
				// Initial render
				renderWordCloud();
			} catch (error) {
				console.error('Failed to load d3 libraries:', error);
			}
		}
	});

	async function loadD3Cloud() {
		try {
			// Try to import d3-cloud and use it to set up the global d3.layout.cloud
			const cloudModule = await import('d3-cloud');
			
			// Ensure global d3 object exists
			if (typeof window !== 'undefined') {
				(window as any).d3 = (window as any).d3 || {};
				(window as any).d3.layout = (window as any).d3.layout || {};
				(window as any).d3.layout.cloud = cloudModule.default || cloudModule;
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

	function getColorScale(chromatic: any): string[] {
		const schemes = {
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
		return schemes[colorScheme] || schemes.category10;
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
		const cloudLayout = (window as any).d3?.layout?.cloud;
		if (!cloudLayout) {
			console.error('d3.layout.cloud not available');
			isRendering = false;
			return;
		}
		
		// Create cloud layout using the correct d3.layout.cloud API
		const layout = cloudLayout()
			.size([width, height])
			.words(wordData)
			.padding(padding)
			.rotate(() => Math.random() * (maxRotation - minRotation) + minRotation)
			.font(fontFamily)
			.fontSize((d: Word) => d.size)
			.on('end', (placedWords: Word[]) => {
				words = placedWords;
				drawWords(placedWords);
				isRendering = false;
			});
		
		layout.start();
	}

	function drawWords(placedWords: Word[]) {
		const svg = d3.select(svgElement)
			.attr('width', width)
			.attr('height', height)
			.style('background-color', backgroundColor);
		
		const g = svg.append('g')
			.attr('transform', `translate(${width / 2},${height / 2})`);
		
		const text = g.selectAll('text')
			.data(placedWords)
			.enter()
			.append('text')
			.style('font-size', (d: Word) => `${d.size}px`)
			.style('font-family', fontFamily)
			.style('fill', (d: Word) => d.color || '#000')
			.style('cursor', 'pointer')
			.attr('text-anchor', 'middle')
			.attr('transform', (d: Word) => `translate(${d.x || 0},${d.y || 0})rotate(${d.rotate || 0})`)
			.text((d: Word) => d.text)
			.on('mouseover', function(this: SVGTextElement, event: Event, d: Word) {
				d3.select(this).style('opacity', 0.7);
				if (hover) hover(d, event);
			})
			.on('mouseout', function(this: SVGTextElement) {
				d3.select(this).style('opacity', 1);
			})
			.on('click', function(event: Event, d: Word) {
				if (click) click(d, event);
			});
		
		// Add entrance animation
		text.style('opacity', 0)
			.transition()
			.duration(600)
			.delay((d: Word, i: number) => i * 50)
			.style('opacity', 1);
	}

	// Re-render when data or settings change
	$effect(() => {
		if (svgElement && d3 && data && colorScale && (window as any).d3?.layout?.cloud) {
			renderWordCloud();
		}
	});

	// Export function to manually trigger re-render
	export function refresh() {
		renderWordCloud();
	}
</script>

<div class="wordcloud-container" style="width: {width}px; height: {height}px;">
	<svg
		bind:this={svgElement}
		class="wordcloud-svg"
		style="max-width: 100%; height: auto; background-color: {backgroundColor};"
	></svg>
	
	{#if isRendering}
		<div class="loading-overlay">
			<div class="loading-spinner"></div>
			<p class="text-sm text-muted-foreground">Generating word cloud...</p>
		</div>
	{/if}
	
	{#if data.length === 0}
		<div class="empty-state">
			<p class="text-muted-foreground">No data available for word cloud</p>
		</div>
	{/if}
</div>

<style>
	.wordcloud-container {
		position: relative;
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
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
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
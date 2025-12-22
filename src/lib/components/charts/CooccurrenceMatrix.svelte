<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { browser } from '$app/environment';
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';

	interface CooccurrenceData {
		terms: string[];
		matrix: number[][];
		term_counts: Record<string, number>;
		max_cooccurrence: number;
		total_articles?: number;
	}

	interface Props {
		data: CooccurrenceData | null;
		orderBy?: 'name' | 'count' | 'cluster';
		showDiagonal?: boolean;
		cellSize?: number;
		margin?: { top: number; right: number; bottom: number; left: number };
	}

	const {
		data = null,
		orderBy = 'name',
		showDiagonal = false,
		cellSize = 40,
		margin = { top: 120, right: 20, bottom: 20, left: 120 }
	}: Props = $props();

	let containerElement: HTMLDivElement | null = $state(null);
	let svgElement: SVGSVGElement | null = $state(null);
	let tooltip: HTMLDivElement | null = $state(null);
	let d3Module: any = null;
	let containerWidth = $state(800);
	let resizeObserver: ResizeObserver | null = null;

	// Computed cell size based on container width
	const effectiveCellSize = $derived.by(() => {
		if (!data || data.terms.length === 0) return cellSize;
		const availableWidth = containerWidth - margin.left - margin.right;
		const calculatedSize = Math.floor(availableWidth / data.terms.length);
		// Clamp between min and max sizes
		return Math.max(25, Math.min(cellSize, calculatedSize));
	});

	// Computed dimensions
	const width = $derived(data ? data.terms.length * effectiveCellSize + margin.left + margin.right : 0);
	const height = $derived(data ? data.terms.length * effectiveCellSize + margin.top + margin.bottom : 0);

	// Order terms based on selected ordering
	const orderedTerms = $derived.by(() => {
		if (!data || !data.terms.length) return [];

		const terms = [...data.terms];

		switch (orderBy) {
			case 'count':
				// Order by total term count (descending)
				return terms.sort(
					(a, b) => (data.term_counts[b] || 0) - (data.term_counts[a] || 0)
				);
			case 'cluster':
				// Simple clustering by co-occurrence similarity
				return clusterTerms(terms, data.matrix, data.terms);
			case 'name':
			default:
				return terms.sort((a, b) => a.localeCompare(b, 'fr'));
		}
	});

	// Create ordered indices mapping
	const orderedIndices = $derived.by(() => {
		if (!data || !orderedTerms.length) return [];
		return orderedTerms.map((term) => data.terms.indexOf(term));
	});

	// Reorder matrix based on term ordering
	const orderedMatrix = $derived.by(() => {
		if (!data || !orderedIndices.length) return [];

		const n = orderedIndices.length;
		const newMatrix: number[][] = [];

		for (let i = 0; i < n; i++) {
			const row: number[] = [];
			for (let j = 0; j < n; j++) {
				row.push(data.matrix[orderedIndices[i]][orderedIndices[j]]);
			}
			newMatrix.push(row);
		}

		return newMatrix;
	});

	function clusterTerms(
		terms: string[],
		matrix: number[][],
		originalTerms: string[]
	): string[] {
		// Simple hierarchical clustering based on co-occurrence similarity
		if (terms.length <= 2) return terms;

		// Compute similarity matrix (normalized co-occurrence)
		const n = terms.length;
		const indices = terms.map((t) => originalTerms.indexOf(t));

		// Use greedy nearest neighbor ordering
		const ordered: string[] = [];
		const remaining = new Set(terms);

		// Start with term with highest total co-occurrence
		let maxTotal = -1;
		let startTerm = terms[0];
		for (const term of terms) {
			const idx = originalTerms.indexOf(term);
			let total = 0;
			for (let j = 0; j < originalTerms.length; j++) {
				if (j !== idx) total += matrix[idx][j];
			}
			if (total > maxTotal) {
				maxTotal = total;
				startTerm = term;
			}
		}

		ordered.push(startTerm);
		remaining.delete(startTerm);

		// Greedy: always pick the most similar remaining term
		while (remaining.size > 0) {
			const lastTerm = ordered[ordered.length - 1];
			const lastIdx = originalTerms.indexOf(lastTerm);

			let bestTerm = '';
			let bestSimilarity = -1;

			for (const term of remaining) {
				const idx = originalTerms.indexOf(term);
				const similarity = matrix[lastIdx][idx] + matrix[idx][lastIdx];
				if (similarity > bestSimilarity) {
					bestSimilarity = similarity;
					bestTerm = term;
				}
			}

			if (bestTerm) {
				ordered.push(bestTerm);
				remaining.delete(bestTerm);
			} else {
				// Fallback: just add remaining
				ordered.push(...remaining);
				break;
			}
		}

		return ordered;
	}

	function getCSSVariable(variable: string): string {
		if (!browser) return '#000000';
		const root = document.documentElement;
		const value = getComputedStyle(root).getPropertyValue(variable).trim();
		
		// Return the computed color value, ensuring we have a valid color
		if (!value) return '#000000';
		
		// If it's already an oklch/rgb/hex color, return it
		if (value.startsWith('#') || value.startsWith('rgb') || value.startsWith('oklch')) {
			return value;
		}
		
		// Fallback
		return '#000000';
	}

	onMount(() => {
		if (!browser) return;

		let active = true;

		// Set up ResizeObserver
		if (containerElement) {
			resizeObserver = new ResizeObserver((entries) => {
				for (const entry of entries) {
					const { width } = entry.contentRect;
					if (width > 0) {
						containerWidth = width;
					}
				}
			});
			resizeObserver.observe(containerElement);
			
			// Get initial size
			const rect = containerElement.getBoundingClientRect();
			if (rect.width > 0) {
				containerWidth = rect.width;
			}
		}

		const initialize = async () => {
			try {
				// Import D3 modules
				const [selectionModule, scaleModule, chromaticModule] = await Promise.all([
					import('d3-selection'),
					import('d3-scale'),
					import('d3-scale-chromatic')
				]);

				if (!active) return;

				d3Module = {
					select: selectionModule.select,
					selectAll: selectionModule.selectAll,
					scaleLinear: scaleModule.scaleLinear,
					scaleSequential: scaleModule.scaleSequential,
					interpolateBlues: chromaticModule.interpolateBlues
				};

				// Initial render
				renderMatrix();
			} catch (error) {
				console.error('Failed to load D3 libraries:', error);
			}
		};

		initialize();

		return () => {
			active = false;
			if (resizeObserver) {
				resizeObserver.disconnect();
				resizeObserver = null;
			}
		};
	});

	// Re-render when data, ordering, or size changes
	$effect(() => {
		if (d3Module && data && orderedMatrix.length > 0) {
			// Track language and size changes
			const _ = languageStore.current;
			const __ = effectiveCellSize;
			untrack(() => renderMatrix());
		}
	});

	function renderMatrix() {
		if (!svgElement || !d3Module || !data || orderedMatrix.length === 0) return;

		const { select, scaleLinear, scaleSequential, interpolateBlues } = d3Module;

		// Clear previous content
		const svg = select(svgElement);
		svg.selectAll('*').remove();

		const n = orderedTerms.length;

		// Color scales
		const maxValue = data.max_cooccurrence || 1;
		const colorScale = scaleSequential(interpolateBlues).domain([0, maxValue]);

		// Get theme colors
		const foregroundColor = getCSSVariable('--foreground');
		const borderColor = getCSSVariable('--border');
		const mutedColor = getCSSVariable('--muted-foreground');

		// Create main group
		const g = svg
			.append('g')
			.attr('transform', `translate(${margin.left}, ${margin.top})`);

		const currentCellSize = effectiveCellSize;

		// Draw cells
		for (let i = 0; i < n; i++) {
			for (let j = 0; j < n; j++) {
				const value = orderedMatrix[i][j];
				const isDiagonal = i === j;

				// Skip diagonal if not showing
				if (isDiagonal && !showDiagonal) continue;

				// Skip zero values (except diagonal)
				if (value === 0 && !isDiagonal) continue;

				// Capture loop variables for closure
				const rowIdx = i;
				const colIdx = j;
				const cellValue = value;
				const cellIsDiagonal = isDiagonal;

				g
					.append('rect')
					.attr('x', j * currentCellSize)
					.attr('y', i * currentCellSize)
					.attr('width', currentCellSize - 1)
					.attr('height', currentCellSize - 1)
					.attr('rx', 2)
					.style('fill', isDiagonal ? 'var(--muted)' : colorScale(value))
					.style('stroke', borderColor)
					.style('stroke-width', 0.5)
					.style('cursor', 'pointer')
					.on('mouseover', function (this: SVGRectElement, event: MouseEvent) {
						showTooltip(event, orderedTerms[rowIdx], orderedTerms[colIdx], cellValue, cellIsDiagonal);
						select(this).style('stroke-width', 2).style('stroke', 'var(--primary)');
					})
					.on('mousemove', function (this: SVGRectElement, event: MouseEvent) {
						updateTooltipPosition(event);
					})
					.on('mouseout', function (this: SVGRectElement) {
						hideTooltip();
						select(this).style('stroke-width', 0.5).style('stroke', borderColor);
					});
			}
		}

		// Font size based on cell size - increased minimum for better readability
		const fontSize = Math.max(11, Math.min(14, currentCellSize * 0.32));

		// Add row labels (left side)
		g.selectAll('.row-label')
			.data(orderedTerms)
			.enter()
			.append('text')
			.attr('class', 'row-label')
			.attr('x', -8)
			.attr('y', (d: string, i: number) => i * currentCellSize + currentCellSize / 2)
			.attr('text-anchor', 'end')
			.attr('dominant-baseline', 'middle')
			.style('font-size', `${fontSize}px`)
			.style('font-weight', '500')
			.style('fill', foregroundColor)
			.text((d: string) => d);

		// Add column labels (top)
		g.selectAll('.col-label')
			.data(orderedTerms)
			.enter()
			.append('text')
			.attr('class', 'col-label')
			.attr('x', (d: string, i: number) => i * currentCellSize + currentCellSize / 2)
			.attr('y', -8)
			.attr('text-anchor', 'start')
			.attr('dominant-baseline', 'middle')
			.attr('transform', (d: string, i: number) => 
				`rotate(-45, ${i * currentCellSize + currentCellSize / 2}, -8)`
			)
			.style('font-size', `${fontSize}px`)
			.style('font-weight', '500')
			.style('fill', foregroundColor)
			.text((d: string) => d);
	}

	function showTooltip(
		event: MouseEvent,
		term1: string,
		term2: string,
		value: number,
		isDiagonal: boolean
	) {
		if (!tooltip) return;

		let content = '';
		if (isDiagonal) {
			content = `<strong>${term1}</strong><br/>${t('cooccurrence.term_count')}: ${value.toLocaleString()}`;
		} else {
			content = `<strong>${term1}</strong> ↔ <strong>${term2}</strong><br/>${t('cooccurrence.cooccurrences')}: ${value.toLocaleString()}`;
		}

		tooltip.innerHTML = content;
		tooltip.style.display = 'block';
		updateTooltipPosition(event);
	}

	function updateTooltipPosition(event: MouseEvent) {
		if (!tooltip) return;
		
		// Position tooltip avoiding screen edges
		const tooltipRect = tooltip.getBoundingClientRect();
		const padding = 10;
		
		let left = event.clientX + padding;
		let top = event.clientY + padding;
		
		// Adjust if tooltip would go off right edge
		if (left + tooltipRect.width > window.innerWidth - padding) {
			left = event.clientX - tooltipRect.width - padding;
		}
		
		// Adjust if tooltip would go off bottom edge
		if (top + tooltipRect.height > window.innerHeight - padding) {
			top = event.clientY - tooltipRect.height - padding;
		}
		
		tooltip.style.left = `${left}px`;
		tooltip.style.top = `${top}px`;
	}

	function hideTooltip() {
		if (!tooltip) return;
		tooltip.style.display = 'none';
	}
</script>

<div class="cooccurrence-container relative" bind:this={containerElement}>
	{#if !data || data.terms.length === 0}
		<div class="flex h-64 items-center justify-center text-muted-foreground">
			{t('common.no_data')}
		</div>
	{:else}
		<div class="overflow-auto">
			<svg
				bind:this={svgElement}
				{width}
				{height}
				class="cooccurrence-matrix"
			></svg>
		</div>

		<!-- Legend -->
		<div class="mt-4 flex items-center justify-center gap-4 text-sm text-muted-foreground">
			<div class="flex items-center gap-2">
				<div
					class="h-4 w-4 rounded"
					style="background: linear-gradient(to right, white, var(--chart-2));"
				></div>
				<span>{t('cooccurrence.low')}</span>
			</div>
			<div class="flex items-center gap-2">
				<div
					class="h-4 w-4 rounded"
					style="background: var(--chart-2);"
				></div>
				<span>{t('cooccurrence.high')}</span>
			</div>
		</div>

		<!-- Tooltip -->
		<div
			bind:this={tooltip}
			class="pointer-events-none fixed z-50 hidden rounded-md border border-border bg-popover px-3 py-2 text-sm text-popover-foreground shadow-md"
		></div>
	{/if}
</div>

<style>
	.cooccurrence-container {
		width: 100%;
	}

	.cooccurrence-matrix {
		display: block;
		margin: 0 auto;
	}
</style>

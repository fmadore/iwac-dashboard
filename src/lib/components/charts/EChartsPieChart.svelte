<script lang="ts">
	import * as Chart from '$lib/components/ui/chart/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { PieChart, Tooltip as TooltipPrimitive } from 'layerchart';

	interface PieDataItem {
		label: string;
		value: number;
		/**
		 * Color for the slice. Prefer theme variables like `var(--chart-1)`.
		 * We also accept `--chart-1` (converted to `var(--chart-1)`).
		 */
		color?: string;
		percentage?: string;
	}

	interface Props {
		data?: PieDataItem[];
		innerRadius?: number | string;
		outerRadius?: number | string;
		showLabels?: boolean;
		showValues?: boolean;
		animationDuration?: number;
		minSlicePercent?: number;
	}

	let {
		data = [],
		innerRadius = '0%',
		outerRadius = '75%',
		showLabels = true,
		showValues = true,
		animationDuration = 1000,
		minSlicePercent = 0.5
	}: Props = $props();

	function asCssColor(value: string | undefined): string | undefined {
		if (!value) return undefined;
		const trimmed = value.trim();
		if (!trimmed) return undefined;
		if (trimmed.startsWith('var(')) return trimmed;
		if (trimmed.startsWith('--')) return `var(${trimmed})`;
		return trimmed;
	}

	function toCssKey(input: string): string {
		return input
			.normalize('NFKD')
			.replace(/[\u0300-\u036f]/g, '')
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/^-+|-+$/g, '');
	}

	function normalizeInnerRadius(value: number | string | undefined): number | undefined {
		if (value === undefined || value === null) return undefined;
		if (typeof value === 'number') return value;
		const trimmed = value.trim();
		if (trimmed.endsWith('%')) {
			const p = Number.parseFloat(trimmed.slice(0, -1));
			if (!Number.isFinite(p)) return undefined;
			return Math.max(0, p / 100);
		}
		const n = Number.parseFloat(trimmed);
		return Number.isFinite(n) ? n : undefined;
	}

	function normalizeOuterRadius(value: number | string | undefined): number | undefined {
		if (value === undefined || value === null) return undefined;
		if (typeof value === 'number') return value;
		const trimmed = value.trim();
		// LayerChart's `outerRadius` is a pixel number; if a percentage is passed (ECharts-style),
		// ignore it and let LayerChart compute a responsive radius.
		if (trimmed.endsWith('%')) return undefined;
		const n = Number.parseFloat(trimmed);
		return Number.isFinite(n) ? n : undefined;
	}

	const normalizedInnerRadius = $derived(normalizeInnerRadius(innerRadius));
	const normalizedOuterRadius = $derived(normalizeOuterRadius(outerRadius));

	const totalValue = $derived(data.reduce((sum, item) => sum + item.value, 0));

	// Group small slices into "Others" (keeps the same behavior as the old ECharts version).
	const grouped = $derived.by(() => {
		if (!data.length) return { processedData: [] as PieDataItem[], othersGroupDetails: [] as PieDataItem[] };

		const sorted = [...data].sort((a, b) => b.value - a.value);
		const total = sorted.reduce((sum, item) => sum + item.value, 0);
		if (!total) return { processedData: [] as PieDataItem[], othersGroupDetails: [] as PieDataItem[] };

		const topSlicePercent = ((sorted[0]?.value ?? 0) / total) * 100;

		if (topSlicePercent > 90) {
			const mainSlices = sorted.slice(0, 5);
			const smallSlices = sorted.slice(5);

			if (smallSlices.length) {
				const othersValue = smallSlices.reduce((sum, item) => sum + item.value, 0);
				return {
					processedData: [
						...mainSlices,
						{
							label: t('chart.others', [String(smallSlices.length)]),
							value: othersValue,
							color: 'var(--muted-foreground)'
						}
					],
					othersGroupDetails: smallSlices
				};
			}

			return { processedData: mainSlices, othersGroupDetails: [] as PieDataItem[] };
		}

		const threshold = (minSlicePercent / 100) * total;
		const mainSlices: PieDataItem[] = [];
		const smallSlices: PieDataItem[] = [];

		sorted.forEach((item, index) => {
			if (index < 8 && item.value >= threshold) mainSlices.push(item);
			else if (item.value < threshold) smallSlices.push(item);
			else mainSlices.push(item);
		});

		if (smallSlices.length > 2) {
			const othersValue = smallSlices.reduce((sum, item) => sum + item.value, 0);
			return {
				processedData: [
					...mainSlices,
					{
						label: t('chart.others', [String(smallSlices.length)]),
						value: othersValue,
						color: 'var(--muted-foreground)'
					}
				],
				othersGroupDetails: smallSlices
			};
		}

		return { processedData: [...mainSlices, ...smallSlices], othersGroupDetails: [] as PieDataItem[] };
	});

	const processedData = $derived(grouped.processedData);
	const othersGroupDetails = $derived(grouped.othersGroupDetails);

	// Turn the incoming labels into CSS-safe keys for ChartStyle variables.
	const layerData = $derived.by(() => {
		const used = new Map<string, number>();
		return processedData.map((item, index) => {
			const base = toCssKey(item.label) || 'item';
			const seen = used.get(base) ?? 0;
			used.set(base, seen + 1);
			const key = seen ? `${base}-${seen}` : base;

			// Keep colors stable and theme-friendly.
			const fallbackColor = `var(--chart-${(index % 16) + 1})`;
			const resolvedColor = asCssColor(item.color) ?? fallbackColor;

			return {
				key,
				label: item.label,
				value: item.value,
				configColor: resolvedColor,
				cssColorVar: `var(--color-${key})`,
				isOthers: othersGroupDetails.length > 0 && item.label === processedData[processedData.length - 1]?.label
			};
		});
	});

	const chartConfig = $derived.by(() => {
		const config: Chart.ChartConfig = {};
		for (const item of layerData) {
			config[item.key] = { label: item.label, color: item.configColor };
		}
		return config;
	});

	const cRange = $derived(layerData.map((d) => d.cssColorVar));

	function formatPercent(part: number, total: number): string {
		if (!total) return '0.0%';
		return `${((part / total) * 100).toFixed(1)}%`;
	}
</script>

<div
	class="h-full min-h-[400px] w-full"
	role="img"
	aria-label={t('chart.pie_distribution_aria')}
>
	{#if layerData.length > 0}
		<Chart.Container config={chartConfig} class="h-full w-full min-w-0 justify-start">
			<PieChart
				data={layerData}
				key="key"
				label="label"
				value="value"
				legend={showLabels}
				cRange={cRange}
				innerRadius={normalizedInnerRadius}
				outerRadius={normalizedOuterRadius}
				padding={28}
				props={{
					pie: { motion: { type: 'tween', duration: animationDuration } },
					legend: { placement: 'bottom', variant: 'swatches' }
				}}
			>
				{#snippet tooltip({ context })}
					<TooltipPrimitive.Root variant="none" context={context}>
						{#snippet children({ data: hovered, payload })}
							<div
								class="grid min-w-[9rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl"
							>
								<div class="font-medium">{hovered.label}</div>
								{#if showValues}
									<div class="flex items-center justify-between gap-4">
										<span class="text-muted-foreground">{t('chart.documents')}</span>
										<span class="font-mono font-medium text-foreground tabular-nums">
											{Number(hovered.value).toLocaleString()}
										</span>
									</div>
								{/if}
								<div class="text-muted-foreground">{formatPercent(Number(hovered.value), totalValue)}</div>

								{#if othersGroupDetails.length > 0 && hovered.isOthers}
									<div class="mt-1 grid gap-1">
										{#each othersGroupDetails as item (item.label)}
											<div class="flex items-center justify-between gap-4">
												<span class="text-muted-foreground">{item.label}</span>
												<span class="font-mono text-foreground tabular-nums">
													{item.value.toLocaleString()} ({formatPercent(item.value, totalValue)})
												</span>
											</div>
										{/each}
									</div>
								{/if}
							</div>
						{/snippet}
					</TooltipPrimitive.Root>
				{/snippet}
			</PieChart>
		</Chart.Container>
	{:else}
		<div class="flex h-[200px] items-center justify-center text-muted-foreground">
			{t('chart.no_data')}
		</div>
	{/if}
</div>


<script lang="ts" module>
	import type { Snippet } from 'svelte';

	/**
	 * Represents a single item to display in the tooltip.
	 */
	export interface TooltipItem {
		/** Display name for this item */
		name: string;
		/** Value to display */
		value: number | string;
		/** Color indicator (CSS color or variable like 'var(--chart-1)') */
		color?: string;
		/** Optional key for unique identification */
		key?: string;
	}

	/**
	 * Props for the LayerChartTooltip component.
	 */
	export interface LayerChartTooltipProps {
		/** Label displayed at the top of the tooltip (e.g., category name) */
		label?: string;
		/** Array of items to display */
		items?: TooltipItem[];
		/** Style of the color indicator */
		indicator?: 'dot' | 'line' | 'dashed';
		/** Whether to hide the label */
		hideLabel?: boolean;
		/** Whether to hide the color indicator */
		hideIndicator?: boolean;
		/** Custom content to render instead of items */
		children?: Snippet;
		/** Additional CSS class */
		class?: string;
	}
</script>

<script lang="ts">
	import { cn } from '$lib/utils.js';

	let {
		label,
		items = [],
		indicator = 'dot',
		hideLabel = false,
		hideIndicator = false,
		children,
		class: className
	}: LayerChartTooltipProps = $props();

	// Helper to format numbers with locale
	function formatValue(value: number | string): string {
		if (typeof value === 'number') return value.toLocaleString();
		return String(value);
	}
</script>

{#if children}
	{@render children()}
{:else if items.length > 0 || label}
	<div
		class={cn(
			'grid min-w-36 items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl',
			className
		)}
	>
		{#if !hideLabel && label}
			<div class="font-medium">{label}</div>
		{/if}

		{#if items.length > 0}
			<div class="grid gap-1.5">
				{#each items as item, i (item.key ?? item.name ?? i)}
					<div
						class={cn(
							'flex w-full flex-wrap items-stretch gap-2',
							indicator === 'dot' && 'items-center'
						)}
					>
						{#if !hideIndicator && item.color}
							<div
								style="--color-bg: {item.color}; --color-border: {item.color};"
								class={cn('shrink-0 rounded-[2px] border-(--color-border) bg-(--color-bg)', {
									'size-2.5': indicator === 'dot',
									'h-full w-1': indicator === 'line',
									'w-0 border-[1.5px] border-dashed bg-transparent': indicator === 'dashed'
								})}
							></div>
						{/if}
						<div class="flex flex-1 shrink-0 items-center justify-between leading-none">
							<span class="text-muted-foreground">{item.name}</span>
							<span class="font-mono font-medium text-foreground tabular-nums">
								{formatValue(item.value)}
							</span>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}

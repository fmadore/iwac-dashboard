<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { ExternalLink } from '@lucide/svelte';
	import type { MapLocation, PopoverPosition } from '$lib/types/map-location.js';

	interface Props {
		location: MapLocation | null;
		position: PopoverPosition | null;
		itemLabel?: string;
	}

	let { location, position, itemLabel = 'publications' }: Props = $props();

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	const isVisible = $derived(location !== null && position !== null);

	function getItemLabel(count: number): string {
		// Use provided label or default to publications
		return t(`map_popup.${itemLabel}`, [count.toString()]) || `${count} ${itemLabel}`;
	}
</script>

{#if isVisible && location && position}
	<div
		class="map-location-popover"
		style="
			left: {position.x}px;
			top: {position.y}px;
			transform: translateX(-50%) {position.placement === 'top' ? 'translateY(-100%)' : 'translateY(8px)'};
		"
		role="tooltip"
	>
		<div class="popover-content">
			<!-- Location name with optional external link -->
			<div class="popover-header">
				{#if location.externalUrl}
					<a
						href={location.externalUrl}
						target="_blank"
						rel="noopener noreferrer"
						class="location-link"
					>
						<span class="location-name">{location.name}</span>
						<ExternalLink class="h-3.5 w-3.5 shrink-0" />
					</a>
				{:else}
					<span class="location-name">{location.name}</span>
				{/if}
			</div>

			<!-- Stats row: count badge, year range, country -->
			<div class="popover-stats">
				<Badge variant="secondary" class="text-xs">
					{location.count}
				</Badge>

				{#if location.yearRange}
					<span class="year-range">
						{location.yearRange.start}–{location.yearRange.end}
					</span>
				{/if}

				{#if location.country}
					<span class="country">{location.country}</span>
				{/if}
			</div>

			<!-- Hint text -->
			<div class="popover-hint">
				{t('map_popup.view_details')}
			</div>
		</div>

		<!-- Arrow pointer -->
		<div
			class="popover-arrow"
			class:arrow-bottom={position.placement === 'top'}
			class:arrow-top={position.placement === 'bottom'}
		></div>
	</div>
{/if}

<style>
	.map-location-popover {
		position: absolute;
		z-index: 1000;
		pointer-events: none;
		animation: popover-fade-in 0.15s ease-out;
	}

	@keyframes popover-fade-in {
		from {
			opacity: 0;
			transform: translateX(-50%) translateY(-90%);
		}
		to {
			opacity: 1;
		}
	}

	.popover-content {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 0.5rem;
		padding: 0.75rem;
		box-shadow:
			0 4px 6px -1px rgb(0 0 0 / 0.1),
			0 2px 4px -2px rgb(0 0 0 / 0.1);
		min-width: 160px;
		max-width: 280px;
	}

	.popover-header {
		margin-bottom: 0.5rem;
	}

	.location-link {
		display: inline-flex;
		align-items: center;
		gap: 0.375rem;
		color: var(--primary);
		text-decoration: none;
		font-weight: 600;
		font-size: 0.875rem;
		line-height: 1.25rem;
	}

	.location-link:hover {
		text-decoration: underline;
	}

	.location-name {
		font-weight: 600;
		font-size: 0.875rem;
		line-height: 1.25rem;
		color: var(--foreground);
	}

	.popover-stats {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: var(--muted-foreground);
	}

	.year-range {
		font-variant-numeric: tabular-nums;
	}

	.country {
		opacity: 0.8;
	}

	.popover-hint {
		margin-top: 0.5rem;
		font-size: 0.675rem;
		color: var(--muted-foreground);
		opacity: 0.7;
		font-style: italic;
	}

	.popover-arrow {
		position: absolute;
		left: 50%;
		transform: translateX(-50%);
		width: 0;
		height: 0;
		border-left: 6px solid transparent;
		border-right: 6px solid transparent;
	}

	.arrow-bottom {
		bottom: -6px;
		border-top: 6px solid var(--card);
	}

	.arrow-top {
		top: -6px;
		border-bottom: 6px solid var(--card);
	}
</style>

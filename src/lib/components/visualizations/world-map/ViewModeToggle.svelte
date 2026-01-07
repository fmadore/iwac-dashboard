<script lang="ts">
	import { mapDataStore } from '$lib/stores/mapDataStore.svelte.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { Globe, CircleDot } from '@lucide/svelte';

	// Reactive state for current view mode
	const currentViewMode = $derived(mapDataStore.viewMode);

	function toggleToBubbles() {
		mapDataStore.setViewMode('bubbles');
	}

	function toggleToChoropleth() {
		mapDataStore.setViewMode('choropleth');
	}
</script>

<div class="view-mode-toggle">
	<div class="toggle-group">
		<button
			type="button"
			class="toggle-button"
			class:active={currentViewMode === 'bubbles'}
			onclick={toggleToBubbles}
			aria-pressed={currentViewMode === 'bubbles'}
			title={t('worldmap.bubbles')}
		>
			<CircleDot size={14} />
			<span>{t('worldmap.bubbles')}</span>
		</button>
		<button
			type="button"
			class="toggle-button"
			class:active={currentViewMode === 'choropleth'}
			onclick={toggleToChoropleth}
			aria-pressed={currentViewMode === 'choropleth'}
			title={t('worldmap.choropleth')}
		>
			<Globe size={14} />
			<span>{t('worldmap.choropleth')}</span>
		</button>
	</div>
</div>

<style>
	.view-mode-toggle {
		display: inline-block;
	}

	.toggle-group {
		display: flex;
		background: var(--card);
		backdrop-filter: blur(10px);
		border-radius: 0.75rem;
		padding: 0.25rem;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
		border: 1px solid var(--border);
	}

	.toggle-button {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.375rem 0.625rem;
		border: none;
		background: transparent;
		border-radius: 0.5rem;
		font-size: 0.8125rem;
		font-weight: 500;
		color: var(--muted-foreground);
		cursor: pointer;
		transition: all 0.2s ease;
		white-space: nowrap;
	}

	.toggle-button:hover {
		background: var(--accent);
		color: var(--primary);
		transform: translateY(-1px);
	}

	.toggle-button.active {
		background: var(--primary);
		color: var(--primary-foreground);
		box-shadow: 0 2px 8px color-mix(in oklch, var(--primary) 30%, transparent);
	}

	.toggle-button.active:hover {
		transform: translateY(0);
	}

	@media (max-width: 640px) {
		.toggle-button span {
			display: none;
		}

		.toggle-button {
			padding: 0.375rem;
		}
	}
</style>

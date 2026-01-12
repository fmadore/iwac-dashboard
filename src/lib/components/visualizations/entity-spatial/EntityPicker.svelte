<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { entitySpatialStore } from '$lib/stores/entitySpatialStore.svelte.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { ScrollArea } from '$lib/components/ui/scroll-area/index.js';
	import type { EntitySummary } from '$lib/types/entity-spatial.js';

	let isOpen = $state(false);
	let inputElement = $state<HTMLInputElement | null>(null);

	const searchQuery = $derived(entitySpatialStore.searchQuery);
	const filteredEntities = $derived(entitySpatialStore.filteredEntities);
	const selectedEntityId = $derived(entitySpatialStore.selectedEntityId);
	const currentEntity = $derived(entitySpatialStore.currentEntity);

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	// Get display value for input
	const displayValue = $derived.by(() => {
		if (currentEntity) {
			return currentEntity.name;
		}
		return searchQuery;
	});

	function handleInputChange(e: Event) {
		const target = e.target as HTMLInputElement;
		entitySpatialStore.setSearchQuery(target.value);
		entitySpatialStore.setSelectedEntity(null);
		isOpen = true;
	}

	function handleInputFocus() {
		isOpen = true;
	}

	function handleInputBlur(e: FocusEvent) {
		// Delay closing to allow click on dropdown items
		setTimeout(() => {
			const relatedTarget = e.relatedTarget as HTMLElement;
			if (!relatedTarget?.closest('.entity-picker-dropdown')) {
				isOpen = false;
			}
		}, 150);
	}

	function selectEntity(entity: EntitySummary) {
		entitySpatialStore.setSelectedEntity(entity.id);
		entitySpatialStore.setSearchQuery('');
		isOpen = false;
		inputElement?.blur();
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			isOpen = false;
			inputElement?.blur();
		}
	}

	function clearSelection() {
		entitySpatialStore.setSelectedEntity(null);
		entitySpatialStore.setSearchQuery('');
		inputElement?.focus();
	}
</script>

<div class="relative w-full">
	<div class="relative">
		<Input
			bind:ref={inputElement}
			type="text"
			placeholder={t('entity_spatial.search_entity')}
			value={displayValue}
			oninput={handleInputChange}
			onfocus={handleInputFocus}
			onblur={handleInputBlur}
			onkeydown={handleKeyDown}
			class="w-full pr-10"
		/>
		<!-- Search icon or clear button -->
		{#if currentEntity}
			<button
				type="button"
				class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
				onclick={clearSelection}
				aria-label="Clear selection"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<line x1="18" y1="6" x2="6" y2="18"></line>
					<line x1="6" y1="6" x2="18" y2="18"></line>
				</svg>
			</button>
		{:else}
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
			>
				<circle cx="11" cy="11" r="8"></circle>
				<line x1="21" y1="21" x2="16.65" y2="16.65"></line>
			</svg>
		{/if}
	</div>

	<!-- Dropdown list -->
	{#if isOpen && !currentEntity}
		<div
			class="entity-picker-dropdown absolute top-full left-0 right-0 z-50 mt-1 rounded-md border border-border bg-popover shadow-lg"
		>
			<ScrollArea class="h-[280px]">
				{#if filteredEntities.length === 0}
					<div class="p-4 text-center text-sm text-muted-foreground">
						{t('table.no_results')}
					</div>
				{:else}
					<div class="p-1">
						{#each filteredEntities.slice(0, 100) as entity (entity.id)}
							<button
								type="button"
								class="flex w-full items-center justify-between rounded-sm px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none"
								class:bg-accent={selectedEntityId === entity.id}
								onclick={() => selectEntity(entity)}
							>
								<span class="truncate font-medium">{entity.name}</span>
								<span class="ml-2 flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
									<span>{entity.articleCount} {t('entity_spatial.articles_count')}</span>
									{#if entity.locationCount > 0}
										<span class="text-muted-foreground/60">|</span>
										<span>{entity.locationCount} {t('entity_spatial.locations')}</span>
									{/if}
								</span>
							</button>
						{/each}
						{#if filteredEntities.length > 100}
							<div class="px-3 py-2 text-center text-xs text-muted-foreground">
								{t('entity_spatial.showing_first_100', [filteredEntities.length.toString()])}
							</div>
						{/if}
					</div>
				{/if}
			</ScrollArea>
		</div>
	{/if}
</div>

<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { entitySpatialStore } from '$lib/stores/entitySpatialStore.svelte.js';
	import { Tabs, TabsList, TabsTrigger } from '$lib/components/ui/tabs/index.js';
	import type { EntityType } from '$lib/types/entity-spatial.js';

	// Categories with their icons
	const categories: { type: EntityType; icon: string }[] = [
		{ type: 'Personnes', icon: 'user' },
		{ type: 'Événements', icon: 'calendar' },
		{ type: 'Sujets', icon: 'tag' },
		{ type: 'Organisations', icon: 'building' }
	];

	// Translation keys for entity types
	const typeTranslationKeys: Record<EntityType, string> = {
		Personnes: 'entity.persons',
		'Événements': 'entity.events',
		Sujets: 'entity.topics',
		Organisations: 'entity.organizations'
	};

	const selectedCategory = $derived(entitySpatialStore.selectedCategory);
	const categoryCounts = $derived(entitySpatialStore.categoryCounts);

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	function handleCategoryChange(value: string) {
		entitySpatialStore.setCategory(value as EntityType);
	}

	function getLabel(type: EntityType): string {
		// Access lang for reactivity
		void lang;
		return t(typeTranslationKeys[type]);
	}
</script>

<div class="w-full">
	<Tabs value={selectedCategory} onValueChange={handleCategoryChange}>
		<TabsList class="grid w-full grid-cols-4">
			{#each categories as { type, icon }}
				<TabsTrigger value={type} class="flex items-center gap-2 text-xs sm:text-sm">
					{#if icon === 'user'}
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
							class="hidden sm:block"
						>
							<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
							<circle cx="12" cy="7" r="4" />
						</svg>
					{:else if icon === 'calendar'}
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
							class="hidden sm:block"
						>
							<rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
							<line x1="16" y1="2" x2="16" y2="6" />
							<line x1="8" y1="2" x2="8" y2="6" />
							<line x1="3" y1="10" x2="21" y2="10" />
						</svg>
					{:else if icon === 'tag'}
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
							class="hidden sm:block"
						>
							<path
								d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"
							/>
							<line x1="7" y1="7" x2="7.01" y2="7" />
						</svg>
					{:else if icon === 'building'}
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
							class="hidden sm:block"
						>
							<rect x="4" y="2" width="16" height="20" rx="2" ry="2" />
							<path d="M9 22v-4h6v4" />
							<path d="M8 6h.01" />
							<path d="M16 6h.01" />
							<path d="M12 6h.01" />
							<path d="M12 10h.01" />
							<path d="M12 14h.01" />
							<path d="M16 10h.01" />
							<path d="M16 14h.01" />
							<path d="M8 10h.01" />
							<path d="M8 14h.01" />
						</svg>
					{/if}
					<span class="truncate">{getLabel(type)}</span>
					<span class="hidden text-xs text-muted-foreground lg:inline">
						({categoryCounts[type]})
					</span>
				</TabsTrigger>
			{/each}
		</TabsList>
	</Tabs>
</div>

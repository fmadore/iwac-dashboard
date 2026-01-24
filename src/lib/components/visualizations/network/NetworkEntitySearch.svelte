<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { ScrollArea } from '$lib/components/ui/scroll-area/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import type { GlobalNetworkNode, EntityType } from '$lib/types/network.js';
	import { Search, X, Users, Building2, Calendar, Tag, MapPin, Hash, FileText } from '@lucide/svelte';

	interface Props {
		nodes: GlobalNetworkNode[];
		selectedNode?: GlobalNetworkNode | null;
		onSelect?: (node: GlobalNetworkNode | null) => void;
		placeholder?: string;
	}

	let { nodes = [], selectedNode = null, onSelect, placeholder }: Props = $props();

	let isOpen = $state(false);
	let searchQuery = $state('');
	let inputElement = $state<HTMLInputElement | null>(null);

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	// Entity type icons
	const entityIcons: Record<EntityType, typeof Users> = {
		person: Users,
		organization: Building2,
		event: Calendar,
		subject: Tag,
		location: MapPin,
		topic: Hash,
		article: FileText,
		author: Users
	};

	// Entity type colors
	const entityColors: Record<EntityType, string> = {
		person: '#3b82f6',
		organization: '#8b5cf6',
		event: '#f97316',
		subject: '#22c55e',
		location: '#ec4899',
		topic: '#22c55e',
		article: '#3b82f6',
		author: '#3b82f6'
	};

	// Filter nodes based on search query
	const filteredNodes = $derived.by(() => {
		if (!searchQuery.trim()) {
			// Show top nodes by strength when no query
			return [...nodes].sort((a, b) => b.strength - a.strength).slice(0, 50);
		}
		const query = searchQuery.toLowerCase().trim();
		return nodes
			.filter((n) => n.label.toLowerCase().includes(query))
			.sort((a, b) => {
				// Prioritize exact start match
				const aStartsWith = a.label.toLowerCase().startsWith(query);
				const bStartsWith = b.label.toLowerCase().startsWith(query);
				if (aStartsWith && !bStartsWith) return -1;
				if (!aStartsWith && bStartsWith) return 1;
				return b.strength - a.strength;
			})
			.slice(0, 100);
	});

	// Get display value for input
	const displayValue = $derived.by(() => {
		if (selectedNode && !isOpen) {
			return selectedNode.label;
		}
		return searchQuery;
	});

	function handleInputChange(e: Event) {
		const target = e.target as HTMLInputElement;
		searchQuery = target.value;
		isOpen = true;
	}

	function handleInputFocus() {
		isOpen = true;
		// Select all text when focusing with a selected node
		if (selectedNode && inputElement) {
			inputElement.select();
		}
	}

	function handleInputBlur(e: FocusEvent) {
		// Delay closing to allow click on dropdown items
		setTimeout(() => {
			const relatedTarget = e.relatedTarget as HTMLElement;
			if (!relatedTarget?.closest('.network-search-dropdown')) {
				isOpen = false;
				// Reset search query if no selection made
				if (!selectedNode) {
					searchQuery = '';
				}
			}
		}, 150);
	}

	function selectNode(node: GlobalNetworkNode) {
		onSelect?.(node);
		searchQuery = '';
		isOpen = false;
		inputElement?.blur();
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			isOpen = false;
			searchQuery = '';
			inputElement?.blur();
		}
	}

	function clearSelection() {
		onSelect?.(null);
		searchQuery = '';
		inputElement?.focus();
	}
</script>

<div class="relative w-full">
	<div class="relative">
		<Input
			bind:ref={inputElement}
			type="text"
			placeholder={placeholder || t('network.search_entity')}
			value={displayValue}
			oninput={handleInputChange}
			onfocus={handleInputFocus}
			onblur={handleInputBlur}
			onkeydown={handleKeyDown}
			class="w-full pr-10"
		/>
		<!-- Search icon or clear button -->
		{#if selectedNode}
			<button
				type="button"
				class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
				onclick={clearSelection}
				aria-label={t('common.clear')}
			>
				<X class="h-4 w-4" />
			</button>
		{:else}
			<Search class="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
		{/if}
	</div>

	<!-- Dropdown list -->
	{#if isOpen}
		<div
			class="network-search-dropdown absolute top-full left-0 right-0 z-50 mt-1 rounded-md border border-border bg-popover shadow-lg"
		>
			<ScrollArea class="h-[320px]">
				{#if filteredNodes.length === 0}
					<div class="p-4 text-center text-sm text-muted-foreground">
						{t('table.no_results')}
					</div>
				{:else}
					<div class="p-1">
						{#if !searchQuery.trim()}
							<div class="px-3 py-1.5 text-xs font-medium text-muted-foreground">
								{t('network.top_entities')}
							</div>
						{/if}
						{#each filteredNodes as node (node.id)}
							{@const Icon = entityIcons[node.type]}
							{@const color = entityColors[node.type]}
							<button
								type="button"
								class="flex w-full items-center gap-2 rounded-sm px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none transition-colors"
								class:bg-accent={selectedNode?.id === node.id}
								onclick={() => selectNode(node)}
							>
								<span style="color: {color}" class="shrink-0">
									<Icon class="h-4 w-4" />
								</span>
								<span class="truncate flex-1 font-medium">{node.label}</span>
								<span class="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
									<Badge variant="outline" class="h-5 px-1.5 text-[10px]" style="border-color: {color}; color: {color}">
										{node.degree}
									</Badge>
								</span>
							</button>
						{/each}
						{#if filteredNodes.length >= 100}
							<div class="px-3 py-2 text-center text-xs text-muted-foreground">
								{t('network.showing_first_100')}
							</div>
						{/if}
					</div>
				{/if}
			</ScrollArea>
		</div>
	{/if}
</div>

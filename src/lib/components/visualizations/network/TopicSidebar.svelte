<script lang="ts">
	import { Input } from '$lib/components/ui/input/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import type { TopicNetworkTopicNode } from '$lib/types/topicNetwork.js';
	import { Search, Hash } from '@lucide/svelte';

	interface Props {
		topics: TopicNetworkTopicNode[];
		selectedTopicId?: string | null;
		onTopicSelect?: (topic: TopicNetworkTopicNode | null) => void;
	}

	let { topics = [], selectedTopicId = null, onTopicSelect }: Props = $props();

	let searchQuery = $state('');

	// Filter topics by search query
	const filteredTopics = $derived.by(() => {
		if (!searchQuery.trim()) return topics;
		const query = searchQuery.toLowerCase();
		return topics.filter(
			(topic) =>
				topic.label.toLowerCase().includes(query) ||
				topic.keywords.some((kw) => kw.toLowerCase().includes(query))
		);
	});

	function handleTopicClick(topic: TopicNetworkTopicNode) {
		if (selectedTopicId === topic.id) {
			// Deselect if clicking the same topic
			onTopicSelect?.(null);
		} else {
			onTopicSelect?.(topic);
		}
	}

	function formatKeywords(keywords: string[]): string {
		return keywords.slice(0, 3).join(', ');
	}
</script>

<div class="flex h-full flex-col overflow-hidden">
	<!-- Header -->
	<div class="shrink-0 border-b p-3">
		<h3 class="mb-2 text-sm font-semibold">{t('topic_network.topics')}</h3>
		<div class="relative">
			<Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
			<Input
				type="search"
				placeholder={t('topic_network.search_topics')}
				class="pl-8"
				bind:value={searchQuery}
			/>
		</div>
	</div>

	<!-- Topic List -->
	<div class="min-h-0 flex-1 overflow-y-auto">
		<div class="space-y-1 p-2">
			{#each filteredTopics as topic (topic.id)}
				{@const isSelected = selectedTopicId === topic.id}
				<button
					class="w-full rounded-md p-2 text-left transition-colors hover:bg-accent {isSelected
						? 'bg-accent'
						: ''}"
					onclick={() => handleTopicClick(topic)}
				>
					<div class="flex items-start justify-between gap-2">
						<div class="min-w-0 flex-1">
							<div class="flex items-center gap-1.5">
								<Hash class="h-3.5 w-3.5 shrink-0 text-green-500" />
								<span class="truncate text-sm font-medium">
									{topic.keywords[0] || topic.label}
								</span>
							</div>
							{#if topic.keywords.length > 1}
								<p class="mt-0.5 truncate text-xs text-muted-foreground">
									{formatKeywords(topic.keywords.slice(1))}
								</p>
							{/if}
						</div>
						<Badge variant="secondary" class="shrink-0 text-xs">
							{topic.count}
						</Badge>
					</div>
				</button>
			{/each}

			{#if filteredTopics.length === 0}
				<div class="py-4 text-center text-sm text-muted-foreground">
					{t('chart.no_data')}
				</div>
			{/if}
		</div>
	</div>

	<!-- Footer Stats -->
	<div class="shrink-0 border-t p-3">
		<div class="flex items-center justify-between text-xs text-muted-foreground">
			<span>{filteredTopics.length} {t('topic_network.topics').toLowerCase()}</span>
			{#if searchQuery}
				<button class="text-primary hover:underline" onclick={() => (searchQuery = '')}>
					{t('common.clear')}
				</button>
			{/if}
		</div>
	</div>
</div>

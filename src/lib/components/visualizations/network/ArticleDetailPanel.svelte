<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import type { TopicNetworkArticleNode } from '$lib/types/topicNetwork.js';
	import { X, ExternalLink, Calendar, Newspaper, MapPin, Percent } from '@lucide/svelte';

	interface Props {
		article: TopicNetworkArticleNode | null;
		onClose?: () => void;
	}

	let { article = null, onClose }: Props = $props();

	function formatDate(dateStr: string | undefined): string {
		if (!dateStr) return '-';
		try {
			const date = new Date(dateStr);
			return date.toLocaleDateString();
		} catch {
			return dateStr;
		}
	}

	function formatProbability(prob: number): string {
		return `${(prob * 100).toFixed(1)}%`;
	}
</script>

{#if article}
	<div
		class="absolute right-4 top-4 z-20 w-72 rounded-lg border bg-card/95 p-4 shadow-lg backdrop-blur-sm lg:w-80"
	>
		<!-- Header -->
		<div class="mb-3 flex items-start justify-between gap-2">
			<div class="min-w-0 flex-1">
				<h3 class="line-clamp-2 font-semibold leading-tight">{article.label}</h3>
			</div>
			<Button variant="ghost" size="sm" class="h-7 w-7 shrink-0 p-0" onclick={onClose}>
				<X class="h-4 w-4" />
			</Button>
		</div>

		<!-- Metadata -->
		<div class="space-y-2">
			{#if article.country}
				<div class="flex items-center gap-2 text-sm">
					<MapPin class="h-4 w-4 shrink-0 text-muted-foreground" />
					<span>{article.country}</span>
				</div>
			{/if}

			{#if article.newspaper}
				<div class="flex items-center gap-2 text-sm">
					<Newspaper class="h-4 w-4 shrink-0 text-muted-foreground" />
					<span class="truncate">{article.newspaper}</span>
				</div>
			{/if}

			{#if article.pubDate}
				<div class="flex items-center gap-2 text-sm">
					<Calendar class="h-4 w-4 shrink-0 text-muted-foreground" />
					<span>{formatDate(article.pubDate)}</span>
				</div>
			{/if}

			<!-- Topic Probability -->
			<div class="flex items-center gap-2 text-sm">
				<Percent class="h-4 w-4 shrink-0 text-muted-foreground" />
				<span>{t('topic_network.probability')}:</span>
				<Badge variant="secondary" class="ml-auto">
					{formatProbability(article.topicProb)}
				</Badge>
			</div>
		</div>

		<!-- View Article Button -->
		{#if article.url}
			<div class="mt-4">
				<a
					href={article.url}
					target="_blank"
					rel="noopener noreferrer"
					class="inline-flex h-9 w-full items-center justify-center rounded-md border border-input bg-background px-3 text-sm font-medium ring-offset-background transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
				>
					<ExternalLink class="mr-2 h-4 w-4" />
					{t('topic_network.view_article')}
				</a>
			</div>
		{/if}
	</div>
{/if}

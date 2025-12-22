<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Search } from '@lucide/svelte';

	// Props
	interface WordData {
		word: string;
		count: number;
	}

	interface TermData {
		term: string;
		total_occurrences: number;
		articles_with_term: number;
		unique_words: number;
		max_word_count: number;
		words: WordData[];
	}

	interface Props {
		data: TermData | null;
		maxDisplayed?: number;
	}

	let { data, maxDisplayed = 50 }: Props = $props();

	let searchQuery = $state('');
	let showAll = $state(false);

	// Filter words based on search
	const filteredWords = $derived.by(() => {
		if (!data?.words) return [];
		
		let words = data.words;
		
		// Filter by search
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			words = words.filter(w => w.word.toLowerCase().includes(query));
		}
		
		// Limit if not showing all
		if (!showAll && !searchQuery.trim()) {
			words = words.slice(0, maxDisplayed);
		}
		
		return words;
	});

	const hasMore = $derived((data?.words?.length || 0) > maxDisplayed);

	// Calculate bar width percentage
	function getBarWidth(count: number): number {
		if (!data?.max_word_count) return 0;
		return (count / data.max_word_count) * 100;
	}
</script>

<div class="space-y-4">
	<!-- Search -->
	<div class="relative">
		<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
		<Input
			type="text"
			placeholder={t('words.search_words')}
			bind:value={searchQuery}
			class="pl-10"
		/>
	</div>

	{#if filteredWords.length === 0}
		<div class="py-8 text-center text-muted-foreground">
			{t('words.no_matches')}
		</div>
	{:else}
		<!-- Words Table -->
		<div class="rounded-md border">
			<Table.Root>
				<Table.Header>
					<Table.Row>
						<Table.Head class="w-12">#</Table.Head>
						<Table.Head>{t('cooccurrence.word')}</Table.Head>
						<Table.Head class="w-32 text-right">{t('cooccurrence.count')}</Table.Head>
						<Table.Head class="w-48"></Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each filteredWords as word, i (word.word)}
						<Table.Row>
							<Table.Cell class="text-muted-foreground">{i + 1}</Table.Cell>
							<Table.Cell class="font-medium">{word.word}</Table.Cell>
							<Table.Cell class="text-right tabular-nums">{word.count.toLocaleString()}</Table.Cell>
							<Table.Cell>
								<div class="h-2 w-full rounded-full bg-muted">
									<div
										class="h-full rounded-full bg-primary"
										style="width: {getBarWidth(word.count)}%"
									></div>
								</div>
							</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
		</div>

		<!-- Show more/less -->
		{#if hasMore && !searchQuery.trim()}
			<div class="text-center">
				<button
					class="text-sm text-primary hover:underline"
					onclick={() => showAll = !showAll}
				>
					{showAll ? t('words.show_less') : t('words.show_more')}
				</button>
			</div>
		{/if}

		<!-- Count info -->
		<p class="text-center text-sm text-muted-foreground">
			{t('words.showing', [filteredWords.length.toString(), (data?.words?.length || 0).toString()])}
		</p>
	{/if}
</div>

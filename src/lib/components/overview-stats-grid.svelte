<script lang="ts">
	import { t } from '$lib/stores/translationStore.svelte.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import StatsCard from '$lib/components/stats-card.svelte';
	import type { OverviewSummary } from '$lib/stores/overviewStore.svelte.js';
	
	interface Props {
		summary: OverviewSummary;
	}
	
	let { summary }: Props = $props();
</script>

<div class="space-y-8">
	<!-- Primary Statistics -->
	<div>
		<h2 class="mb-4 text-xl font-semibold">{t('overview.primary_stats')}</h2>
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
			<StatsCard
				title={t('stats.total_items')}
				value={summary.total_items}
				description={t('stats.total_items_desc')}
			/>
			<StatsCard
				title={t('stats.countries')}
				value={summary.countries}
				description={t('stats.countries_desc')}
			/>
			<StatsCard
				title={t('stats.languages')}
				value={summary.languages}
				description={t('stats.languages_desc')}
			/>
			<StatsCard
				title={t('stats.types')}
				value={summary.types}
				description={t('stats.types_desc')}
			/>
		</div>
	</div>

	<!-- Content Statistics -->
	<div>
		<h2 class="mb-4 text-xl font-semibold">{t('overview.content_stats')}</h2>
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
			<StatsCard
				title={t('overview.total_words')}
				value={summary.total_words.toLocaleString()}
				description={t('overview.total_words_desc')}
			/>
			<StatsCard
				title={t('overview.total_pages')}
				value={summary.total_pages.toLocaleString()}
				description={t('overview.total_pages_desc')}
			/>
			<StatsCard
				title={t('overview.newspapers')}
				value={summary.newspapers}
				description={t('overview.newspapers_desc')}
			/>
			<StatsCard
				title={t('overview.audiovisual_duration')}
				value={(summary.audiovisual_duration || 0).toLocaleString()}
				description={t('overview.audiovisual_duration_desc')}
			/>
			<StatsCard
				title={t('overview.references')}
				value={(summary.references_count || 0).toLocaleString()}
				description={t('overview.references_desc')}
			/>
		</div>
	</div>
</div>

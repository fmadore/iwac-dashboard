<script lang="ts">
	import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
	import { Card, CardContent } from '$lib/components/ui/card/index.js';

	interface Props {
		articleCount: number;
		countries: string[];
		dateRange: {
			first: string;
			last: string;
		};
	}

	let { articleCount, countries, dateRange }: Props = $props();

	// Force reactivity on language change
	const lang = $derived(languageStore.current);

	// Format date range for display
	const formattedDateRange = $derived.by(() => {
		if (!dateRange.first && !dateRange.last) {
			return '-';
		}
		const firstYear = dateRange.first ? dateRange.first.substring(0, 4) : '?';
		const lastYear = dateRange.last ? dateRange.last.substring(0, 4) : '?';
		if (firstYear === lastYear) {
			return firstYear;
		}
		return `${firstYear} - ${lastYear}`;
	});
</script>

<div class="grid grid-cols-3 gap-4">
	<!-- Articles Card -->
	<Card class="bg-card">
		<CardContent class="p-4">
			<div class="flex flex-col items-center text-center">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="24"
					height="24"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="mb-2 text-muted-foreground"
				>
					<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
					<polyline points="14 2 14 8 20 8" />
					<line x1="16" y1="13" x2="8" y2="13" />
					<line x1="16" y1="17" x2="8" y2="17" />
					<polyline points="10 9 9 9 8 9" />
				</svg>
				<span class="text-2xl font-bold text-foreground">
					{articleCount.toLocaleString()}
				</span>
				<span class="text-xs text-muted-foreground">
					{t('entity_spatial.articles_count')}
				</span>
			</div>
		</CardContent>
	</Card>

	<!-- Countries Card -->
	<Card class="bg-card">
		<CardContent class="p-4">
			<div class="flex flex-col items-center text-center">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="24"
					height="24"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="mb-2 text-muted-foreground"
				>
					<circle cx="12" cy="12" r="10" />
					<line x1="2" y1="12" x2="22" y2="12" />
					<path
						d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"
					/>
				</svg>
				<span class="text-2xl font-bold text-foreground">
					{countries.length}
				</span>
				<span class="text-xs text-muted-foreground">
					{t('entity_spatial.countries_count')}
				</span>
			</div>
		</CardContent>
	</Card>

	<!-- Time Period Card -->
	<Card class="bg-card">
		<CardContent class="p-4">
			<div class="flex flex-col items-center text-center">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="24"
					height="24"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="mb-2 text-muted-foreground"
				>
					<rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
					<line x1="16" y1="2" x2="16" y2="6" />
					<line x1="8" y1="2" x2="8" y2="6" />
					<line x1="3" y1="10" x2="21" y2="10" />
				</svg>
				<span class="text-lg font-bold text-foreground">
					{formattedDateRange}
				</span>
				<span class="text-xs text-muted-foreground">
					{t('entity_spatial.time_period')}
				</span>
			</div>
		</CardContent>
	</Card>
</div>

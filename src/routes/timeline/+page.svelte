<script lang="ts">
	import { Card } from '$lib/components/ui/card/index.js';
	import { t } from '$lib/stores/translationStore.js';
</script>

<div class="space-y-6">
	<div>
		<h2 class="text-3xl font-bold tracking-tight">{$t('nav.timeline')}</h2>
		<p class="text-muted-foreground">Timeline visualization coming soon</p>
	</div>

	<Card class="p-6">
		<div class="text-center py-12">
			<h3 class="text-xl font-semibold mb-4">Timeline View</h3>
			<p class="text-muted-foreground">This feature is under development and will be available soon.</p>
		</div>
	</Card>
</div>
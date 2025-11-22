<script lang="ts">
	import { page } from '$app/state';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
</script>

<div class="container mx-auto flex min-h-[80vh] items-center justify-center p-4">
	<Card.Root class="w-full max-w-md border-destructive/20 shadow-lg">
		<Card.Header class="text-center">
			<Card.Title class="text-6xl font-bold text-destructive">
				{page.status}
			</Card.Title>
			<Card.Description class="mt-2 text-xl font-medium text-foreground">
				{#if page.status === 404}
					Page not found
				{:else if page.status === 500}
					Internal server error
				{:else}
					An error occurred
				{/if}
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-6 text-center">
			<p class="text-muted-foreground">
				{page.error?.message || 'Something went wrong'}
			</p>
			<div class="flex justify-center">
				<Button href="/" variant="default" size="lg">Go back home</Button>
			</div>
		</Card.Content>
	</Card.Root>
</div>

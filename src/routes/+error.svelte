<script lang="ts">
	import { page } from '$app/state';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
</script>

<div class="container mx-auto flex min-h-[80vh] items-center justify-center p-4">
	<Card.Root class="w-full max-w-md">
		<Card.Header>
			<Card.Title class="text-center text-4xl font-bold text-destructive">
				{page.status}
			</Card.Title>
			<Card.Description class="text-center text-lg">
				{#if page.status === 404}
					Page not found
				{:else if page.status === 500}
					Internal server error
				{:else}
					An error occurred
				{/if}
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-4">
			<p class="text-center text-muted-foreground">
				{page.error?.message || 'Something went wrong'}
			</p>
			<div class="flex justify-center">
				<Button href="/" variant="default">
					Go back home
				</Button>
			</div>
		</Card.Content>
	</Card.Root>
</div>

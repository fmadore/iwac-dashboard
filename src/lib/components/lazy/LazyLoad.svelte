<script lang="ts">
	import { browser } from '$app/environment';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import type { Snippet } from 'svelte';

	interface Props {
		/**
		 * Minimum height for the placeholder to prevent layout shift
		 */
		minHeight?: string;
		/**
		 * Threshold for intersection observer (0 = just entering viewport, 1 = fully visible)
		 */
		threshold?: number;
		/**
		 * Root margin for intersection observer (e.g., "100px" to load 100px before entering viewport)
		 */
		rootMargin?: string;
		/**
		 * CSS class for the container
		 */
		class?: string;
		/**
		 * Custom placeholder snippet
		 */
		placeholder?: Snippet;
		/**
		 * The content to render when visible
		 */
		children: Snippet;
	}

	let {
		minHeight = '200px',
		threshold = 0.1,
		rootMargin = '100px',
		class: className = '',
		placeholder,
		children
	}: Props = $props();

	let containerRef = $state<HTMLDivElement | null>(null);
	let isVisible = $state(false);
	let hasBeenVisible = $state(false);

	$effect(() => {
		if (!browser || !containerRef) return;

		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						isVisible = true;
						hasBeenVisible = true;
						// Once loaded, stop observing
						observer.unobserve(entry.target);
					}
				});
			},
			{
				threshold,
				rootMargin
			}
		);

		observer.observe(containerRef);

		return () => {
			observer.disconnect();
		};
	});
</script>

<div
	bind:this={containerRef}
	class={className}
	style:min-height={hasBeenVisible ? 'auto' : minHeight}
>
	{#if hasBeenVisible}
		{@render children()}
	{:else if placeholder}
		{@render placeholder()}
	{:else}
		<div class="flex h-full min-h-[inherit] w-full items-center justify-center">
			<Skeleton class="h-full min-h-[inherit] w-full rounded-lg" />
		</div>
	{/if}
</div>

<script lang="ts" generics="T extends Record<string, unknown>">
	import { browser } from '$app/environment';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import type { Component, Snippet } from 'svelte';

	type ComponentModule<P extends Record<string, unknown>> = {
		default: Component<P>;
	};

	interface Props<P extends Record<string, unknown>> {
		/**
		 * Dynamic import function for the component
		 * Example: () => import('./MyChart.svelte')
		 */
		loader: () => Promise<ComponentModule<P>>;
		/**
		 * Props to pass to the loaded component
		 */
		componentProps: P;
		/**
		 * Minimum height for loading placeholder
		 */
		minHeight?: string;
		/**
		 * Whether to lazy load on viewport intersection
		 */
		lazyOnViewport?: boolean;
		/**
		 * Threshold for intersection observer
		 */
		threshold?: number;
		/**
		 * Root margin for intersection observer
		 */
		rootMargin?: string;
		/**
		 * CSS class for the container
		 */
		class?: string;
		/**
		 * Custom loading placeholder
		 */
		placeholder?: Snippet;
		/**
		 * Error handler snippet
		 */
		onError?: Snippet<[Error]>;
	}

	let {
		loader,
		componentProps,
		minHeight = '200px',
		lazyOnViewport = true,
		threshold = 0.1,
		rootMargin = '100px',
		class: className = '',
		placeholder,
		onError
	}: Props<T> = $props();

	let containerRef = $state<HTMLDivElement | null>(null);
	let loadedComponent = $state<Component<T> | null>(null);
	let isLoading = $state(false);
	let error = $state<Error | null>(null);
	// Initialize based on lazyOnViewport prop - if false, should load immediately
	let shouldLoad = $state(false);

	// Set initial shouldLoad based on lazyOnViewport prop
	$effect(() => {
		if (!lazyOnViewport) {
			shouldLoad = true;
		}
	});

	async function loadComponent() {
		if (loadedComponent || isLoading) return;

		isLoading = true;
		error = null;

		try {
			const module = await loader();
			loadedComponent = module.default;
		} catch (e) {
			error = e instanceof Error ? e : new Error('Failed to load component');
			console.error('LazyComponent load error:', e);
		} finally {
			isLoading = false;
		}
	}

	// Intersection observer for viewport-based loading
	$effect(() => {
		if (!browser || !containerRef || !lazyOnViewport) return;

		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						shouldLoad = true;
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

	// Load component when shouldLoad becomes true
	$effect(() => {
		if (shouldLoad && browser) {
			loadComponent();
		}
	});
</script>

<div
	bind:this={containerRef}
	class={className}
	style:min-height={loadedComponent ? 'auto' : minHeight}
>
	{#if loadedComponent}
		{@const LoadedComp = loadedComponent}
		<LoadedComp {...componentProps} />
	{:else if error}
		{#if onError}
			{@render onError(error)}
		{:else}
			<div class="flex h-full min-h-[inherit] items-center justify-center">
				<p class="text-destructive">Failed to load component</p>
			</div>
		{/if}
	{:else if placeholder}
		{@render placeholder()}
	{:else}
		<div class="flex h-full min-h-[inherit] w-full items-center justify-center">
			<Skeleton class="h-full min-h-[inherit] w-full rounded-lg" />
		</div>
	{/if}
</div>

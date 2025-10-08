<script lang="ts">
	import * as Button from '$lib/components/ui/button/index.js';
	import { Maximize, Minimize } from '@lucide/svelte';
	import { languageStore } from '$lib/stores/translationStore.svelte.js';
	import { browser } from '$app/environment';

	let isFullscreen = $state(false);

	// Derive if Fullscreen API is supported
	const isSupported = $derived(
		browser &&
			!!(
				document.fullscreenEnabled ||
				(document as any).webkitFullscreenEnabled ||
				(document as any).mozFullScreenEnabled ||
				(document as any).msFullscreenEnabled
			)
	);

	// Reactive translations that update when language changes
	const enterFullscreenLabel = $derived(languageStore.t('fullscreen.enter'));
	const exitFullscreenLabel = $derived(languageStore.t('fullscreen.exit'));

	// Listen for fullscreen changes (including user pressing Esc)
	$effect(() => {
		if (!browser) return;

		const handleFullscreenChange = () => {
			isFullscreen = !!(
				document.fullscreenElement ||
				(document as any).webkitFullscreenElement ||
				(document as any).mozFullScreenElement ||
				(document as any).msFullScreenElement
			);
		};

		document.addEventListener('fullscreenchange', handleFullscreenChange);
		document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
		document.addEventListener('mozfullscreenchange', handleFullscreenChange);
		document.addEventListener('MSFullscreenChange', handleFullscreenChange);

		// Set initial state
		handleFullscreenChange();

		return () => {
			document.removeEventListener('fullscreenchange', handleFullscreenChange);
			document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
			document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
			document.removeEventListener('MSFullscreenChange', handleFullscreenChange);
		};
	});

	async function toggleFullscreen() {
		if (!isSupported) return;

		try {
			if (!isFullscreen) {
				// Request fullscreen on the document element
				const elem = document.documentElement;
				if (elem.requestFullscreen) {
					await elem.requestFullscreen();
				} else if ((elem as any).webkitRequestFullscreen) {
					await (elem as any).webkitRequestFullscreen();
				} else if ((elem as any).mozRequestFullScreen) {
					await (elem as any).mozRequestFullScreen();
				} else if ((elem as any).msRequestFullscreen) {
					await (elem as any).msRequestFullscreen();
				}
			} else {
				// Exit fullscreen
				if (document.exitFullscreen) {
					await document.exitFullscreen();
				} else if ((document as any).webkitExitFullscreen) {
					await (document as any).webkitExitFullscreen();
				} else if ((document as any).mozCancelFullScreen) {
					await (document as any).mozCancelFullScreen();
				} else if ((document as any).msExitFullscreen) {
					await (document as any).msExitFullscreen();
				}
			}
		} catch (error) {
			console.error('Error toggling fullscreen:', error);
		}
	}
</script>

{#if isSupported}
	<Button.Root
		variant="ghost"
		size="icon"
		onclick={toggleFullscreen}
		class="h-9 w-9"
		aria-label={isFullscreen ? exitFullscreenLabel : enterFullscreenLabel}
	>
		{#if isFullscreen}
			<Minimize class="h-4 w-4" />
		{:else}
			<Maximize class="h-4 w-4" />
		{/if}
		<span class="sr-only">{isFullscreen ? exitFullscreenLabel : enterFullscreenLabel}</span>
	</Button.Root>
{/if}

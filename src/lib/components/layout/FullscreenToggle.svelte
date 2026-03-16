<script lang="ts">
	import * as Button from '$lib/components/ui/button/index.js';
	import { Maximize, Minimize } from '@lucide/svelte';
	import { languageStore } from '$lib/stores/translationStore.svelte.js';
	import { browser } from '$app/environment';

	// Vendor-prefixed fullscreen API types
	interface VendorDocument extends Document {
		webkitFullscreenEnabled?: boolean;
		mozFullScreenEnabled?: boolean;
		msFullscreenEnabled?: boolean;
		webkitFullscreenElement?: Element | null;
		mozFullScreenElement?: Element | null;
		msFullScreenElement?: Element | null;
		webkitExitFullscreen?: () => Promise<void>;
		mozCancelFullScreen?: () => Promise<void>;
		msExitFullscreen?: () => Promise<void>;
	}

	interface VendorHTMLElement extends HTMLElement {
		webkitRequestFullscreen?: () => Promise<void>;
		mozRequestFullScreen?: () => Promise<void>;
		msRequestFullscreen?: () => Promise<void>;
	}

	let isFullscreen = $state(false);

	// Derive if Fullscreen API is supported
	const isSupported = $derived(
		browser &&
			!!(
				document.fullscreenEnabled ||
				(document as VendorDocument).webkitFullscreenEnabled ||
				(document as VendorDocument).mozFullScreenEnabled ||
				(document as VendorDocument).msFullscreenEnabled
			)
	);

	// Reactive translations that update when language changes
	const enterFullscreenLabel = $derived(languageStore.t('fullscreen.enter'));
	const exitFullscreenLabel = $derived(languageStore.t('fullscreen.exit'));

	// Listen for fullscreen changes (including user pressing Esc)
	$effect(() => {
		if (!browser) return;

		const handleFullscreenChange = () => {
			const doc = document as VendorDocument;
			isFullscreen = !!(
				doc.fullscreenElement ||
				doc.webkitFullscreenElement ||
				doc.mozFullScreenElement ||
				doc.msFullScreenElement
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
				const elem = document.documentElement as VendorHTMLElement;
				if (elem.requestFullscreen) {
					await elem.requestFullscreen();
				} else if (elem.webkitRequestFullscreen) {
					await elem.webkitRequestFullscreen();
				} else if (elem.mozRequestFullScreen) {
					await elem.mozRequestFullScreen();
				} else if (elem.msRequestFullscreen) {
					await elem.msRequestFullscreen();
				}
			} else {
				// Exit fullscreen
				const doc = document as VendorDocument;
				if (doc.exitFullscreen) {
					await doc.exitFullscreen();
				} else if (doc.webkitExitFullscreen) {
					await doc.webkitExitFullscreen();
				} else if (doc.mozCancelFullScreen) {
					await doc.mozCancelFullScreen();
				} else if (doc.msExitFullscreen) {
					await doc.msExitFullscreen();
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

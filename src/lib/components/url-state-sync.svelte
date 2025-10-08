<!--
  UrlStateSync Component
  
  Handles bidirectional synchronization between URL parameters and app state (language & theme).
  This component must be included in the root layout to work properly.
  
  It syncs:
  - Language: languageStore ↔ ?lang=en|fr
  - Theme: mode-watcher ↔ ?theme=light|dark|system
-->
<script lang="ts">
	import { browser } from '$app/environment';
	import { afterNavigate } from '$app/navigation';
	import { urlManager } from '$lib/stores/urlManager.svelte.js';
	import { languageStore } from '$lib/stores/translationStore.svelte.js';
	import { mode, setMode } from 'mode-watcher';
	import type { Language } from '$lib/stores/translationStore.svelte.js';
	import type { Theme } from '$lib/stores/urlManager.svelte.js';

	let isInitialized = $state(false);

	// Wait for router to be initialized using afterNavigate
	// This ensures replaceState is available before we try to sync state
	afterNavigate(() => {
		if (isInitialized) return;

		// Read initial state from URL
		const urlLang = urlManager.get('lang') as Language | undefined;
		if (urlLang && (urlLang === 'en' || urlLang === 'fr')) {
			languageStore.set(urlLang);
		}

		const urlTheme = urlManager.get('theme') as Theme | undefined;
		if (urlTheme && ['light', 'dark', 'system'].includes(urlTheme)) {
			setMode(urlTheme as 'light' | 'dark' | 'system');
		}

		// Mark as initialized and enable URL writing
		urlManager.enableUrlWriting();
		isInitialized = true;
	});

	// Watch for language changes and update URL
	// Note: We're tracking the previous value to detect changes,
	// which is a valid use case for state assignment in effects
	$effect(() => {
		if (!browser || !isInitialized) return;

		const currentLang = languageStore.current;
		// Write to URL when language changes
		urlManager.set('lang', currentLang);
	});

	// Watch for theme changes and update URL
	// Note: We're tracking the previous value to detect changes,
	// which is a valid use case for state assignment in effects
	$effect(() => {
		if (!browser || !isInitialized) return;

		const currentMode = mode.current;
		// Write to URL when theme changes
		if (currentMode) {
			urlManager.set('theme', currentMode as string);
		}
	});
</script>

<!-- Component that only contains effects must render something -->
<!-- This is a Svelte 5 requirement for hydration -->

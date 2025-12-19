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
	import { base } from '$app/paths';
	import { urlManager } from '$lib/stores/urlManager.svelte.js';
	import { languageStore } from '$lib/stores/translationStore.svelte.js';
	import { mode, setMode } from 'mode-watcher';
	import { isStorageAvailable } from '$lib/utils/storage-check.js';
	import type { Language } from '$lib/stores/translationStore.svelte.js';
	import type { Theme } from '$lib/stores/urlManager.svelte.js';

	let isInitialized = $state(false);

	function routeKeyFromPath(pathname: string): string {
		// Strip configured base (e.g. /iwac-dashboard) so routing works the same in dev and prod.
		const withoutBase = base && pathname.startsWith(base) ? pathname.slice(base.length) : pathname;
		const trimmed = withoutBase.replace(/^\/+/, '');
		return trimmed.split('/')[0] || '';
	}

	const allowlistByRoute: Record<string, Set<string>> = {
		'': new Set(['lang', 'theme']),
		countries: new Set(['lang', 'theme']),
		entities: new Set(['lang', 'theme']),
		references: new Set(['lang', 'theme']),
		topics: new Set(['lang', 'theme']),
		languages: new Set(['lang', 'theme', 'country', 'type']),
		timeline: new Set(['lang', 'theme', 'country', 'type']),
		categories: new Set(['lang', 'theme', 'country', 'yearMin', 'yearMax']),
		words: new Set(['lang', 'theme', 'view', 'country', 'year']),
		scary: new Set(['lang', 'theme', 'view', 'country'])
	};

	function pruneUrlParamsForRoute(pathname: string) {
		if (!browser || !isInitialized) return;

		const routeKey = routeKeyFromPath(pathname);
		const allowed = allowlistByRoute[routeKey] ?? allowlistByRoute[''];
		const keys = urlManager.keys();
		const toClear = keys.filter((k) => !allowed.has(k));
		if (toClear.length) {
			urlManager.clearMany(toClear as any);
		}
	}

	// Wait for router to be initialized using afterNavigate
	// This ensures replaceState is available before we try to sync state
	afterNavigate(({ to }) => {
		const pathname = to?.url?.pathname ?? window.location.pathname;
		if (isInitialized) {
			pruneUrlParamsForRoute(pathname);
			return;
		}

		// Read initial state from URL
		const urlLang = urlManager.get('lang') as Language | undefined;
		if (urlLang && (urlLang === 'en' || urlLang === 'fr')) {
			languageStore.set(urlLang);
		}

		const urlTheme = urlManager.get('theme') as Theme | undefined;
		if (urlTheme && ['light', 'dark', 'system'].includes(urlTheme)) {
			// Wrap in try-catch to handle storage errors in iframe contexts
			try {
				setMode(urlTheme as 'light' | 'dark' | 'system');
			} catch (e) {
				console.warn('Could not set theme mode (storage may be blocked):', e);
			}
		}

		// Mark as initialized and enable URL writing
		urlManager.enableUrlWriting();
		isInitialized = true;

		// Prune any stale params on initial load.
		pruneUrlParamsForRoute(pathname);
	});

	// Track previous values to avoid unnecessary URL writes
	let prevLang: Language | undefined = $state(undefined);
	let prevTheme: string | undefined = $state(undefined);

	// Watch for language changes and update URL
	$effect(() => {
		if (!browser || !isInitialized) return;

		const currentLang = languageStore.current;
		// Only write to URL when language actually changes
		if (currentLang !== prevLang) {
			prevLang = currentLang;
			urlManager.set('lang', currentLang);
		}
	});

	// Watch for theme changes and update URL
	$effect(() => {
		if (!browser || !isInitialized) return;

		const currentMode = mode.current;
		// Only write to URL when theme actually changes
		if (currentMode && currentMode !== prevTheme) {
			prevTheme = currentMode;
			urlManager.set('theme', currentMode as string);
		}
	});
</script>

<!-- Component that only contains effects must render something -->
<!-- This is a Svelte 5 requirement for hydration -->

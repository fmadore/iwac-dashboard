<script lang="ts">
	import { t } from '$lib/stores/translationStore.svelte.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { AppSidebar, FullscreenToggle } from '$lib/components/layout/index.js';
	import { LanguageToggle, ThemeToggle } from '$lib/components/controls/index.js';
	import { UrlStateSync, SafeModeWatcher } from '$lib/components/utilities/index.js';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import '../app.css';

	let { children } = $props();

	// Register service worker only in browser
	onMount(async () => {
		if (browser) {
			try {
				const { pwaInfo } = await import('virtual:pwa-info');
				if (pwaInfo) {
					const { registerSW } = await import('virtual:pwa-register');
					registerSW({
						immediate: true,
						onRegistered(r) {
							console.log('SW Registered:', r);
						},
						onRegisterError(error) {
							console.log('SW registration error', error);
						}
					});
				}
			} catch (e) {
				// PWA not available in dev mode or if disabled
				console.log('PWA not available:', e);
			}
		}
	});

	// Note: itemsStore is kept for legacy fallback support only
	// All data is now loaded from pre-computed JSON files
	// $effect(() => {
	// 	itemsStore.loadItems();
	// });
</script>

<SafeModeWatcher />
<UrlStateSync />
<Sidebar.Provider>
	<AppSidebar />
	<Sidebar.Inset class="min-h-screen w-full overflow-hidden">
		<header
			class="sticky top-0 z-10 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6"
		>
			<Sidebar.Trigger class="-ml-1" />
			<h1 class="text-xl font-semibold">{t('app.title')}</h1>
			<div class="ml-auto flex items-center gap-2">
				<FullscreenToggle />
				<ThemeToggle />
				<LanguageToggle />
			</div>
		</header>
		<main class="w-full min-w-0 flex-1 overflow-x-hidden overflow-y-auto p-4 md:p-6">
			{@render children?.()}
		</main>
	</Sidebar.Inset>
</Sidebar.Provider>

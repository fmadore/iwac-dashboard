<script lang="ts">
	import { itemsStore } from '$lib/stores/itemsStore.svelte.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import LanguageToggle from '$lib/components/language-toggle.svelte';
	import ThemeToggle from '$lib/components/theme-toggle.svelte';
	import FullscreenToggle from '$lib/components/fullscreen-toggle.svelte';
	import UrlStateSync from '$lib/components/url-state-sync.svelte';
	import { ModeWatcher } from 'mode-watcher';
	import '../app.css';

	let { children } = $props();

	// Note: itemsStore is kept for legacy fallback support only
	// All data is now loaded from pre-computed JSON files
	// $effect(() => {
	// 	itemsStore.loadItems();
	// });
</script>

<ModeWatcher />
<UrlStateSync />
<Sidebar.Provider>
	<AppSidebar />
	<Sidebar.Inset>
		<header class="sticky top-0 z-10 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6">
			<Sidebar.Trigger class="-ml-1" />
			<h1 class="text-xl font-semibold">{t('app.title')}</h1>
			<div class="ml-auto flex items-center gap-2">
				<FullscreenToggle />
				<ThemeToggle />
				<LanguageToggle />
			</div>
		</header>
		<main class="flex-1 overflow-auto p-4 md:p-6">
			{@render children?.()}
		</main>
	</Sidebar.Inset>
</Sidebar.Provider>

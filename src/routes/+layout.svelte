<script lang="ts">
	import { itemsStore } from '$lib/stores/itemsStore.js';
	import { t } from '$lib/stores/translationStore.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import LanguageToggle from '$lib/components/language-toggle.svelte';
	import ThemeToggle from '$lib/components/theme-toggle.svelte';
	import { ModeWatcher } from 'mode-watcher';
	import '../app.css';

	let { children } = $props();

	$effect(() => {
		itemsStore.loadItems();
	});
</script>

<div class="flex h-screen">
	<ModeWatcher />
	<Sidebar.Provider>
		<AppSidebar />
		<Sidebar.Inset class="flex-1">
			<header class="sticky top-0 flex h-16 items-center gap-4 border-b bg-background px-6">
				<h1 class="text-xl font-semibold">{$t('app.title')}</h1>
				<div class="ml-auto flex items-center gap-2">
					<ThemeToggle />
					<LanguageToggle />
				</div>
			</header>
			<main class="flex-1 p-6 overflow-auto">
				{@render children?.()}
			</main>
		</Sidebar.Inset>
	</Sidebar.Provider>
</div>

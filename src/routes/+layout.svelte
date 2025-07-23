<script lang="ts">
	import { onMount } from 'svelte';
	import { itemsStore } from '$lib/stores/itemsStore.js';
	import { t } from '$lib/stores/translationStore.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import LanguageToggle from '$lib/components/language-toggle.svelte';
	import '../app.css';

	onMount(() => {
		itemsStore.loadItems();
	});
</script>

<div class="flex h-screen">
	<Sidebar.Provider>
		<AppSidebar />
		<Sidebar.Inset class="flex-1">
			<header class="sticky top-0 flex h-16 items-center gap-4 border-b bg-background px-6">
				<h1 class="text-xl font-semibold">{$t('app.title')}</h1>
				<div class="ml-auto">
					<LanguageToggle />
				</div>
			</header>
			<main class="flex-1 p-6 overflow-auto">
				<slot />
			</main>
		</Sidebar.Inset>
	</Sidebar.Provider>
</div>

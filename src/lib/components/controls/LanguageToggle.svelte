<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { languageStore, type Language } from '$lib/stores/translationStore.svelte.js';
	import { Globe } from '@lucide/svelte';

	function toggleLanguage() {
		languageStore.set(languageStore.current === 'en' ? 'fr' : 'en');
	}
</script>

<Button variant="outline" size="sm" onclick={toggleLanguage} class="gap-2">
	<Globe class="h-4 w-4" />
	{languageStore.current === 'en' ? 'FR' : 'EN'}
</Button>

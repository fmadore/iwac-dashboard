<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { languageStore, type Language } from '$lib/stores/translationStore.js';
	import { Globe } from 'lucide-svelte';

	function toggleLanguage() {
		languageStore.update((current: Language) => (current === 'en' ? 'fr' : 'en'));
	}
</script>

<Button variant="outline" size="sm" on:click={toggleLanguage} class="gap-2">
	<Globe class="h-4 w-4" />
	{$languageStore === 'en' ? 'FR' : 'EN'}
</Button>

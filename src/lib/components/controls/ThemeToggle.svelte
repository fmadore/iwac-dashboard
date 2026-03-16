<script lang="ts">
	import * as Button from '$lib/components/ui/button/index.js';
	import { Moon, Sun } from '@lucide/svelte';
	import { toggleMode } from 'mode-watcher';
	import { t } from '$lib/stores/translationStore.svelte.js';

	function handleToggle() {
		try {
			toggleMode();
		} catch (e) {
			// Storage may be blocked in iframe contexts
			console.warn('Could not toggle theme (storage may be blocked):', e);
		}
	}
</script>

<Button.Root
	variant="ghost"
	size="icon"
	onclick={handleToggle}
	class="h-9 w-9"
	aria-label={t('a11y.toggle_theme')}
>
	<Sun class="h-4 w-4 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
	<Moon class="absolute h-4 w-4 scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
	<span class="sr-only">{t('a11y.toggle_theme')}</span>
</Button.Root>

<script lang="ts">
	import * as Button from '$lib/components/ui/button/index.js';
	import { Moon, Sun } from '@lucide/svelte';
	import { mode, toggleMode } from 'mode-watcher';
</script>

<Button.Root
	variant="ghost"
	size="icon"
	onclick={toggleMode}
	class="h-9 w-9"
	aria-label="Toggle theme"
>
	<Sun class="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
	<Moon class="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
	<span class="sr-only">Toggle theme</span>
</Button.Root>
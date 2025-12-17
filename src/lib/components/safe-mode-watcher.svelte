<!--
  SafeModeWatcher Component
  
  Wrapper around mode-watcher that handles cross-origin iframe embedding scenarios
  where localStorage access may be blocked by tracking prevention.
-->
<script lang="ts">
	import { ModeWatcher } from 'mode-watcher';
	import { browser } from '$app/environment';
	import { isStorageAvailable, isInIframe } from '$lib/utils/storage-check.js';

	// Check storage availability
	const storageOk = browser ? isStorageAvailable() : true;
	const inIframe = browser ? isInIframe() : false;

	// If we're in an iframe with blocked storage, we still render ModeWatcher
	// but it will use system preferences since localStorage is unavailable.
	// mode-watcher internally handles the noopStorage fallback.

	if (browser && !storageOk && inIframe) {
		console.warn(
			'IWAC Dashboard: Running in iframe with blocked localStorage. ' +
				"Theme preferences will use system defaults and won't persist."
		);
	}
</script>

<!--
  ModeWatcher will internally fall back to system preferences when localStorage
  is unavailable. The key is that it doesn't throw - it just uses noopStorage.
  
  The actual error occurs during Svelte's hydration when the injected script
  tries to access localStorage. Using disableHeadScriptInjection prevents this.
-->
{#if storageOk}
	<ModeWatcher />
{:else}
	<!-- In restricted environments, disable head script injection to prevent errors -->
	<ModeWatcher disableHeadScriptInjection={true} defaultMode="system" />
{/if}

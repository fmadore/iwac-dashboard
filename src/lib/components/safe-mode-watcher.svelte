<!--
  SafeModeWatcher Component
  
  Wrapper around mode-watcher for cross-origin iframe embedding.
  
  The localStorage polyfill in app.html handles blocked storage by replacing
  it with an in-memory implementation BEFORE this component loads.
  
  We still use disableHeadScriptInjection to prevent potential hydration
  issues with the inline FOUC-prevention script.
-->
<script lang="ts">
	import { ModeWatcher } from 'mode-watcher';
</script>

<ModeWatcher disableHeadScriptInjection={true} defaultMode="system" />

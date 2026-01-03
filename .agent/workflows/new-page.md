---
description: Create a new page/route in the dashboard
---

# Create New Page

## Steps

1. Create the route directory and files:
   - `src/routes/[page-name]/+page.svelte` - Page component
   - `src/routes/[page-name]/+page.ts` - Page configuration

2. Create `+page.ts` with static prerendering:
   ```typescript
   export const prerender = true;
   ```

3. Create `+page.svelte` using this template:
   ```svelte
   <script lang="ts">
     import { Card } from '$lib/components/ui/card/index.js';
     import { Skeleton } from '$lib/components/ui/skeleton/index.js';
     import { t } from '$lib/stores/translationStore.svelte.js';
     import { base } from '$app/paths';
     
     // State
     let loading = $state(true);
     let error = $state<string | null>(null);
     let data = $state<YourDataType | null>(null);
     
     // Load data
     async function loadData() {
       try {
         const response = await fetch(`${base}/data/your-data.json`);
         if (!response.ok) throw new Error(`HTTP ${response.status}`);
         data = await response.json();
       } catch (e) {
         error = e instanceof Error ? e.message : 'Failed to load';
       } finally {
         loading = false;
       }
     }
     
     $effect(() => {
       loadData();
     });
   </script>
   
   <div class="space-y-6">
     <div>
       <h2 class="text-3xl font-bold tracking-tight">{t('nav.page_title')}</h2>
       <p class="text-muted-foreground">{t('page.description')}</p>
     </div>
     
     {#if loading}
       <Skeleton class="h-64 w-full" />
     {:else if error}
       <Card class="p-6">
         <p class="text-destructive">{t('common.error')}: {error}</p>
       </Card>
     {:else if data}
       <!-- Your content here -->
     {/if}
   </div>
   ```

4. Add translations to `src/lib/stores/translationStore.svelte.ts`:
   ```typescript
   // In both 'en' and 'fr' objects
   'nav.page_title': 'Page Title',
   'page.description': 'Page description text',
   ```

5. Add navigation link to `src/lib/components/app-sidebar.svelte`

6. Run type check:
   ```bash
   npm run check
   ```

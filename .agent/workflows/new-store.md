---
description: Create a new Svelte 5 store
---

# Create New Store

## Store Pattern (Class-based with Runes)

1. Create the store file in `src/lib/stores/`:
   - Use naming convention: `myStore.svelte.ts`

2. Template:
   ```typescript
   import { base } from '$app/paths';
   
   interface MyDataItem {
     id: string;
     name: string;
     value: number;
   }
   
   class MyStore {
     // State
     items = $state<MyDataItem[]>([]);
     loading = $state(false);
     error = $state<string | null>(null);
     selectedId = $state<string | null>(null);
     
     // Computed/getters
     get totalCount(): number {
       return this.items.length;
     }
     
     get selectedItem(): MyDataItem | undefined {
       return this.items.find(item => item.id === this.selectedId);
     }
     
     get sortedItems(): MyDataItem[] {
       return [...this.items].sort((a, b) => b.value - a.value);
     }
     
     // Actions
     async load() {
       if (this.items.length > 0) return; // Already loaded
       
       this.loading = true;
       this.error = null;
       
       try {
         const response = await fetch(`${base}/data/my-data.json`);
         if (!response.ok) {
           throw new Error(`HTTP ${response.status}`);
         }
         this.items = await response.json();
       } catch (e) {
         this.error = e instanceof Error ? e.message : 'Failed to load';
       } finally {
         this.loading = false;
       }
     }
     
     select(id: string | null) {
       this.selectedId = id;
     }
     
     reset() {
       this.items = [];
       this.loading = false;
       this.error = null;
       this.selectedId = null;
     }
   }
   
   export const myStore = new MyStore();
   ```

3. Export from `src/lib/stores/index.ts` if using barrel exports

4. Usage in components:
   ```svelte
   <script lang="ts">
     import { myStore } from '$lib/stores/myStore.svelte.js';
     
     // Derived values for reactivity
     const items = $derived(myStore.items);
     const loading = $derived(myStore.loading);
     const error = $derived(myStore.error);
     
     $effect(() => {
       myStore.load();
     });
   </script>
   ```

## Key Points

- Use `$state<T>()` for all mutable state
- Use getters for computed values (automatically reactive)
- Export a singleton instance
- Don't use `$derived` inside the store class (use getters instead)
- File extension must be `.svelte.ts` to use runes

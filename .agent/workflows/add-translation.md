---
description: Add new translations for i18n support
---

# Add Translations

## Steps

1. Open `src/lib/stores/translationStore.svelte.ts`

2. Add translations to both language objects:
   ```typescript
   export const translations = {
     en: {
       // ... existing translations
       'my.new.key': 'English text',
       'my.parameterized.key': 'Hello {0}, you have {1} items',
     },
     fr: {
       // ... existing translations
       'my.new.key': 'Texte français',
       'my.parameterized.key': 'Bonjour {0}, vous avez {1} éléments',
     }
   } as const;
   ```

3. Use in components:
   ```svelte
   <script>
     import { t } from '$lib/stores/translationStore.svelte.js';
   </script>
   
   <!-- Simple -->
   <p>{t('my.new.key')}</p>
   
   <!-- With parameters -->
   <p>{t('my.parameterized.key', ['User', 5])}</p>
   ```

## Naming Conventions

Use dot notation with semantic prefixes:
- `nav.*` - Navigation items
- `stats.*` - Statistics labels
- `chart.*` - Chart labels and titles
- `table.*` - Table headers and messages
- `common.*` - Shared UI text (loading, error, etc.)
- `filters.*` - Filter controls
- `entity.*` - Entity type names
- `type.*` - Document type names
- `[page].*` - Page-specific text (e.g., `timeline.*`, `words.*`)

## Reactive Charts

For charts that need to update on language change:
```svelte
<script>
  import { languageStore, t } from '$lib/stores/translationStore.svelte.js';
  
  const chartKey = $derived(`chart-${languageStore.current}`);
  const labels = $derived({
    title: t('chart.title'),
    tooltip: t('chart.tooltip')
  });
</script>

{#key chartKey}
  <Chart {labels} />
{/key}
```

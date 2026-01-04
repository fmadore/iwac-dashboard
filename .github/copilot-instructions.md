# IWAC Dashboard - Copilot Instructions

## Overview
Static SvelteKit dashboard for the Islam West Africa Collection (IWAC), fully prerendered.
**Stack:** Svelte 5 (Runes), SvelteKit (Static), shadcn-svelte, Tailwind v4, LayerChart/D3, Python (Data Gen).

## Critical Rules

### 1. Svelte 5 (Runes Mode) Only
**NEVER use Svelte 4 syntax.** Use `$state`, `$derived`, `$props`, `$effect`.
```svelte
<script>
	let { count = 0 } = $props();
	const doubled = $derived(count * 2);
	let items = $state([]);
</script>
```

### 2. UI & Styling
- **Components:** Use `shadcn-svelte` from `$lib/components/ui`.
- **Theming:** Use CSS variables from `src/app.css` (e.g., `var(--chart-1)`, `--foreground`). **Never hardcode colors.**

#### Theme Variables (src/app.css):
`--background`, `--foreground`, `--card`, `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--border`, `--input`, `--ring`, `--chart-1` to `--chart-5`, `--country-color-*`.

### 3. Data Flow (Python → JSON → Svelte)
- Python scripts (`scripts/`) generate static JSON in `static/data/`.
- **Loading:** Use `fetch` in `+page.ts` `load` functions for preloading.
- **Performance:**
  - **Brotli:** Enabled in config.
  - **Lazy Loading:** Use `LazyLoad` (viewport) or `LazyComponent` (dynamic import) from `$lib/components/lazy`.
  - **Fetching:** Use `fetchData` / `prefetchData` from `$lib/utils/dataFetcher.ts`.

### 4. Visualizations
- **Charts:** Use LayerChart (preferred) or D3.js. Avoid ECharts for new components.
- **Maps:** Leaflet via `src/lib/components/world-map`. Use `mapDataStore`.

### 5. Internationalization (i18n)
- **Bilingual (EN/FR):** All text must use `$t('key')` from `$lib/stores/translationStore.ts`.
- **Reactivity:** Charts must update on language change (use `$derived` with `$languageStore`).

### 6. Constraints
- **Static Only:** `export const prerender = true;` on all pages.
- **No Server Routes:** No `+server.ts`.
- **Strict Types:** Maintain TypeScript safety.

## Project Structure

```
src/
├── lib/
│   ├── components/
│   │   ├── ui/                    # shadcn-svelte components
│   │   ├── charts/                # Chart components (LayerChart/D3)
│   │   ├── facets/                # Faceted visualization components
│   │   ├── lazy/                  # Lazy loading components
│   │   ├── app-sidebar.svelte     # Main navigation sidebar
│   │   └── ...
│   ├── stores/
│   │   ├── itemsStore.ts          # Global data store
│   │   └── translationStore.ts    # i18n store
│   └── utils/
│       └── dataFetcher.ts         # Data loading utilities
├── routes/
│   ├── +layout.svelte             # Root layout
│   ├── +page.svelte               # Overview
│   └── ...
scripts/                           # Python data generation scripts
static/data/                       # Static JSON files
```

## Tool Usage
- **Svelte MCP:** ALWAYS use for Svelte code. Workflow: `list-sections` -> `get-documentation` -> Write -> `svelte-autofixer`.
- **Context7 MCP:** Use for shadcn, LayerChart, D3 docs.

## Validation Checklist
- ✅ Validated with `svelte-autofixer`
- ✅ Used Svelte 5 Runes
- ✅ Used shadcn-svelte & CSS variables
- ✅ Fully translatable (EN/FR)
- ✅ Static data loading
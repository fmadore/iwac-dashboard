# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static SvelteKit dashboard for the Islam West Africa Collection (IWAC) database. Fully prerendered with no server runtime.

**Stack:** Svelte 5 (Runes), SvelteKit 2 (adapter-static), shadcn-svelte, Tailwind CSS v4, LayerChart/D3/ECharts, Python data generation.

## Commands

```bash
npm run dev              # Development server
npm run build            # Production build (static)
npm run preview          # Preview production build
npm run check            # TypeScript/Svelte type checking
npm run lint             # ESLint + Prettier check
npm run test:unit        # Vitest unit tests
npm run test:e2e         # Playwright E2E tests
npm run test             # Run all tests
```

### Data Generation (Python)

```bash
cd scripts
pip install -r requirements.txt
python generate_overview_stats.py    # Run individual generators
```

### IWAC Dataset Skill

Use the `iwac-dataset` skill when creating new visualizations that require fetching data from Hugging Face. This skill provides efficient access to the IWAC dataset (`fmadore/islam-west-africa-collection`) and helps generate Python scripts for new data pipelines.

## Architecture

### Data Flow

```
Python Scripts (scripts/generate_*.py)
    → Static JSON (static/data/)
    → SvelteKit Page Load (+page.ts with prerender=true)
    → Components (via fetch or dataFetcher.ts)
```

All data is pre-computed at build time. No API calls or database queries at runtime.

### Key Directories

- `src/lib/stores/` - Svelte 5 rune-based stores (translationStore, overviewStore, mapDataStore, urlManager)
- `src/lib/components/ui/` - shadcn-svelte components (DO NOT MODIFY)
- `src/lib/components/visualizations/` - D3, LayerChart, network, and map components
- `src/lib/utils/dataFetcher.ts` - Data fetching with in-memory caching
- `static/data/` - Pre-computed JSON data files

### Import Pattern

Use barrel exports with `/index.js` suffix:

```typescript
import { AppSidebar } from '$lib/components/layout/index.js';
import { TimelineChart } from '$lib/components/visualizations/charts/d3/index.js';
import { Bar, PieChart } from '$lib/components/visualizations/charts/layerchart/index.js';
```

## Critical Rules

### 1. Svelte 5 Runes Only

Never use Svelte 4 syntax. Always use `$state`, `$derived`, `$props`, `$effect`:

```svelte
<script>
    let { count = 0 } = $props();
    const doubled = $derived(count * 2);
    let items = $state([]);
</script>
```

### 2. Theming

Use CSS variables from `src/app.css`. Never hardcode colors:

```svelte
<!-- Correct -->
<div class="bg-background text-foreground border-border">

<!-- Wrong -->
<div class="bg-blue-500 text-white">
```

Theme variables: `--background`, `--foreground`, `--card`, `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--border`, `--chart-1` to `--chart-5`, `--country-color-*`.

### 3. Internationalization

All text must use the translation function. Bilingual EN/FR support required:

```svelte
<script>
    import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
</script>

{t('chart.top_countries')}
{t('chart.languages_in_type', ['Press Article'])}  <!-- with parameters -->
```

Charts must update reactively on language change (use `$derived` with `languageStore.current`).

### 4. Static Constraints

- All pages: `export const prerender = true;`
- No `+server.ts` files
- Data loading via `fetch()` to `/data/*.json` in `+page.ts` load functions

### 5. Visualizations

- **Preferred:** LayerChart for new charts
- **Custom:** D3.js when needed
- **Avoid:** ECharts for new components

## Testing

- Unit tests: `*.{test,spec}.{js,ts}` (Vitest with browser environment for `.svelte` files)
- E2E tests: `e2e/` directory (Playwright)
- Svelte component tests use `vitest-browser-svelte`

## Deployment

Static site deployed to GitHub Pages at `/iwac-dashboard/` subpath. Base path handled via `$app/paths`.

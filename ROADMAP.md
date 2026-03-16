# IWAC Dashboard — Refactoring & Cleanup Roadmap

> Generated 2026-03-16. Updated after implementation rounds 1 & 2.

## Completed Work

### Phase 1: Theme System & CSS Consistency ✅

- **1.1** Added 9 `--entity-*` CSS variables (light + dark) to `app.css`
- **1.2** Created `src/lib/constants/theme.ts` with shared `FALLBACK_COLORS`, `resolveCSSColor()` (canvas pixel readback for OKLCH→hex), entity/edge color maps
- **1.3** Unified MapLibre `theme.ts` with shared constants — single source of truth
- **1.4** Updated `NetworkGraph.svelte`, `NetworkEntitySearch.svelte`, `BarChartRace.svelte`, `ChoroplethLayer.svelte` to use CSS variables and shared constants
- **Bug fix:** Fixed `#NaN` color parsing — modern Chrome preserves OKLCH in `getComputedStyle` and canvas `fillStyle`; switched to `getImageData` pixel readback which always returns sRGB

### Phase 2: Shared Utilities & DRY Refactoring ✅

- **2.1** Created `src/lib/utils/chartUtils.ts` — axis rotation, tick calculation, bottom padding, tooltip parsing, label formatting (deduplicated from Bar.svelte + StackedBarChart.svelte)
- **2.2** Created `src/lib/hooks/usePagination.svelte.ts` — shared pagination composable (extracted from LocationArticlePanel + MapLocationSheet)
- **2.3** Created `src/lib/components/ui/pagination-controls/PaginationControls.svelte` — shared pagination UI with smart ellipsis
- **2.4** Created `src/lib/utils/formatDate.ts` — shared locale-aware date formatting (extracted from 2 components)

### Phase 3: Dead Code Removal ✅

- **3.1** Removed `LazyLoad.svelte`, `LazyComponent.svelte`, and barrel export (unused)
- **3.2** Removed 4 unused type interfaces from `types/index.ts`

### Phase 4: Data Fetching Consistency ✅

- **4.1** Migrated 17 page components from raw `fetch()` to `fetchData<T>()` with caching
- Note: `+page.ts` load functions kept using SvelteKit's enhanced `fetch` (required for prerendering)

### Phase 5: i18n & Accessibility ✅

- **5.1** Added 8 `a11y.*` translation keys (EN + FR)
- **5.2** Translated hardcoded `aria-label` in ThemeToggle and entities-table
- **5.3** Added `pagination.*` translation keys for shared pagination component

### Phase 6: CI ✅ (Partial)

- **6.1** Added 10 missing Python scripts to `generate-data.yml` workflow

### Phase 8: Testing ✅

- **194 unit tests** across 6 test files (all passing):
  - `chartUtils.test.ts` — 68 tests (axis, tooltip, label formatting)
  - `theme.test.ts` — 29 tests (constants, color resolution, NaN regression)
  - `dataFetcher.test.ts` — 32 tests (cache, retry, pagination, prefetch)
  - `translationStore.test.ts` — 37 tests (lookup, params, language, parity)
  - `usePagination.test.ts` — 18 tests (pages, navigation, bounds)
  - `formatDate.test.ts` — 10 tests (locale, null/invalid input)

---

## Remaining Work

### Phase 2b: ResizeObserver Composable
**Priority: Medium** | **Effort: 30m** | **Impact: Medium**

6 components use ResizeObserver with inconsistent patterns ($effect vs onMount vs function-based). Create a shared `useResizeObserver.svelte.ts` composable.

**Components to update:** Bar.svelte, BarChartRace.svelte, CooccurrenceMatrix.svelte, TimelineChart.svelte, SemanticMapCanvas.svelte, Wordcloud.svelte

### Phase 3b: Remaining Dead Code
**Priority: Low** | **Effort: 10m** | **Impact: Low**

- `src/routes/newspaper-coverage/+page.svelte` uses hardcoded `placeholderData`
- `e2e/demo.test.ts` is a minimal placeholder test

### Phase 6b: Python Script Consistency
**Priority: Medium** | **Effort: 2h** | **Impact: Medium**

9 of 17 generator scripts don't use `iwac_utils.py` shared utilities. Migrate them for consistency.

### Phase 7: Type Safety
**Priority: Medium** | **Effort: 1h** | **Impact: Medium**

- Remove remaining `any` types in tooltip handlers
- Type NetworkGraph `sigmaInstance` and `graphInstance` with proper Sigma.js imports

### Phase 9: Component Decomposition
**Priority: Low** | **Effort: 4h+** | **Impact: Medium**

Large components that could be split:

| Component | Lines | Candidates for Extraction |
|-----------|-------|--------------------------|
| NetworkGraph.svelte | 1090 | Tooltip logic, legend, layout init |
| BarChartRace.svelte | 599 | Animation setup, scale calculations |
| SemanticMapCanvas.svelte | 540 | UMAP init, rendering pipeline |
| CooccurrenceMatrix.svelte | 456 | Heatmap rendering, interactions |

### Phase 10: Test Expansion
**Priority: Medium** | **Effort: 2h** | **Impact: High**

Current coverage: ~13% of JS/TS code. Priority additions:
- `urlManager.svelte.ts` — URL sync, state mutations (35-50 tests)
- `useFilters.svelte.ts` — filter logic, mutual exclusivity (30-45 tests)
- `storage-check.ts` — cross-origin safety (15-25 tests)
- E2E tests for key user journeys (chart rendering, filter interactions)

---

## Summary

| Phase | Status | Tests Added |
|-------|--------|-------------|
| 1. Theme/CSS | ✅ Done | 29 |
| 2. Shared Utils | ✅ Done | 96 |
| 3. Dead Code | ✅ Done | — |
| 4. Data Fetching | ✅ Done | 32 |
| 5. i18n | ✅ Done | 37 |
| 6. CI | ✅ Partial | — |
| 7. Types | Remaining | — |
| 8. Testing | ✅ Done | 194 total |
| 9. Decomposition | Remaining | — |
| 10. Test Expansion | Remaining | — |

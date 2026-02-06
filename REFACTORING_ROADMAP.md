# IWAC Dashboard — Refactoring Roadmap

> Generated from comprehensive code review (Feb 2026).
> Overall assessment: **B+** — production-ready with clear improvement paths.

---

## Phase 1: Quick Wins (Critical + Easy)

### 1A. Fix TypeScript Config Contradiction
**File:** `tsconfig.json`
**Issue:** `noImplicitAny: false` contradicts `strict: true`, silently defeating strict mode.
**Fix:** Remove the `noImplicitAny` override.

### 1B. Remove Dead Code
| File | Issue |
|------|-------|
| `src/lib/stores/itemsStore.svelte.ts` | Deprecated store, only used as unreachable fallback |
| `src/lib/components/facets/FacetPie.svelte` | Not imported anywhere in the codebase |
| `src/demo.spec.ts` | Placeholder test (`1+2=3`), no value |
| `src/lib/index.ts` | Empty file (single comment) |
| References in `countries/+page.svelte` | Remove itemsStore import and fallback logic |
| References in `+layout.svelte` | Remove commented-out itemsStore code |

### 1C. Fix Hardcoded i18n Strings & Colors
| File | Line | Issue | Fix |
|------|------|-------|-----|
| `Wordcloud.svelte` | 297 | `"Generating word cloud..."` English-only | Add `words.generating` translation key |
| `Wordcloud.svelte` | 303 | `"No data available for word cloud"` English-only | Add `words.no_data` translation key |
| `TopicSidebar.svelte` | 72 | Hardcoded `text-green-500` | Use `text-chart-3` (semantic) |

### 1D. Fix Core `any` Types
| File | Type | Issue |
|------|------|-------|
| `src/lib/types/index.ts` | `ChartConfig` | `data: any`, `options?: any` |
| `src/lib/types/index.ts` | `ChartDataPoint` | `metadata?: Record<string, any>` |
| `src/lib/components/ui/chart/chart-utils.ts` | `TooltipPayload` | 3 `any` fields + index signature |
| `src/lib/types/treemap.ts` | `TreemapData` | `[key: string]: any` index signature |
| `src/lib/types/treemap.ts` | `TreemapConfig` | `tile: any` |
| `src/lib/types/global.d.ts` + `index.ts` | `Word` | Duplicate interface definition |

---

## Phase 2: Theme Consistency (~6 hrs)

### 2A. Create Centralized Color Utilities
**New file:** `src/lib/utils/colors.ts`
- Entity type color map using CSS variables
- Color normalization function (CSS var parsing)
- Map color palette

**New CSS variables in `src/app.css`:**
- `--entity-person`, `--entity-organization`, `--entity-event`, etc.
- `--map-gradient-*` for choropleth palettes

### 2B. Fix Hardcoded Colors in Components
| Component | Lines | Issue |
|-----------|-------|-------|
| `NetworkGraph.svelte` | 170-178 | 8 hardcoded hex entity colors |
| `BarChartRace.svelte` | 157-171 | 15 hardcoded hex fallback colors |
| `ChoroplethLayer.svelte` | 28-35 | Hardcoded orange gradient |
| `CircleLayer.svelte` | various | `rgba()` with hardcoded values |
| `LineLayer.svelte` | various | Hardcoded color strings |

---

## Phase 3: DRY Chart Utilities (~8 hrs)

### 3A. Extract Shared Chart Patterns
**New files:**
- `src/lib/utils/chartTooltips.ts` — shared tooltip formatting (currently duplicated in 6 charts)
- `src/lib/utils/chartAxisRotation.ts` — responsive axis label rotation (duplicated in Bar, StackedBarChart, Timeline, Keywords)
- `src/lib/utils/useContainerSize.svelte.ts` — ResizeObserver composition (duplicated in Bar, Timeline, Wordcloud)

### 3B. Consolidate Color Normalization
Merge duplicated `asCssColor()` / `normalizeColor()` from PieChart, BarChartRace, Bar, StackedBarChart into `src/lib/utils/colors.ts`.

### 3C. Consider Bar + StackedBarChart Merge
`Bar.svelte` and `StackedBarChart.svelte` share ~75% of their logic. Consider merging with a `stacked` prop.

---

## Phase 4: Data Flow Consistency (~4 hrs)

### 4A. Migrate Pages to `dataFetcher.ts`
The existing `src/lib/utils/dataFetcher.ts` provides caching, retry, and error handling — but ~15 `+page.ts` files call raw `fetch()` instead.

**Pages to migrate:** languages, keywords, references/by-year, categories, scary, cooccurrence, words, countries, timeline, topics, entity-spatial, network, newspaper-coverage, spatial/world-map, spatial/sources.

### 4B. Standardize Error Handling
Create consistent error shape across all page load functions:
- Return `{ data, error }` tuple
- Use `fetchData<T>()` for type-safe loading
- Centralize HTTP error messages

---

## Phase 5: Python Script Consolidation (~1-2 days)

### 5A. Migrate Scripts to `iwac_utils.py`
**9 scripts don't use shared utilities:**
`generate_overview_stats`, `generate_categories`, `generate_treemap`, `generate_wordcloud`, `generate_cooccurrence`, `generate_scary_terms`, `generate_index_entities`, `generate_topic_explorer_data`, `generate_topic_network`

**Functions to adopt:** `load_dataset_safe()`, `save_json()`, `configure_logging()`, `normalize_country()`, `generate_timestamp()`, `create_metadata_block()`

### 5B. Standardize Output Metadata
- Use `camelCase` consistently (`generatedAt` not `generated_at`)
- Always use UTC with `'Z'` suffix via `generate_timestamp()`
- Use `create_metadata_block()` for consistent structure

### 5C. Pin Python Dependencies
Add version constraints to `scripts/requirements.txt`.

---

## Phase 6: Store Modernization (~2 hrs)

### 6A. Modernize `urlManager`
Replace manual subscription/listener pattern with Svelte 5 `$state` runes for consistency.

### 6B. Simplify Nested Record Types
Replace deeply nested `Record<string, Record<string, Record<string, number>>>` in `worldmap.ts` with named intermediate types.

### 6C. Type-Safe Translation Function
Replace `t(key: string, params: any[])` with `t(key: TranslationKey, params?: string[])`.

---

## Phase 7: Test Coverage (~10 hrs)

### 7A. Store Unit Tests
Test `translationStore`, `overviewStore`, `mapDataStore`, `entitySpatialStore`.

### 7B. Component Smoke Tests
Test top 5 visualization components render correctly with sample data.

### 7C. Python Integration Tests
Run actual generator scripts against test fixtures and validate output JSON.

### 7D. E2E Navigation Tests
Test multi-page navigation, language switching, filter interactions.

---

## Phase 8: Accessibility (~3 hrs)

### 8A. Add Missing ARIA Labels
NetworkGraph, MapLibre components, some custom SVG charts.

### 8B. Keyboard Navigation
Interactive charts and network graph need keyboard support.

### 8C. Color-Independent Indicators
Add text/pattern alternatives to legend items that rely on color alone.

---

## Summary

| Phase | Effort | Impact | Priority |
|-------|--------|--------|----------|
| 1. Quick Wins | ~3 hrs | High | **Do now** |
| 2. Theme Consistency | ~6 hrs | High | High |
| 3. DRY Chart Utilities | ~8 hrs | Medium | Medium |
| 4. Data Flow Consistency | ~4 hrs | Medium | Medium |
| 5. Python Consolidation | ~12 hrs | Medium | Medium |
| 6. Store Modernization | ~2 hrs | Low-Medium | Low |
| 7. Test Coverage | ~10 hrs | High | Medium |
| 8. Accessibility | ~3 hrs | Medium | Low |
| **Total** | **~48 hrs** | | |

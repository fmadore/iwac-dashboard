# IWAC Dashboard — Refactoring & Cleanup Roadmap

> Generated 2026-03-16 from a comprehensive codebase audit.

## Phase 1: Theme System & CSS Consistency

### 1.1 Add Entity Type CSS Variables to `app.css`
**Priority: Critical** | **Effort: 1h** | **Impact: High**

Network and entity-related components hardcode 9+ hex colors (`#3b82f6`, `#8b5cf6`, `#f97316`, etc.) that bypass the theme system and break in dark mode.

**Action:**
- Add `--entity-person`, `--entity-organization`, `--entity-event`, `--entity-subject`, `--entity-location`, `--entity-topic`, `--entity-article`, `--entity-author`, `--entity-authority` CSS variables to both `:root` and `.dark` in `src/app.css`
- Update `NetworkGraph.svelte` (lines 172–182) to use new variables
- Update `NetworkEntitySearch.svelte` (lines 39–49) to use new variables — eliminates duplication with NetworkGraph

### 1.2 Consolidate Fallback Color Maps
**Priority: High** | **Effort: 30m** | **Impact: Medium**

`BarChartRace.svelte` (lines 157–169) and `scary/+page.svelte` (lines 117–129) duplicate an identical fallback color map with outdated hex values.

**Action:**
- Create `src/lib/constants/theme.ts` with shared `FALLBACK_COLORS` map
- Import from both components
- Add dark-mode variants

### 1.3 Replace Hardcoded Colors in ChoroplethLayer
**Priority: Medium** | **Effort: 30m** | **Impact: Medium**

`ChoroplethLayer.svelte` (lines 28–36) uses a hardcoded orange gradient (`#fff7ed` → `#ea580c`). Replace with CSS variable-derived values or add dedicated `--choropleth-*` variables.

---

## Phase 2: Shared Utilities & DRY Refactoring

### 2.1 Extract Chart Axis Utilities
**Priority: High** | **Effort: 1h** | **Impact: High**

`Bar.svelte` and `StackedBarChart.svelte` share near-identical logic for:
- `effectiveXAxisLabelRotate` (breakpoints at 55px, 90px)
- `xAxisTicks` (min label spacing)
- `bottomPadding` (110/80/40 by rotation)

**Action:**
- Create `src/lib/utils/chartUtils.ts` with:
  - `calculateXAxisRotation(perItemWidth: number): number`
  - `calculateXAxisTicks(perItemWidth: number, rotation: number, dataLength: number): number`
  - `calculateBottomPadding(rotation: number, dataLength: number): number`
- Extract `tooltipLabelFromPayload()` and `tooltipItemsFromPayload()` (duplicated in 12+ chart components) into a shared `tooltipUtils` section
- Define chart constants: `LABEL_BREAKPOINT_TIGHT = 55`, `LABEL_BREAKPOINT_COMFORTABLE = 90`, etc.

### 2.2 Create ResizeObserver Composable
**Priority: Medium** | **Effort: 30m** | **Impact: Medium**

6 components implement ResizeObserver with inconsistent patterns. Create `src/lib/utils/useResizeObserver.svelte.ts`:

```ts
export function useResizeObserver(element: () => HTMLElement | null) { ... }
```

**Components to update:** Bar.svelte, BarChartRace.svelte, CooccurrenceMatrix.svelte, TimelineChart.svelte, SemanticMapCanvas.svelte, Wordcloud.svelte

---

## Phase 3: Dead Code Removal

### 3.1 Remove Unused Components & Types
**Priority: Medium** | **Effort: 15m** | **Impact: Low**

| Item | Location | Reason |
|------|----------|--------|
| LazyLoad, LazyComponent | `src/lib/components/lazy/` | Exported but never imported by any page/component |
| OmekaItem, ChartDataPoint, StatsData | `src/lib/types/index.ts` | Declared but never imported |

### 3.2 Clean Up Placeholder Content
**Priority: Low** | **Effort: 10m** | **Impact: Low**

- `src/routes/newspaper-coverage/+page.svelte` uses hardcoded `placeholderData`
- `e2e/demo.test.ts` is a minimal placeholder

---

## Phase 4: Data Fetching Consistency

### 4.1 Migrate Pages to `dataFetcher.ts`
**Priority: High** | **Effort: 2h** | **Impact: High**

`src/lib/utils/dataFetcher.ts` provides caching (5min TTL), retry logic, and consistent error handling — but only `overviewStore` uses it. ~15 pages use raw `fetch()`.

**Action:** Migrate all page components to use `fetchData<T>()`:

**Pages to migrate:**
- `timeline/+page.svelte` (3 fetch calls)
- `countries/+page.svelte`
- `cooccurrence/+page.svelte`
- `entities/+page.svelte`
- `network/+page.svelte`
- `network-map/+page.svelte`
- `semantic-map/+page.svelte`
- `words/+page.svelte`
- `keywords/+page.svelte`
- `scary/+page.svelte`
- `references/*` (6 sub-pages)
- `spatial/*` (2 sub-pages)
- `knowledge-graph/+page.svelte`
- `entity-spatial/+page.svelte`
- `topic-network/+page.svelte`

---

## Phase 5: i18n Completeness

### 5.1 Add Missing French Translations (30 keys)
**Priority: High** | **Effort: 1h** | **Impact: Medium**

95.6% FR coverage → 100%. Missing keys include descriptions, help text, chart labels.

### 5.2 Translate Hardcoded aria-labels & sr-only Text
**Priority: Medium** | **Effort: 30m** | **Impact: Medium**

7 hardcoded `aria-label` attributes and 5 `sr-only` text strings need translation keys:
- `ThemeToggle.svelte`: "Toggle theme"
- `sidebar-rail.svelte`: "Toggle Sidebar"
- `EntityPicker.svelte`: "Clear selection"
- `Map.svelte`: "Close legend", "Show legend"
- `entities-table.svelte`: "Remove filter" (×2)

---

## Phase 6: CI & Python Consistency

### 6.1 Add Missing Python Scripts to CI Workflow
**Priority: High** | **Effort: 30m** | **Impact: Critical**

10 Python scripts are NOT in `.github/workflows/generate-data.yml`, meaning their data won't regenerate on schedule:
- `generate_cooccurrence.py`, `generate_entity_spatial.py`, `generate_keywords.py`, `generate_knowledge_graph.py`, `generate_references_subject_cooccurrence.py`, `generate_semantic_map.py`, `generate_sources.py`, `generate_spatial_networks.py`, `generate_topic_network.py`, `generate_world_map.py`

### 6.2 Migrate Python Scripts to Use `iwac_utils.py`
**Priority: Medium** | **Effort: 2h** | **Impact: Medium**

9 of 17 generator scripts have their own `load_dataset_safe()`, `safe_sum_column()`, etc. instead of using the shared utilities.

---

## Phase 7: Type Safety (Future)

### 7.1 Remove `any` Types from Tooltip Handlers
Replace `any[]` in tooltip payload parsers with proper `TooltipPayload` interface.

### 7.2 Type NetworkGraph Sigma Instance
Replace `sigmaInstance: any` and `graphInstance: any` with proper imports.

---

## Summary

| Phase | Items | Effort | Impact |
|-------|-------|--------|--------|
| 1. Theme/CSS | 3 items | 2h | High — fixes 30+ hardcoded colors |
| 2. Shared Utils | 2 items | 1.5h | High — eliminates duplication in 12+ components |
| 3. Dead Code | 2 items | 25m | Low — cleaner codebase |
| 4. Data Fetching | 1 item | 2h | High — consistent caching/error handling |
| 5. i18n | 2 items | 1.5h | Medium — completes FR translations |
| 6. CI/Python | 2 items | 2.5h | Critical — prevents stale data |
| 7. Types | 2 items | 1h | Medium — better DX |

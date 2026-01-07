# Component Reorganization Plan

This plan proposes a cleaner, more scalable structure for `src/lib/components/`.

## Current State Analysis

```
src/lib/components/
├── app-sidebar.svelte          ← loose: layout-related
├── fullscreen-toggle.svelte    ← loose: toggle/control
├── language-toggle.svelte      ← loose: toggle/control
├── overview-stats-grid.svelte  ← loose: dashboard/stats
├── safe-mode-watcher.svelte    ← loose: utility
├── stats-card.svelte           ← loose: dashboard/stats
├── theme-toggle.svelte         ← loose: toggle/control
├── url-state-sync.svelte       ← loose: utility
├── wordcloud.svelte            ← loose: visualization
│
├── charts/                     (11 files - mixed D3 and LayerChart)
│   ├── BarChartRace.svelte     ← D3-based
│   ├── CooccurrenceMatrix.svelte  ← D3-based
│   ├── LayerChartBar.svelte       ← LayerChart-based
│   ├── LayerChartDuration.svelte  ← LayerChart-based
│   ├── LayerChartPieChart.svelte  ← LayerChart-based
│   ├── LayerChartTooltip.svelte   ← LayerChart shared
│   ├── LayerChartTreemap.svelte   ← LayerChart-based
│   ├── StackedBarChart.svelte     ← D3-based
│   ├── TimelineChart.svelte       ← D3-based
│   ├── WordAssociations.svelte    ← D3-based
│   └── utils.ts
│
├── facets/                     (1 file - underutilized)
├── lazy/                       (3 files - good)
├── network/                    (6 files - good)
├── ui/                         (20 shadcn folders - keep as-is)
└── world-map/                  (5 files - good)
```

### Issues Identified

1. **9 loose files in root** - No clear organization for layout, toggles, utilities, and stats components
2. **Charts mixing rendering libraries** - D3-based and LayerChart-based components are intermingled
3. **Inconsistent naming** - Some use PascalCase (`LayerChartBar`), others use kebab-case in folders
4. **Orphan folders** - `facets/` has only 1 file, could merge elsewhere
5. **Missing barrel exports** - No `index.ts` in charts folder for cleaner imports

---

## Proposed Structure

```
src/lib/components/
│
├── layout/                        ← NEW: layout & navigation
│   ├── index.ts
│   ├── AppSidebar.svelte          (was: app-sidebar.svelte)
│   └── FullscreenToggle.svelte    (was: fullscreen-toggle.svelte)
│
├── controls/                      ← NEW: user preference toggles
│   ├── index.ts
│   ├── LanguageToggle.svelte      (was: language-toggle.svelte)
│   └── ThemeToggle.svelte         (was: theme-toggle.svelte)
│
├── dashboard/                     ← NEW: dashboard/overview components  
│   ├── index.ts
│   ├── OverviewStatsGrid.svelte   (was: overview-stats-grid.svelte)
│   └── StatsCard.svelte           (was: stats-card.svelte)
│
├── utilities/                     ← NEW: non-visual utility components
│   ├── index.ts
│   ├── SafeModeWatcher.svelte     (was: safe-mode-watcher.svelte)
│   └── UrlStateSync.svelte        (was: url-state-sync.svelte)
│
├── visualizations/                ← NEW: top-level viz folder
│   ├── index.ts
│   ├── Wordcloud.svelte           (was: wordcloud.svelte)
│   │
│   ├── charts/                    ← charts regrouped
│   │   ├── index.ts               ← NEW: barrel export
│   │   ├── utils.ts
│   │   │
│   │   ├── d3/                    ← NEW: D3-based charts
│   │   │   ├── index.ts
│   │   │   ├── BarChartRace.svelte
│   │   │   ├── CooccurrenceMatrix.svelte
│   │   │   ├── StackedBarChart.svelte
│   │   │   ├── TimelineChart.svelte
│   │   │   └── WordAssociations.svelte
│   │   │
│   │   └── layerchart/            ← NEW: LayerChart-based
│   │       ├── index.ts
│   │       ├── Bar.svelte         (simplified name)
│   │       ├── Duration.svelte
│   │       ├── PieChart.svelte
│   │       ├── Tooltip.svelte
│   │       └── Treemap.svelte
│   │
│   ├── network/                   ← MOVED from root
│   │   └── (unchanged - already well organized)
│   │
│   └── world-map/                 ← MOVED from root
│       └── (unchanged - already well organized)
│
├── facets/                        ← KEEP or merge into visualizations
│   └── FacetPie.svelte
│
├── lazy/                          ← KEEP (already organized)
│   └── (unchanged)
│
└── ui/                            ← KEEP: shadcn primitives (do not modify)
    └── (unchanged - 20 folders)
```

---
> **Decision: Facets Folder**
> `FacetPie.svelte` is the only file in `facets/`. Options:
> - Keep as-is (allows for future growth)
> - Move to `visualizations/charts/` or `visualizations/` root

> [!IMPORTANT]
> **Decision: Component Naming**
> Proposed to rename kebab-case files to PascalCase (Svelte convention). All imports will need updating.

---

## Proposed Changes

### Layout Components

#### [NEW] [index.ts](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/layout/index.ts)
Barrel export for layout components.

#### [MOVE] [AppSidebar.svelte](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/layout/AppSidebar.svelte)
Move from `app-sidebar.svelte` to `layout/AppSidebar.svelte`.

#### [MOVE] [FullscreenToggle.svelte](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/layout/FullscreenToggle.svelte)
Move from `fullscreen-toggle.svelte` to `layout/`.

---

### Controls Components

#### [NEW] [index.ts](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/controls/index.ts)
Barrel export for control/toggle components.

#### [MOVE] [LanguageToggle.svelte](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/controls/LanguageToggle.svelte)
Move from `language-toggle.svelte`.

#### [MOVE] [ThemeToggle.svelte](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/controls/ThemeToggle.svelte)
Move from `theme-toggle.svelte`.

---

### Dashboard Components

#### [NEW] [index.ts](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/dashboard/index.ts)
Barrel export.

#### [MOVE] [OverviewStatsGrid.svelte](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/dashboard/OverviewStatsGrid.svelte)
Move from `overview-stats-grid.svelte`.

#### [MOVE] [StatsCard.svelte](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/dashboard/StatsCard.svelte)
Move from `stats-card.svelte`.

---

### Utilities Components

#### [NEW] [index.ts](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/utilities/index.ts)
Barrel export.

#### [MOVE] [SafeModeWatcher.svelte](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/utilities/SafeModeWatcher.svelte)
Move from `safe-mode-watcher.svelte`.

#### [MOVE] [UrlStateSync.svelte](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/utilities/UrlStateSync.svelte)
Move from `url-state-sync.svelte`.

---

### Visualizations

#### [NEW] [index.ts](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/visualizations/index.ts)
Barrel export for all visualizations.

#### [MOVE] [Wordcloud.svelte](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/visualizations/Wordcloud.svelte)
Move from `wordcloud.svelte`.

#### [MOVE] network/
Move folder from `components/network/` to `components/visualizations/network/`.

#### [MOVE] world-map/
Move folder from `components/world-map/` to `components/visualizations/world-map/`.

---

### Charts Restructure

#### [NEW] [charts/index.ts](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/visualizations/charts/index.ts)
Re-exports all chart components.

#### [NEW] [charts/d3/index.ts](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/visualizations/charts/d3/index.ts)
Barrel export for D3 charts.

#### [MOVE] D3 Charts
Move to `charts/d3/`:
- `BarChartRace.svelte`  
- `CooccurrenceMatrix.svelte`
- `StackedBarChart.svelte`
- `TimelineChart.svelte`
- `WordAssociations.svelte`

#### [NEW] [charts/layerchart/index.ts](file:///c:/Users/frede/GitHub/iwac-dashboard/src/lib/components/visualizations/charts/layerchart/index.ts)
Barrel export for LayerChart components.

#### [MOVE] LayerChart Components
Move to `charts/layerchart/` with simplified names:
- `LayerChartBar.svelte` → `Bar.svelte`
- `LayerChartDuration.svelte` → `Duration.svelte`
- `LayerChartPieChart.svelte` → `PieChart.svelte`
- `LayerChartTooltip.svelte` → `Tooltip.svelte`
- `LayerChartTreemap.svelte` → `Treemap.svelte`

---

## Import Update Summary

All imports will need updating. Example transformations:

```diff
- import AppSidebar from '$lib/components/app-sidebar.svelte';
+ import { AppSidebar } from '$lib/components/layout';

- import TimelineChart from '$lib/components/charts/TimelineChart.svelte';
+ import { TimelineChart } from '$lib/components/visualizations/charts/d3';

- import LayerChartBar from '$lib/components/charts/LayerChartBar.svelte';
+ import { Bar } from '$lib/components/visualizations/charts/layerchart';
```

---

## Verification Plan

### Build Verification
```bash
npm run check
npm run build
```
Ensures TypeScript compilation succeeds with all updated imports.

### Manual Verification
1. Start dev server: `npm run dev`
2. Navigate to each major page and verify components load:
   - `/` (overview - uses StatsCard, OverviewStatsGrid)
   - `/timeline` (uses TimelineChart)
   - `/network` (uses NetworkGraph)
   - `/spatial/world-map` (uses WorldMapVisualization)
   - `/topics` (uses LayerChartBar, LayerChartPieChart)
   - `/scary` (uses BarChartRace)

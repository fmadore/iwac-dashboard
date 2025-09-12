# IWAC Database Overview Migration Roadmap to shadcn-svelte

## Overview

This roadmap tracks the migration of the IWAC Database Overview from a custom D3.js-based visualization app to a modern dashboard using shadcn-svelte with **Svelte 5**. The new architecture features a sidebar navigation, integrated charts, and data tables while maintaining all existing functionality.

## Progress Summary

**Current Status: Core Infrastructure Complete, UI Components Implemented**

## Phase 1: Project Setup & Foundation ✅ COMPLETED

### 1.1 Create New Svelte 5 Project ✅ COMPLETED
- SvelteKit project with **Svelte 5** and TypeScript
- Vite build system
- ESLint, Prettier, Vitest, Playwright configured

### 1.2 Configure TypeScript for Svelte 5 ✅ COMPLETED
- Auto-configured by SvelteKit template
- Path aliases configured for `$lib/*`
- **Svelte 5 runes/reactivity syntax used throughout the codebase**

### 1.3 Setup shadcn-svelte ✅ COMPLETED
- TailwindCSS integration
- Slate theme configuration
- Component path aliases configured

### 1.4 Install Core shadcn-svelte Components ✅ COMPLETED
- All essential UI components installed (button, card, sidebar, table, tabs, etc.)
- lucide-svelte for icons

## Phase 2: Core Infrastructure ✅ COMPLETED

### 2.1 Data Management Setup ✅ COMPLETED
- `src/lib/stores/itemsStore.ts` - Items store with loading states and derived statistics
- Mock data implementation ready for real API integration

### 2.2 Translation System ✅ COMPLETED  
- `src/lib/stores/translationStore.ts` - English/French translations with reactive language switching
- Language toggle component implemented

### 2.3 Type Definitions ✅ COMPLETED
- `src/lib/types/index.ts` - Complete TypeScript interfaces for OmekaItem, ChartDataPoint, FilterState

## Phase 3: Dashboard Layout Implementation ✅ PARTIALLY COMPLETED

### 3.1 Main Layout Structure ✅ COMPLETED
- `src/routes/+layout.svelte` - Dashboard layout with sidebar and header
- Sidebar provider integration with language toggle

### 3.2 Sidebar Navigation ✅ COMPLETED
- `src/lib/components/app-sidebar.svelte` - Navigation menu with active state tracking
- Lucide icons for all navigation items

## Phase 4: Visualization Components Migration 🔄 IN PROGRESS

### 4.1 Overview Dashboard ✅ COMPLETED
- `src/routes/+page.svelte` - Main dashboard with stats cards
- `src/lib/components/stats-card.svelte` - Reusable stats component
- Loading states and error handling

### 4.2 Country Distribution ✅ COMPLETED
- `src/routes/countries/+page.svelte` - Hierarchical country view
- Expandable/collapsible country breakdown by document types
- Replaces original treemap visualization

### 4.3 Language Distribution 📋 TODO
- `src/routes/languages/+page.svelte` - Pie chart visualization
- Filter by country and document type
- Chart.js or similar integration needed

### 4.4 Timeline Visualization 📋 TODO
- `src/routes/timeline/+page.svelte` - Line chart with tabs
- Monthly/yearly/cumulative views
- Document creation timeline analysis

### 4.5 Type Distribution 📋 TODO
- `src/routes/types/+page.svelte` - Document type breakdown
- Stacked bar chart or similar visualization

### 4.6 Category Distribution 📋 TODO
- `src/routes/categories/+page.svelte` - Category analysis
- Bar chart visualization

### 4.7 Word Analysis 📋 TODO
- `src/routes/words/+page.svelte` - Word count analysis
- Alternative to original D3 word visualization

## Phase 5: Advanced Features 📋 TODO

### 5.1 URL Parameter Support
- Language persistence in URL
- Filter state in URL parameters

### 5.2 Export Functionality
- JSON, CSV export options
- Chart export as SVG/PNG

### 5.3 Filter System
- Global filter panel
- Country, type, language, date range filters

### 5.4 Search Implementation
- Full-text search across items
- Search highlighting

## Phase 6: Performance Optimization 📋 TODO

### 6.1 Lazy Loading
- Component-level lazy loading
- Intersection Observer implementation

### 6.2 Data Virtualization
- Virtual scrolling for large datasets
- Efficient rendering optimization

## Phase 7: Testing & Deployment 📋 TODO

### 7.1 Testing Setup
- Unit tests for components
- Integration tests for workflows

### 7.2 Build Configuration
- Production build optimization
- GitHub Pages deployment setup

## Current Issues to Resolve

### 🚨 High Priority
1. **Module Resolution Issues** - Fix TypeScript import errors in layout
2. **Development Server** - Get `npm run dev` working
3. **Chart Library Integration** - Choose and implement chart solution

### 🔧 Medium Priority
1. **Real Data Integration** - Replace mock data with actual API
2. **Responsive Design** - Ensure mobile compatibility
3. **Dark Mode Support** - Implement theme switching

## Migration Checklist

### Setup Phase ✅ COMPLETED
- [x] Create new Svelte 5 project (SvelteKit with TypeScript)
- [x] Configure TypeScript (auto-configured by SvelteKit)
- [x] Install shadcn-svelte (with Slate theme)
- [x] Setup routing structure (SvelteKit file-based routing)
- [x] Configure build tools (Vite, ESLint, Prettier, Vitest, Playwright)

### Core Features ✅ COMPLETED
- [x] Migrate data loading (itemsStore with mock data)
- [x] Implement translation system (en/fr support)
- [x] Create dashboard layout (with sidebar)
- [x] Setup sidebar navigation (with Lucide icons)
- [ ] Implement URL parameters

### Visualizations 🔄 IN PROGRESS
- [x] Overview dashboard with stats cards
- [x] Country distribution (hierarchical table with expand/collapse)
- [ ] Language distribution (pie chart)
- [ ] Timeline (line chart)
- [ ] Type distribution (stacked bar)
- [ ] Category distribution (bar chart)
- [ ] Word analysis (alternative visualization)

### Advanced Features 📋 TODO
- [ ] Filter system
- [ ] Export functionality
- [ ] Search implementation
- [x] Responsive design (TailwindCSS)
- [ ] Dark mode support

### Testing & Deployment 📋 TODO
- [x] Unit tests (Vitest configured)
- [ ] Integration tests
- [ ] Performance testing
- [ ] Build optimization
- [ ] Deploy to GitHub Pages

## Next Steps (Priority Order)

1. **Fix Development Environment** - Resolve module resolution and run dev server
2. **Chart Integration** - Install and configure Chart.js or similar
3. **Complete Visualization Pages** - Implement languages, timeline, types, categories, words
4. **Add Filtering** - Global filter system across all views
5. **Real Data Integration** - Connect to actual IWAC database
6. **Export Features** - CSV/JSON export functionality
7. **Performance Optimization** - Virtual scrolling and lazy loading
8. **Deployment** - GitHub Pages setup

## Architecture Decisions

### UI Framework: shadcn-svelte + Svelte 5 ✅
- Provides consistent, accessible components
- Easy theming and customization
- Good TypeScript support
- **Svelte 5 runes/reactivity model for all new code**

### Charts: TBD 🤔
Options being considered:
- Chart.js (most popular, good docs)
- Apache ECharts (powerful, good for complex charts)
- D3.js (most flexible, steeper learning curve)
- Native HTML/CSS (for simple visualizations)

### Data Management: Svelte Stores ✅
- Reactive and efficient
- Good for small to medium datasets
- Easy state management

## Resources

- [Svelte 5 Documentation](https://svelte.dev/docs)
- [Svelte 5 Migration Guide](migration-guide-Svelte.txt)
- [shadcn-svelte Documentation](https://www.shadcn-svelte.com/)
- [SvelteKit Documentation](https://kit.svelte.dev/)
- [TailwindCSS Documentation](https://tailwindcss.com/)
- [Chart.js Documentation](https://www.chartjs.org/)

## Files Implemented

### Core Structure
- ✅ `src/lib/types/index.ts` - TypeScript interfaces
- ✅ `src/lib/stores/itemsStore.ts` - Data management
- ✅ `src/lib/stores/translationStore.ts` - i18n system

### Components
- ✅ `src/lib/components/language-toggle.svelte` - Language switcher
- ✅ `src/lib/components/app-sidebar.svelte` - Navigation sidebar
- ✅ `src/lib/components/stats-card.svelte` - Statistics display

### Pages
- ✅ `src/routes/+layout.svelte` - Main layout
- ✅ `src/routes/+page.svelte` - Overview dashboard
- ✅ `src/routes/countries/+page.svelte` - Country distribution

### To Implement
- 📋 `src/routes/languages/+page.svelte`
- 📋 `src/routes/timeline/+page.svelte`
- 📋 `src/routes/types/+page.svelte`
- 📋 `src/routes/categories/+page.svelte`
- 📋 `src/routes/words/+page.svelte`

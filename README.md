# IWAC Dashboard

A modern, static data visualization dashboard for the **Islam West Africa Collection (IWAC)** database. Built with SvelteKit, Svelte 5, shadcn-svelte, and fully prerendered as static HTML for deployment.

## Overview

This dashboard provides interactive visualizations and analytics for the IWAC dataset from Hugging Face (`fmadore/islam-west-africa-collection`), featuring:

- 📊 **Overview Dashboard** - Key statistics and summary cards
- 🗺️ **Country Treemap** - Hierarchical visualization of document distribution by country
- 🌍 **Language Analysis** - Distribution of documents by language with pie charts
- 📚 **Entity Index** - Searchable, sortable table of all entities with filtering
- 📈 **Timeline View** - Temporal analysis of document creation and growth
- 🏷️ **Categories** - Document categorization and distribution
- 🔍 **Word Cloud** - Most frequent terms across the collection
- ⚠️ **Scary Terms** - Analysis of concerning terminology patterns
- 🌐 **Bilingual Support** - Full English/French interface with real-time switching
- 🎨 **Dark/Light Mode** - Theme switching with system preference detection
- 📱 **PWA Support** - Progressive Web App with offline capabilities

## Data Flow

The dashboard uses a **static data generation approach**:

1. **Python Scripts** (in `scripts/`) fetch data from Hugging Face
2. Scripts process and generate **static JSON files**
3. JSON files saved to **both** `static/data/` and `build/data/`
4. Svelte components fetch from `/data/[filename].json` using `fetch()`
5. All pages use `export const prerender = true;` for static site generation

### Python Data Generators

- `generate_overview_stats.py` - Overall statistics and counts
- `generate_index_entities.py` - Entity data and bar charts
- `generate_language_facets.py` - Language distribution data
- `generate_treemap.py` - Country treemap data
- `generate_wordcloud.py` - Word frequency data
- `generate_timeline.py` - Temporal analysis data
- `generate_categories.py` - Category distribution data
- `generate_scary_terms.py` - Concerning terminology analysis

### Running Data Generation

```bash
cd scripts
pip install -r requirements.txt
python generate_overview_stats.py
python generate_index_entities.py
python generate_language_facets.py
python generate_treemap.py
python generate_wordcloud.py
python generate_timeline.py
python generate_categories.py
python generate_scary_terms.py
```

## Developing

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev

# or start and open in browser
npm run dev -- --open
```

## Technology Stack

- **Framework**: SvelteKit with **Svelte 5** (runes mode) and TypeScript
- **UI Components**: shadcn-svelte (Card, Button, Table, Skeleton, etc.)
- **Styling**: Tailwind CSS v4 with CSS variables theming
- **Visualizations**:
  - LayerChart (preferred for new charts)
  - D3.js (custom visualizations, treemaps, word clouds)
  - ECharts (complex charts with many options)
- **Icons**: Lucide Svelte
- **Theme Management**: mode-watcher
- **Data Processing**: Python scripts generating static JSON files
- **Testing**: Vitest (unit) + Playwright (E2E)
- **Build Tool**: Vite
- **PWA**: @vite-pwa/sveltekit
- **Adapter**: @sveltejs/adapter-static (full prerendering)

## Project Structure

```
iwac-dashboard/
├── src/
│   ├── lib/
│   │   ├── components/
│   │   │   ├── controls/                    # Controls (toggles)
│   │   │   │   ├── LanguageToggle.svelte    # EN/FR language switcher
│   │   │   │   ├── ThemeToggle.svelte       # Dark/light mode toggle
│   │   │   │   └── index.ts                 # Barrel export
│   │   │   ├── dashboard/                   # Dashboard components
│   │   │   │   ├── OverviewStatsGrid.svelte # Overview statistics grid
│   │   │   │   ├── StatsCard.svelte         # Statistics display card
│   │   │   │   └── index.ts
│   │   │   ├── facets/                      # Faceted visualizations
│   │   │   │   └── FacetPie.svelte          # Pie chart facet
│   │   │   ├── layout/                      # Layout components
│   │   │   │   ├── AppSidebar.svelte        # Navigation sidebar
│   │   │   │   ├── FullscreenToggle.svelte  # Fullscreen mode toggle
│   │   │   │   └── index.ts
│   │   │   ├── lazy/                        # Lazy loading components
│   │   │   │   ├── LazyLoad.svelte          # Viewport lazy loading
│   │   │   │   ├── LazyComponent.svelte     # Dynamic import lazy loading
│   │   │   │   └── index.ts
│   │   │   ├── ui/                          # shadcn-svelte components
│   │   │   │   ├── card/                    # Card component
│   │   │   │   ├── button/                  # Button component
│   │   │   │   ├── table/                   # Table component
│   │   │   │   └── ...                      # Other UI components
│   │   │   ├── utilities/                   # Utility components
│   │   │   │   ├── SafeModeWatcher.svelte   # Safe mode watcher
│   │   │   │   ├── UrlStateSync.svelte      # URL state synchronization
│   │   │   │   └── index.ts
│   │   │   └── visualizations/              # All visualizations
│   │   │       ├── charts/
│   │   │       │   ├── d3/                  # D3-based charts
│   │   │       │   │   ├── BarChartRace.svelte
│   │   │       │   │   ├── CooccurrenceMatrix.svelte
│   │   │       │   │   ├── StackedBarChart.svelte
│   │   │       │   │   ├── TimelineChart.svelte
│   │   │       │   │   ├── WordAssociations.svelte
│   │   │       │   │   └── index.ts
│   │   │       │   ├── layerchart/          # LayerChart-based charts
│   │   │       │   │   ├── Bar.svelte
│   │   │       │   │   ├── Duration.svelte
│   │   │       │   │   ├── PieChart.svelte
│   │   │       │   │   ├── Tooltip.svelte
│   │   │       │   │   ├── Treemap.svelte
│   │   │       │   │   └── index.ts
│   │   │       │   ├── utils.ts             # Chart utilities
│   │   │       │   └── index.ts
│   │   │       ├── network/                 # Network visualizations
│   │   │       │   ├── NetworkGraph.svelte
│   │   │       │   ├── NetworkControls.svelte
│   │   │       │   ├── NetworkNodePanel.svelte
│   │   │       │   └── index.ts
│   │   │       ├── world-map/               # Map visualizations
│   │   │       │   ├── WorldMapVisualization.svelte
│   │   │       │   ├── Map.svelte
│   │   │       │   ├── ChoroplethLayer.svelte
│   │   │       │   └── index.ts
│   │   │       ├── Wordcloud.svelte         # Word cloud visualization
│   │   │       └── index.ts
│   │   ├── stores/                          # Svelte stores
│   │   │   ├── itemsStore.svelte.ts         # Global data store
│   │   │   ├── translationStore.svelte.ts   # i18n translation store
│   │   │   └── ...
│   │   ├── types/                           # TypeScript definitions
│   │   ├── hooks/                           # Custom Svelte hooks
│   │   └── utils/                           # Utility functions
│   ├── routes/                              # SvelteKit file-based routing
│   │   ├── +layout.svelte                   # Root layout with sidebar
│   │   ├── +page.svelte                     # Overview dashboard (/)
│   │   ├── countries/+page.svelte           # Country treemap view
│   │   ├── languages/+page.svelte           # Language distribution
│   │   ├── entities/+page.svelte            # Entity index table
│   │   ├── timeline/+page.svelte            # Timeline analysis
│   │   └── ...
│   ├── app.html                             # HTML template
│   └── app.css                              # Global styles with CSS variables
├── scripts/                                 # Python data generation scripts
├── static/data/                             # Static JSON data files
└── build/                                   # Production build output
```


## Building

To create a production build:

```bash
npm run build
```

The build process:

1. Prerenders all pages to static HTML
2. Copies static assets to `build/`
3. Generates service worker for PWA
4. Creates a fully static site ready for deployment

Preview the production build:

```bash
npm run preview
```

## Available Scripts

```bash
npm run dev              # Start development server
npm run build            # Build for production
npm run preview          # Preview production build
npm run check            # Type-check with svelte-check
npm run check:watch      # Type-check in watch mode
npm run format           # Format code with Prettier
npm run lint             # Lint code with ESLint and Prettier
npm test                 # Run all tests
npm run test:unit        # Run unit tests with Vitest
npm run test:e2e         # Run E2E tests with Playwright
npm run generate-icons   # Generate PWA icons
```

## Key Features

### Svelte 5 Runes Mode

This project uses **Svelte 5 with runes mode** exclusively:

```svelte
<script>
	// Props
	let { count = 0 } = $props();

	// State
	let items = $state([]);

	// Derived values
	const doubled = $derived(count * 2);

	// Effects
	$effect(() => {
		console.log('Count changed:', count);
	});
</script>
```

### Internationalization (i18n)

Full bilingual support (English/French) with:

- Store-based translation system (`translationStore.ts`)
- Language toggle component in header
- All text uses `$t('key')` for translation
- Charts and visualizations update reactively with language changes

```svelte
<script>
	import { t, languageStore } from '$lib/stores/translationStore.js';
</script>

<h1>{$t('app.title')}</h1><p>{$t('stats.total_items')}</p>
```

### Theme System

- Dark/light mode with system preference detection
- CSS variables for theming (in `src/app.css`)
- `mode-watcher` package for theme management
- All colors use CSS variables for theme compatibility

### PWA Support

- Progressive Web App with offline capabilities
- Service worker for caching
- Manifest file for installation
- Generated icons in multiple sizes

## Deployment

This is a **fully static site** that can be deployed to:

- GitHub Pages
- Netlify
- Vercel
- Any static hosting service

The site is configured for deployment at a subpath (`/iwac-dashboard/`) using the `base` path from `$app/paths`.

## Development Guidelines

### Critical Rules

1. **Always use Svelte 5 syntax** - No Svelte 4 patterns
2. **Use shadcn-svelte components** - Never create custom basic UI
3. **Use CSS variables** - No hardcoded colors
4. **Static JSON data only** - All data from `/data/*.json`
5. **Bilingual required** - All text must support EN/FR
6. **LayerChart preferred** - Use LayerChart for new visualizations

### Color System

Always reference CSS variables from our theme:

```svelte
<!-- ✅ Correct -->
<div class="bg-background text-foreground">
	<div class="border border-border bg-card text-card-foreground">
		<span class="text-muted-foreground">Muted text</span>
	</div>
</div>

<!-- ❌ Wrong -->
<div class="bg-blue-500 text-white">
	<span class="text-gray-500">Muted</span>
</div>
```

### Data Loading Pattern

```svelte
<script>
	import { base } from '$app/paths';

	let data = $state([]);
	let loading = $state(true);
	let error = $state(null);

	async function loadData() {
		try {
			const response = await fetch(`${base}/data/filename.json`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			data = await response.json();
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		loadData();
	});
</script>
```

## Pages Overview

| Route         | Description                                               |
| ------------- | --------------------------------------------------------- |
| `/`           | Overview dashboard with key statistics and charts         |
| `/countries`  | Interactive treemap of document distribution by country   |
| `/languages`  | Language distribution with pie charts and facets          |
| `/entities`   | Searchable entity index table with sorting and filtering  |
| `/timeline`   | Temporal analysis with timeline charts and growth metrics |
| `/categories` | Document categorization and distribution analysis         |
| `/words`      | Word cloud visualization of frequent terms                |
| `/scary`      | Analysis of concerning terminology patterns               |

## Dataset

This dashboard visualizes the **Islam West Africa Collection (IWAC)** dataset:

- **Source**: Hugging Face Dataset `fmadore/islam-west-africa-collection`
- **Content**: Islamic manuscripts, documents, and texts from West Africa
- **Countries**: Côte d'Ivoire, Burkina Faso, Benin, Togo, Niger, Nigeria
- **Languages**: Multiple languages including Arabic, French, English, and local languages

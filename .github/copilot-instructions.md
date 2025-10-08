# IWAC Dashboard - GitHub Copilot Instructions

## Project Overview

This project is an **Islam West Africa Collection (IWAC) Dashboard** - a static data visualization dashboard built with SvelteKit that displays analytics and visualizations for the IWAC dataset from Hugging Face. The dashboard is fully prerendered as static HTML for deployment and features interactive charts, word clouds, and data exploration tools.

**Key Technologies:**

- **Svelte 5** (latest) - Using runes mode for reactivity
- **SvelteKit** - Static site generation (SSR, prerendering)
- **shadcn-svelte** - UI component library
- **Tailwind CSS v4** - Styling with CSS variables theming
- **D3.js** - Current visualization library
- **ECharts** - Preferred library for future visualizations
- **Python** - Data preprocessing and JSON generation
- **TypeScript** - Type safety

## Critical Development Rules

### 1. Always Use Svelte 5 Syntax (Runes Mode)

**NEVER use Svelte 4 syntax.** This project uses Svelte 5 exclusively with runes mode.

#### ❌ WRONG (Svelte 4):

```svelte
<script>
	export let count = 0;
	$: doubled = count * 2;
	let items = [];
</script>
```

#### ✅ CORRECT (Svelte 5):

```svelte
<script>
	let { count = 0 } = $props();
	const doubled = $derived(count * 2);
	let items = $state([]);
</script>
```

**Key Svelte 5 Patterns:**

- Use `$state()` for reactive variables
- Use `$derived()` for computed values (replaces `$:`)
- Use `$props()` for component props (replaces `export let`)
- Use `$effect()` for side effects (replaces `$:` statements)
- Use `$bindable()` for two-way binding props

### 2. Use shadcn-svelte Components for UI

**Always use shadcn-svelte components** for UI elements. Never create custom basic UI components when shadcn-svelte provides them.

#### Available Components:

- Card, Button, Input, Select, Table, Skeleton, Badge, etc.
- Import from `$lib/components/ui/[component]/index.js`

#### ✅ Example:

```svelte
<script>
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
</script>

<Card.Root>
	<Card.Header>
		<Card.Title>Title</Card.Title>
	</Card.Header>
	<Card.Content>
		<Button>Click me</Button>
	</Card.Content>
</Card.Root>
```

### 3. Use CSS Variables from Our Theme System

**Always use Tailwind classes that reference our CSS variables** defined in `src/app.css`. Never use arbitrary color values.

#### Our Theme Variables (src/app.css):

```css
--background, --foreground
--card, --card-foreground
--primary, --primary-foreground
--secondary, --secondary-foreground
--muted, --muted-foreground
--accent, --accent-foreground
--destructive
--border, --input, --ring
--popover, --popover-foreground
--chart-1, --chart-2, --chart-3, --chart-4, --chart-5
--country-color-default
--country-color-cote-divoire
--country-color-burkina-faso
--country-color-benin
--country-color-togo
--country-color-niger
```

#### ✅ Correct Usage:

```svelte
<div class="bg-background text-foreground">
	<div class="border border-border bg-card text-card-foreground">
		<span class="text-muted-foreground">Muted text</span>
		<div style="color: var(--chart-1)">Chart color</div>
	</div>
</div>
```

**Important for Charts/Visualizations:**

- Use `--foreground` for all text/labels (readable in both light and dark themes)
- Use `--border` for axis lines, grid lines, and borders
- Use `--popover` and `--popover-foreground` for tooltips
- Never hardcode colors like `#000000` or `#666666`

#### ❌ WRONG:

```svelte
<div class="bg-blue-500 text-white">
	<span class="text-gray-500">Muted</span>
</div>
```

### 4. Data Flow: Python → JSON → Svelte

**All data processing happens in Python scripts that generate static JSON files.**

#### Data Generation Workflow:

1. **Python scripts** (in `scripts/`) fetch data from Hugging Face
2. Scripts process data and generate JSON files
3. JSON files saved to **both** `static/data/` and `build/data/`
4. Svelte components fetch from `/data/[filename].json` using `fetch()`
5. All pages use `export const prerender = true;`

#### Python Scripts:

- `scripts/generate_index_entities.py` - Entity data and bar charts
- `scripts/generate_language_facets.py` - Language distribution data
- `scripts/generate_treemap.py` - Country treemap data
- `scripts/generate_wordcloud.py` - Word frequency data

#### ✅ Loading Data Pattern:

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

### 5. Visualization Library Preferences

**Prefer ECharts for new visualizations**, fall back to D3.js if needed.

#### Priority Order:

1. **ECharts** (preferred) - For new charts and standard visualizations
2. **D3.js** (current) - For custom/complex visualizations, word clouds
3. Avoid other charting libraries unless specifically needed

#### When to Use Each:

- **ECharts**: Bar charts, line charts, pie charts, scatter plots, standard charts
- **D3.js**: Custom treemaps, word clouds, force-directed graphs, unique visualizations

### 6. File and Folder Structure

```
src/
├── lib/
│   ├── components/
│   │   ├── ui/                    # shadcn-svelte components
│   │   ├── charts/                # Chart components (D3/ECharts)
│   │   ├── facets/                # Faceted visualization components
│   │   ├── app-sidebar.svelte     # Main navigation sidebar
│   │   ├── entities-table.svelte  # Data table component
│   │   ├── language-toggle.svelte # i18n toggle
│   │   ├── theme-toggle.svelte    # Dark/light mode
│   │   └── wordcloud.svelte       # Word cloud component
│   ├── stores/
│   │   ├── itemsStore.ts          # Global data store
│   │   └── translationStore.ts    # i18n store
│   └── types/                     # TypeScript type definitions
├── routes/
│   ├── +layout.svelte             # Root layout with sidebar
│   ├── +page.svelte               # Overview/dashboard page
│   ├── countries/+page.svelte     # Country treemap
│   ├── languages/+page.svelte     # Language pie charts
│   ├── index/+page.svelte         # Entity index with table
│   ├── timeline/+page.svelte      # Timeline view (placeholder)
│   ├── categories/+page.svelte    # Categories view (placeholder)
│   └── words/+page.svelte         # Word cloud view
└── app.css                        # Global styles with CSS variables

scripts/
├── generate_index_entities.py     # Index data generation
├── generate_language_facets.py    # Language facets
├── generate_treemap.py            # Treemap data
└── generate_wordcloud.py          # Word cloud data

static/data/                       # Static JSON files
build/data/                        # Built JSON files (copied)
```

### 7. Build and Development Commands

**Always use npm commands** for building and running:

```bash
# Development server
npm run dev

# Build static site (prerender all pages)
npm run build

# Preview production build
npm run preview

# Type checking
npm run check

# Format code
npm run format

# Lint
npm run lint

# Run tests
npm test

# Run E2E tests
npm run test:e2e
```

**Python Data Generation:**

```bash
# Install Python dependencies
cd scripts
pip install -r requirements.txt

# Run individual generators
python generate_index_entities.py
python generate_language_facets.py
python generate_treemap.py
python generate_wordcloud.py
```

### 8. Internationalization (i18n)

**The project is fully bilingual: English and French.** All user-facing text must be translatable.

#### Translation System:

- Uses a simple Svelte store-based system (`translationStore.ts`)
- Translations defined in `src/lib/stores/translationStore.ts`
- Language toggle component in header (`language-toggle.svelte`)
- Default language: English (`en`)
- Supported languages: `'en' | 'fr'`

#### Usage Pattern:

```svelte
<script>
	import { t, languageStore } from '$lib/stores/translationStore.js';
</script>

<h1>{$t('app.title')}</h1>
<p>{$t('stats.total_items_desc')}</p>

<!-- Check current language -->
{#if $languageStore === 'en'}
	<p>English content</p>
{:else}
	<p>Contenu français</p>
{/if}
```

#### Making Charts Reactive to Language Changes:

Charts and visualizations must update when the language changes. Use `$derived` or `$effect` with `$languageStore`:

```svelte
<script>
	import { t, languageStore } from '$lib/stores/translationStore.js';

	// Make labels reactive to language changes
	const categoryLabels = $derived(() => {
		const _ = $languageStore; // Track language changes
		return data.map((d) => $t(`category.${d.key}`));
	});

	// Or use $effect to re-render chart
	$effect(() => {
		if (chartInstance) {
			const _ = $languageStore; // Track language changes
			updateChart(); // Re-render with new translations
		}
	});
</script>
```

#### Adding New Translations:

1. Add translation keys to both `en` and `fr` objects in `translationStore.ts`
2. Use dot notation for namespacing (e.g., `'nav.overview'`, `'stats.total_items'`)
3. Support parameter substitution with `{0}`, `{1}`, etc.

```typescript
// In translationStore.ts
export const translations = {
	en: {
		'my.new_key': 'Hello {0}!'
	},
	fr: {
		'my.new_key': 'Bonjour {0}!'
	}
};

// In component
{
	$t('my.new_key', ['World']);
} // "Hello World!" or "Bonjour World!"
```

#### Important Rules:

- ❌ **NEVER** hardcode English-only text in components
- ✅ **ALWAYS** add translation keys for new user-facing text
- ✅ **ALWAYS** provide both English AND French translations
- ✅ Use the `$t()` function for all visible text
- ✅ Make charts/visualizations reactive to `$languageStore` changes
- ✅ Test with both languages when adding new features

### 9. Important Constraints

1. **Static Site Only** - All pages must use `export const prerender = true;`
2. **No Server-Side Routes** - No `+server.ts` files or API routes
3. **JSON Files Only** - Data must be in static JSON format
4. **No Dynamic Imports of Data** - All data loaded via `fetch()` from static files
5. **Bilingual Support Required** - All user-facing text must support English and French
6. **Mobile-First** - Always consider responsive design
7. **Accessibility** - Use semantic HTML and ARIA attributes
8. **TypeScript Strict** - Maintain type safety throughout

### 10. Common Patterns

#### Faceted Visualization Component:

```svelte
<script>
	import FacetPie from '$lib/components/facets/FacetPie.svelte';

	let facetData = $state([
		{ label: 'Category A', value: 100 },
		{ label: 'Category B', value: 50 }
	]);
</script>

<FacetPie title="Distribution" data={facetData} />
```

#### Table with Search and Sorting:

```svelte
<script>
	import * as Table from '$lib/components/ui/table/index.js';

	let rows = $state([]);
	let search = $state('');
	let sortKey = $state('name');
	let sortDir = $state('asc');

	const filtered = $derived(
		rows.filter((r) => r.name.toLowerCase().includes(search.toLowerCase()))
	);

	const sorted = $derived(
		[...filtered].sort((a, b) => {
			const result = a[sortKey] > b[sortKey] ? 1 : -1;
			return sortDir === 'asc' ? result : -result;
		})
	);
</script>
```

#### Loading States:

```svelte
<script>
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';

	let loading = $state(true);
	let data = $state(null);
</script>

{#if loading}
	<Skeleton class="h-8 w-full" />
{:else if data}
	<div>{data.content}</div>
{:else}
	<p class="text-muted-foreground">No data available</p>
{/if}
```

## Using MCP Servers for Documentation

### Svelte MCP (Primary for Svelte Development)

**ALWAYS use the Svelte MCP server when writing or editing Svelte code.** This is the official Svelte MCP server that provides:

- Official Svelte 5 and SvelteKit documentation
- Code validation and auto-fixing
- Component suggestions and best practices
- Playground link generation

#### Workflow for Svelte Development:

1. **Before writing Svelte code**: Use `list-sections` to find relevant documentation sections
2. **Review use cases**: Analyze the `use_cases` field to identify all relevant sections
3. **Fetch documentation**: Use `get-documentation` to retrieve ALL relevant sections at once
4. **Write your code**: Implement the component following Svelte 5 runes syntax
5. **Validate**: Use `svelte-autofixer` to check for issues and get suggestions
6. **Fix issues**: Apply the suggestions and re-validate
7. **Generate playground link** (optional): Offer the user a playground link to test the code

#### Example Workflow:

```typescript
// 1. List available sections
list - sections();

// 2. Get relevant documentation (e.g., for interactive components with state)
get - documentation({ section: ['$state', '$derived', '$effect', 'event-handlers'] });

// 3. Write component code

// 4. Validate the component
svelte -
	autofixer({
		code: '...',
		desired_svelte_version: 5,
		filename: 'MyComponent.svelte'
	});

// 5. Offer playground link after final version
playground -
	link({
		name: 'My Component Demo',
		tailwind: false,
		files: {
			'App.svelte': '...',
			'MyComponent.svelte': '...'
		}
	});
```

#### Critical Rules:

- ✅ **ALWAYS** use `list-sections` FIRST for any Svelte query
- ✅ **ALWAYS** analyze ALL `use_cases` to identify relevant sections
- ✅ **ALWAYS** use `svelte-autofixer` before sending Svelte code to the user
- ✅ **ALWAYS** fix issues identified by the autofixer
- ✅ **NEVER** write component files without validating with `svelte-autofixer`
- ✅ **ALWAYS** offer playground link for standalone components (not for files in the project)

### Context7 MCP (For Other Libraries)

Use Context7 MCP for documentation of other libraries (shadcn-svelte, ECharts, etc.):

1. **Use the Context7 MCP tools** to get up-to-date documentation
2. Don't rely on outdated training data
3. Always verify syntax against current library versions

Example queries:

- "Get shadcn-svelte component API"
- "Get ECharts configuration examples"
- "Get Tailwind CSS v4 documentation"

## Validation Checklist

Before completing any task, verify:

- ✅ Used Svelte MCP to fetch documentation and validate code
- ✅ Validated Svelte components with `svelte-autofixer` before delivery
- ✅ Using Svelte 5 runes (`$state`, `$derived`, `$props`, `$effect`)
- ✅ Using shadcn-svelte components for UI
- ✅ Using CSS variables from our theme (no hardcoded colors)
- ✅ Data loaded from static JSON files
- ✅ Page has `export const prerender = true;`
- ✅ All text uses `$t()` with translation keys (no hardcoded English text)
- ✅ Both English and French translations provided
- ✅ Responsive design (mobile-first)
- ✅ TypeScript types defined
- ✅ Accessibility attributes included

## Additional Notes

- **Dataset Source**: `fmadore/islam-west-africa-collection` on Hugging Face
- **Deployment**: Static site (can deploy to GitHub Pages, Netlify, Vercel, etc.)
- **Base Path**: Configured via `base` from `$app/paths` for subpath deployments
- **Mode Watcher**: Uses `mode-watcher` package for dark/light theme switching
- **State Management**: Primarily local component state, stores for global data

---

**Remember**: This is a static dashboard with Python-generated JSON data. All visualizations are client-side. When in doubt, check existing components for patterns before creating new ones.

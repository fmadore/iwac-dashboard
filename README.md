
# IWAC Database Overview Dashboard

A modern dashboard for the IWAC Database Overview, built with SvelteKit, shadcn-svelte, Svelte 5, and TypeScript.

## Overview

This dashboard provides an interactive visualization of the IWAC (International Workshop on Aspect Categories) database, featuring:
- Country distribution analysis
- Language statistics
- Timeline visualizations
- Document type breakdowns
- Multi-language support (English/French)

## Developing

Once you've installed dependencies with `npm install`, start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```


## Technology Stack

- **Framework**: SvelteKit with **Svelte 5** and TypeScript  
- **UI Components**: shadcn-svelte
- **Styling**: TailwindCSS
- **Icons**: Lucide Svelte
- **Testing**: Vitest + Playwright
- **Build Tool**: Vite

## Project Structure

```
src/
├── lib/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # shadcn-svelte components
│   │   ├── app-sidebar.svelte
│   │   ├── language-toggle.svelte
│   │   └── stats-card.svelte
│   ├── stores/             # Svelte stores for state management
│   │   ├── itemsStore.ts
│   │   └── translationStore.ts
│   └── types/              # TypeScript type definitions
│       └── index.ts
├── routes/                 # SvelteKit file-based routing
│   ├── +layout.svelte     # Main layout with sidebar
│   ├── +page.svelte       # Overview dashboard
│   └── countries/         # Country distribution page
└── app.css                # Global styles
```

## Building

To create a production version of the dashboard:

```bash
npm run build
```

You can preview the production build with `npm run preview`.


> **Note:** This project requires Svelte 5. Please ensure you are using Svelte 5 and follow the [migration guide](migration-guide-Svelte.txt) if upgrading from Svelte 4.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.

## Features

### Implemented ✅
- Dashboard layout with sidebar navigation
- Multi-language support (EN/FR)
- Country distribution with hierarchical view
- Loading states and error handling
- Responsive design

### In Progress 🔄
- Chart integration for visualizations
- Language distribution page
- Timeline analysis

### Planned 📋
- Export functionality (CSV, JSON)
- Advanced filtering
- Search capabilities
- Dark mode support

## Contributing

This project follows the migration roadmap outlined in `../Roadmap.md`. See the roadmap for current status and next steps.

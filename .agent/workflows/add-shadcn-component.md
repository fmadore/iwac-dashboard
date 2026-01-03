---
description: Add a new shadcn-svelte component
---

# Add shadcn-svelte Component

## Steps

1. Check available components at: https://next.shadcn-svelte.com/docs/components

2. Use the CLI to add the component:
   ```bash
   npx shadcn-svelte@next add [component-name]
   ```

   Example:
   ```bash
   npx shadcn-svelte@next add alert
   npx shadcn-svelte@next add progress
   npx shadcn-svelte@next add sonner
   ```

3. The component will be added to `src/lib/components/ui/[component-name]/`

4. Import and use in your Svelte files:
   ```svelte
   <script>
     import { Alert, AlertDescription, AlertTitle } from '$lib/components/ui/alert/index.js';
   </script>
   
   <Alert>
     <AlertTitle>Heads up!</AlertTitle>
     <AlertDescription>
       You can add components using the shadcn CLI.
     </AlertDescription>
   </Alert>
   ```

## Currently Installed Components

- badge
- button
- card
- chart
- data-table
- dialog
- dropdown-menu
- input
- label
- scroll-area
- select
- separator
- sheet
- sidebar
- skeleton
- slider
- table
- tabs
- toggle
- tooltip

## Configuration

The shadcn-svelte configuration is in `components.json`:
- Components path: `$lib/components/ui`
- Using Tailwind v4
- TypeScript enabled

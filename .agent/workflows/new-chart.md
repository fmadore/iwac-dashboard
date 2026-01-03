---
description: Create a new chart/visualization component
---

# Create New Chart Component

## Chart Library Priority
1. **LayerChart** - Preferred for new charts (Svelte-native)
2. **D3.js** - Complex custom visualizations
3. **ECharts** - Feature-rich charts with many options

## Steps

1. Create the component in `src/lib/components/charts/`:
   - Use naming convention: `MyChart.svelte`

2. Template for LayerChart:
   ```svelte
   <script lang="ts">
     import { Chart, Axis, Bars } from 'layerchart';
     import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
     
     interface Props {
       data: ChartDataItem[];
       class?: string;
     }
     
     let { data, class: className = '' }: Props = $props();
     
     // Force re-render on language change
     const chartKey = $derived(`chart-${languageStore.current}`);
   </script>
   
   {#key chartKey}
     <div class="h-[400px] w-full {className}">
       <Chart {data} x="category" y="value">
         <Axis position="bottom" format={(d) => d} />
         <Axis position="left" />
         <Bars fill="var(--chart-1)" />
       </Chart>
     </div>
   {/key}
   ```

3. Template for D3.js:
   ```svelte
   <script lang="ts">
     import * as d3 from 'd3-selection';
     import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
     
     interface Props {
       data: DataItem[];
     }
     
     let { data }: Props = $props();
     let container: HTMLDivElement;
     
     const chartKey = $derived(`chart-${languageStore.current}`);
     
     $effect(() => {
       if (container && data.length > 0) {
         renderChart();
       }
     });
     
     function renderChart() {
       // D3 rendering logic
       d3.select(container).selectAll('*').remove();
       // ... build chart
     }
   </script>
   
   {#key chartKey}
     <div bind:this={container} class="h-[400px] w-full"></div>
   {/key}
   ```

4. Use CSS variables for colors:
   ```javascript
   // ✅ Correct
   .attr('fill', 'var(--chart-1)')
   .attr('stroke', 'var(--border)')
   
   // ❌ Wrong
   .attr('fill', '#3b82f6')
   ```

5. Ensure accessibility:
   - Add `aria-label` for charts
   - Use `role="img"` for decorative visualizations
   - Provide text alternatives where appropriate

6. Type check:
   ```bash
   npm run check
   ```

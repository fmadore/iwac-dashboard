<script lang="ts">
  import { onMount } from 'svelte';
  import { select } from 'd3-selection';
  import { pie, arc } from 'd3-shape';
  import { scaleOrdinal } from 'd3-scale';
  import { interpolate } from 'd3-interpolate';
  import 'd3-transition';
  import {
    type ChartMargins,
    DEFAULT_MARGINS,
    getResponsiveDimensions,
    truncateText
  } from './utils.js';

  interface PieDataItem {
    label: string;
    value: number;
    color?: string;
  }

  interface Props {
    data: PieDataItem[];
    width?: number;
    height?: number;
    margins?: ChartMargins;
    innerRadius?: number;
    outerRadius?: number;
    cornerRadius?: number;
    padAngle?: number;
    animationDuration?: number;
    showLabels?: boolean;
    showValues?: boolean;
    maxLabelLength?: number;
  }

  let {
    data = [],
    width = 0,
    height = 400,
    margins = DEFAULT_MARGINS,
    innerRadius = 50,
    outerRadius = 150,
    cornerRadius = 4,
    padAngle = 0.02,
    animationDuration = 750,
    showLabels = true,
    showValues = true,
    maxLabelLength = 15
  }: Props = $props();

  let svgElement: SVGSVGElement;
  let containerElement: HTMLDivElement;
  let containerWidth = $state(0);
  let containerHeight = $state(0);

  // Color scale using your CSS variables
  const colorScale = scaleOrdinal([
    'var(--chart-1)',
    'var(--chart-2)',
    'var(--chart-3)',
    'var(--chart-4)',
    'var(--chart-5)'
  ]);

  // Reactive dimensions based on container size
  const dimensions = $derived(() => {
    const { width: responsiveWidth, height: responsiveHeight } = getResponsiveDimensions(
      containerWidth || width,
      height
    );
    return { width: responsiveWidth, height: responsiveHeight };
  });

  // Calculate chart center
  const center = $derived(() => ({
    x: dimensions().width / 2,
    y: dimensions().height / 2
  }));

  // Calculate responsive radii
  const radii = $derived(() => {
    const maxRadius = Math.min(dimensions().width, dimensions().height) / 2 - 40;
    const calculatedOuter = Math.min(outerRadius, maxRadius);
    const calculatedInner = Math.min(innerRadius, calculatedOuter - 20);
    
    return {
      inner: calculatedInner,
      outer: calculatedOuter
    };
  });

  // Pie generator
  const pieGenerator = $derived(() => 
    pie<PieDataItem>()
      .value(d => d.value)
      .padAngle(padAngle)
      .sort(null) // Maintain data order
  );

  // Arc generator for slices
  const arcGenerator = $derived(() => 
    arc()
      .innerRadius(radii().inner)
      .outerRadius(radii().outer)
      .cornerRadius(cornerRadius)
  );

  // Arc generator for labels (positioned outside)
  const labelArcGenerator = $derived(() => 
    arc()
      .innerRadius(radii().outer + 10)
      .outerRadius(radii().outer + 10)
  );

  // ResizeObserver for responsive behavior
  let resizeObserver: ResizeObserver | undefined;

  onMount(() => {
    if (containerElement) {
      resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const { width, height } = entry.contentRect;
          containerWidth = width;
          containerHeight = height;
        }
      });
      resizeObserver.observe(containerElement);
      
      // Initial size measurement
      const rect = containerElement.getBoundingClientRect();
      containerWidth = rect.width;
      containerHeight = rect.height;
    }

    return () => {
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
    };
  });

  // Update chart when data or dimensions change
  $effect(() => {
    if (svgElement && data.length > 0 && pieGenerator()) {
      updateChart();
    }
  });

  function updateChart() {
    if (!svgElement || !pieGenerator() || !arcGenerator()) return;

    const svg = select(svgElement);
    const pieData = pieGenerator()(data);
    
    // Clear previous content
    svg.selectAll('*').remove();

    // Create main group centered
    const g = svg
      .append('g')
      .attr('transform', `translate(${center().x},${center().y})`);

    // Create pie slices
    const slices = g.selectAll('.slice')
      .data(pieData)
      .enter()
      .append('g')
      .attr('class', 'slice');

    // Add paths for slices
    const paths = slices
      .append('path')
      .attr('fill', (d: any, i: number) => d.data.color || colorScale(i.toString()))
      .style('stroke', 'var(--background)')
      .style('stroke-width', '2px')
      .style('cursor', 'pointer')
      .attr('d', (d: any) => {
        // Start from collapsed state for animation
        const startArc = { startAngle: 0, endAngle: 0, innerRadius: radii().inner, outerRadius: radii().outer };
        return arcGenerator()(startArc);
      });

    // Animate slices
    paths
      .transition()
      .duration(animationDuration)
      .attr('d', (d: any) => arcGenerator()(d));

    // Add hover effects
    paths
      .on('mouseenter', function(event: MouseEvent, d: any) {
        select(this)
          .transition()
          .duration(200)
          .style('opacity', 0.8)
          .style('filter', 'brightness(1.1)');
        
        // Show tooltip
        showTooltip(event, d);
      })
      .on('mouseleave', function() {
        select(this)
          .transition()
          .duration(200)
          .style('opacity', 1)
          .style('filter', 'none');
        
        // Hide tooltip
        hideTooltip();
      })
      .on('mousemove', function(event: MouseEvent, d: any) {
        moveTooltip(event, d);
      });

    // Add labels if enabled
    if (showLabels && radii().outer > 60) {
      addLabels(slices, pieData);
    }

    // Add values if enabled
    if (showValues && radii().inner > 30) {
      addValues(slices, pieData);
    }
  }

  function addLabels(slices: any, pieData: any[]) {
    slices
      .append('text')
      .attr('dy', '0.35em')
      .attr('text-anchor', (d: any) => {
        const centroid = labelArcGenerator()(d);
        return centroid && centroid[0] > 0 ? 'start' : 'end';
      })
      .style('font-size', '12px')
      .style('font-weight', '500')
      .style('fill', 'var(--foreground)')
      .style('opacity', 0)
      .text((d: any) => truncateText(d.data.label, maxLabelLength))
      .attr('transform', (d: any) => {
        const centroid = labelArcGenerator()(d);
        return centroid ? `translate(${centroid})` : '';
      })
      .transition()
      .delay(animationDuration * 0.7)
      .duration(animationDuration * 0.3)
      .style('opacity', 1);
  }

  function addValues(slices: any, pieData: any[]) {
    slices
      .append('text')
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('fill', 'var(--card-foreground)')
      .style('opacity', 0)
      .text((d: any) => d.data.value)
      .attr('transform', (d: any) => {
        const centroid = arcGenerator().centroid(d);
        return `translate(${centroid})`;
      })
      .transition()
      .delay(animationDuration * 0.7)
      .duration(animationDuration * 0.3)
      .style('opacity', 1);
  }

  let tooltip: HTMLDivElement | null = null;

  function showTooltip(event: MouseEvent, d: any) {
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.style.position = 'absolute';
      tooltip.style.background = 'var(--popover)';
      tooltip.style.border = '1px solid var(--border)';
      tooltip.style.borderRadius = '6px';
      tooltip.style.padding = '8px 12px';
      tooltip.style.fontSize = '12px';
      tooltip.style.fontWeight = '500';
      tooltip.style.color = 'var(--popover-foreground)';
      tooltip.style.pointerEvents = 'none';
      tooltip.style.opacity = '0';
      tooltip.style.transition = 'opacity 0.2s';
      tooltip.style.zIndex = '1000';
      tooltip.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
      document.body.appendChild(tooltip);
    }

    const percentage = ((d.data.value / data.reduce((sum, item) => sum + item.value, 0)) * 100).toFixed(1);
    tooltip.innerHTML = `
      <div style="font-weight: 600; margin-bottom: 4px;">${d.data.label}</div>
      <div>Value: ${d.data.value}</div>
      <div>Percentage: ${percentage}%</div>
    `;
    
    moveTooltip(event, d);
    tooltip.style.opacity = '1';
  }

  function moveTooltip(event: MouseEvent, d: any) {
    if (!tooltip) return;
    
    tooltip.style.left = `${event.pageX + 10}px`;
    tooltip.style.top = `${event.pageY - 10}px`;
  }

  function hideTooltip() {
    if (tooltip) {
      tooltip.style.opacity = '0';
    }
  }

  // Cleanup tooltip on component destroy
  onMount(() => {
    return () => {
      if (tooltip && tooltip.parentNode) {
        tooltip.parentNode.removeChild(tooltip);
      }
    };
  });
</script>

<div 
  bind:this={containerElement} 
  class="w-full h-full min-h-[300px]"
  style="container-type: inline-size;"
>
  <svg
    bind:this={svgElement}
    width={dimensions().width}
    height={dimensions().height}
    class="w-full h-auto"
    style="max-width: 100%; height: auto;"
    viewBox={`0 0 ${dimensions().width} ${dimensions().height}`}
    role="img"
    aria-label="Pie chart showing data distribution"
  >
    {#if data.length === 0}
      <text
        x={dimensions().width / 2}
        y={dimensions().height / 2}
        text-anchor="middle"
        class="text-muted-foreground text-sm"
        fill="var(--muted-foreground)"
      >
        No data available
      </text>
    {/if}
  </svg>
</div>

<style>
  svg {
    overflow: visible;
  }
  
  :global(.slice path) {
    transition: opacity 0.2s ease, filter 0.2s ease;
  }
</style>
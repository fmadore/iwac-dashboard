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
    minSlicePercent?: number; // Minimum percentage for individual slices (others grouped)
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
    maxLabelLength = 15,
    minSlicePercent = 0.5 // Group slices smaller than 0.5% into "Others"
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

  // Process data to group small slices into "Others"
  const processedData = $derived(() => {
    if (!data || data.length === 0) return [];
    
    const total = data.reduce((sum, item) => sum + item.value, 0);
    
    // Sort data by value descending
    const sortedData = [...data].sort((a, b) => b.value - a.value);
    
    // For heavily skewed data (when top slice is >90%), show top 5 + others
    const topSlicePercent = (sortedData[0]?.value / total) * 100;
    
    if (topSlicePercent > 90) {
      // Show top 5 languages individually, group the rest
      const mainSlices = sortedData.slice(0, 5);
      const smallSlices = sortedData.slice(5);
      
      if (smallSlices.length > 0) {
        const othersValue = smallSlices.reduce((sum, item) => sum + item.value, 0);
        const othersSlice: PieDataItem = {
          label: `Others (${smallSlices.length} languages)`,
          value: othersValue,
          color: 'var(--muted-foreground)'
        };
        
        return [...mainSlices, othersSlice];
      }
      
      return mainSlices;
    }
    
    // For more balanced data, use the percentage threshold
    const threshold = (minSlicePercent / 100) * total;
    const mainSlices: PieDataItem[] = [];
    const smallSlices: PieDataItem[] = [];
    
    // Keep top 8 languages that are above threshold
    sortedData.forEach((item, index) => {
      if (index < 8 && item.value >= threshold) {
        mainSlices.push(item);
      } else if (item.value < threshold) {
        smallSlices.push(item);
      } else {
        mainSlices.push(item);
      }
    });
    
    // Only create "Others" group if we have more than 2 small slices
    if (smallSlices.length > 2) {
      const othersValue = smallSlices.reduce((sum, item) => sum + item.value, 0);
      const othersSlice: PieDataItem = {
        label: `Others (${smallSlices.length} languages)`,
        value: othersValue,
        color: 'var(--muted-foreground)'
      };
      
      return [...mainSlices, othersSlice];
    }
    
    return [...mainSlices, ...smallSlices];
  });

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

  // Calculate responsive radii (accounting for label space)
  const radii = $derived(() => {
    const labelSpace = showLabels ? 80 : 40; // Extra space for labels
    const maxRadius = Math.min(dimensions().width, dimensions().height) / 2 - labelSpace;
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

  // Arc generator for labels (positioned outside with better logic)
  const labelArcGenerator = $derived(() => 
    arc()
      .innerRadius(radii().outer + 20)
      .outerRadius(radii().outer + 20)
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
    if (svgElement && processedData().length > 0 && pieGenerator()) {
      updateChart();
    } else if (svgElement && processedData().length === 0) {
      // Clear chart when no data
      const svg = select(svgElement);
      svg.selectAll('*').remove();
    }
  });

  function updateChart() {
    if (!svgElement || !pieGenerator() || !arcGenerator()) return;

    const svg = select(svgElement);
    const pieData = pieGenerator()(processedData());
    
    // Clear previous content immediately to avoid deformation
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

    // Add paths for slices with immediate final state to avoid deformation
    const paths = slices
      .append('path')
      .attr('fill', (d: any, i: number) => d.data.color || colorScale(i.toString()))
      .style('stroke', 'var(--background)')
      .style('stroke-width', '2px')
      .style('cursor', 'pointer')
      .style('opacity', 0)
      .attr('d', (d: any) => arcGenerator()(d)); // Start with final shape

    // Simple fade-in animation instead of shape morphing
    paths
      .transition()
      .duration(animationDuration * 0.5) // Shorter duration
      .style('opacity', 1);

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

    // Add labels if enabled (check for sufficient space)
    if (showLabels && dimensions().width > 300) {
      addLabels(slices, pieData);
    }

    // Add values if enabled (only if inner radius allows)
    if (showValues && radii().inner > 25) {
      addValues(slices, pieData);
    }
  }

  function addLabels(slices: any, pieData: any[]) {
    // Only show labels if there's enough space
    if (radii().outer < 80 || pieData.length > 8) return;
    
    // Calculate label positions with proper spacing
    const labelRadius = radii().outer + 30;
    
    // Filter out very small slices for labeling (less than 0.5% gets no label)
    const total = pieData.reduce((sum, d) => sum + d.value, 0);
    const labelsToShow = pieData.filter(d => (d.value / total) >= 0.005); // 0.5% minimum
    
    // Sort pie data by angle to handle label positioning
    const sortedPieData = [...labelsToShow].sort((a, b) => {
      const midAngleA = (a.startAngle + a.endAngle) / 2;
      const midAngleB = (b.startAngle + b.endAngle) / 2;
      return midAngleA - midAngleB;
    });
    
    // Calculate initial label positions
    const labelPositions = sortedPieData.map(d => {
      const midAngle = (d.startAngle + d.endAngle) / 2;
      const labelX = Math.cos(midAngle - Math.PI / 2) * labelRadius;
      const labelY = Math.sin(midAngle - Math.PI / 2) * labelRadius;
      
      return {
        data: d,
        x: labelX,
        y: labelY,
        angle: midAngle,
        textAnchor: midAngle < Math.PI ? 'start' : 'end'
      };
    });
    
    // Add polylines connecting slices to labels (only for slices that get labels)
    slices
      .filter((d: any) => labelsToShow.includes(d))
      .append('polyline')
      .style('fill', 'none')
      .style('stroke', 'var(--muted-foreground)')
      .style('stroke-width', '1px')
      .style('opacity', 0)
      .attr('points', function(d: any) {
        const position = labelPositions.find(pos => pos.data === d);
        if (!position) return '';
        
        // Three points: slice centroid, arc edge, label position
        const sliceCentroid = arcGenerator().centroid(d);
        const arcEdge = labelArcGenerator().centroid(d);
        
        return [
          sliceCentroid,
          arcEdge,
          [position.x, position.y]
        ].map(point => point.join(',')).join(' ');
      })
      .transition()
      .delay(animationDuration * 0.4)
      .duration(animationDuration * 0.3)
      .style('opacity', 0.7);

    // Add labels (only for slices above threshold)
    slices
      .filter((d: any) => labelsToShow.includes(d))
      .append('text')
      .attr('dy', '0.35em')
      .style('font-size', '11px')
      .style('font-weight', '500')
      .style('fill', 'var(--foreground)')
      .style('opacity', 0)
      .text((d: any) => truncateText(d.data.label, maxLabelLength))
      .attr('text-anchor', function(d: any) {
        const position = labelPositions.find(pos => pos.data === d);
        return position ? position.textAnchor : 'middle';
      })
      .attr('transform', function(d: any) {
        const position = labelPositions.find(pos => pos.data === d);
        return position ? `translate(${position.x},${position.y})` : '';
      })
      .transition()
      .delay(animationDuration * 0.4)
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
      .delay(animationDuration * 0.3) // Shorter delay
      .duration(animationDuration * 0.2) // Shorter duration
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

    const percentage = ((d.data.value / processedData().reduce((sum, item) => sum + item.value, 0)) * 100).toFixed(1);
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
  class="w-full h-full min-h-[400px]"
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
    {#if processedData().length === 0}
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
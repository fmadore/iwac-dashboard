<script lang="ts">
	import { select } from 'd3-selection';
	import { axisBottom, axisLeft } from 'd3-axis';
	import 'd3-transition'; // This adds the transition methods to d3-selection
	import {
		type ChartDataItem,
		type ChartMargins,
		DEFAULT_MARGINS,
		getInnerDimensions,
		createXScale,
		createYScale,
		getResponsiveDimensions,
		truncateText
	} from './utils.js';

	interface Props {
		data: ChartDataItem[];
		width?: number;
		height?: number;
		margins?: ChartMargins;
		barColor?: string;
		hoverColor?: string;
		animationDuration?: number;
		maxLabelLength?: number;
	}

	let {
		data = [],
		width = 0,
		height = 400,
		margins = DEFAULT_MARGINS,
		barColor = 'var(--chart-1)',
		hoverColor = 'var(--chart-2)',
		animationDuration = 750,
		maxLabelLength = 10
	}: Props = $props();

	let svgElement: SVGSVGElement;
	let containerElement: HTMLDivElement;
	let containerWidth = $state(0);
	let containerHeight = $state(0);

	// Reactive dimensions based on container size
	const dimensions = $derived.by(() => {
		const { width: responsiveWidth, height: responsiveHeight } = getResponsiveDimensions(
			containerWidth || width,
			height
		);
		return { width: responsiveWidth, height: responsiveHeight };
	});

	const innerDimensions = $derived.by(() =>
		getInnerDimensions(dimensions.width, dimensions.height, margins)
	);

	const xScale = $derived.by(() =>
		data.length > 0 ? createXScale(data, innerDimensions.width) : null
	);

	const yScale = $derived.by(() =>
		data.length > 0 ? createYScale(data, innerDimensions.height) : null
	);

	// ResizeObserver for responsive behavior
	let resizeObserver: ResizeObserver | undefined;

	$effect(() => {
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

			return () => {
				resizeObserver?.disconnect();
			};
		}
	});

	// Update chart when data or dimensions change
	$effect(() => {
		if (svgElement && data.length > 0 && xScale && yScale) {
			updateChart();
		}
	});

	function updateChart() {
		if (!svgElement || !xScale || !yScale) return;

		const svg = select(svgElement);
		const { width: innerWidth, height: innerHeight } = innerDimensions;

		// Clear previous content
		svg.selectAll('*').remove();

		// Create main group with margins
		const g = svg.append('g').attr('transform', `translate(${margins.left},${margins.top})`);

		// Create and append X axis
		const xAxis = axisBottom(xScale).tickFormat((d) => truncateText(String(d), maxLabelLength));

		g.append('g')
			.attr('class', 'x-axis')
			.attr('transform', `translate(0,${innerHeight})`)
			.call(xAxis)
			.selectAll('text')
			.style('font-size', '12px')
			.style('fill', 'var(--foreground)');

		// Create and append Y axis
		const yAxis = axisLeft(yScale).ticks(Math.min(10, innerHeight / 40)); // Responsive tick count

		g.append('g')
			.attr('class', 'y-axis')
			.call(yAxis)
			.selectAll('text')
			.style('font-size', '12px')
			.style('fill', 'var(--foreground)');

		// Style axis lines and ticks
		g.selectAll('.domain').style('stroke', 'var(--muted-foreground)').style('opacity', 0.3);

		g.selectAll('.tick line').style('stroke', 'var(--muted-foreground)').style('opacity', 0.3);

		// Create bars
		const bars = g
			.selectAll('.bar')
			.data(data)
			.enter()
			.append('rect')
			.attr('class', 'bar')
			.attr('x', (d) => xScale(d.category) || 0)
			.attr('width', xScale.bandwidth())
			.attr('y', innerHeight) // Start from bottom for animation
			.attr('height', 0) // Start with height 0 for animation
			.style('fill', barColor)
			.style('cursor', 'pointer')
			.style('rx', '4')
			.style('ry', '4');

		// Animate bars
		if (typeof (bars as any).transition === 'function') {
			(bars as any)
				.transition()
				.duration(animationDuration)
				.attr('y', (d: any) => yScale(d.documents))
				.attr('height', (d: any) => innerHeight - yScale(d.documents));
		} else {
			bars
				.attr('y', (d) => yScale(d.documents))
				.attr('height', (d) => innerHeight - yScale(d.documents));
		}

		// Add hover effects
		bars
			.on('mouseenter', function (event, d) {
				select(this).style('fill', hoverColor);

				// Create tooltip
				const tooltip = g
					.append('g')
					.attr('class', 'tooltip')
					.attr(
						'transform',
						`translate(${(xScale(d.category) || 0) + xScale.bandwidth() / 2},${yScale(d.documents) - 10})`
					);

				const rect = tooltip
					.append('rect')
					.attr('x', -30)
					.attr('y', -25)
					.attr('width', 60)
					.attr('height', 20)
					.attr('rx', 4)
					.style('fill', 'var(--popover)')
					.style('stroke', 'var(--border)')
					.style('stroke-width', 1);

				tooltip
					.append('text')
					.attr('text-anchor', 'middle')
					.attr('y', -10)
					.style('fill', 'var(--popover-foreground)')
					.style('font-size', '12px')
					.style('font-weight', 'bold')
					.text(d.documents);
			})
			.on('mouseleave', function () {
				select(this).style('fill', barColor);

				g.select('.tooltip').remove();
			});
	}
</script>

<div
	bind:this={containerElement}
	class="h-full min-h-[300px] w-full border-border bg-card text-card-foreground"
	style="container-type: inline-size;"
>
	<svg
		bind:this={svgElement}
		width={dimensions.width}
		height={dimensions.height}
		class="h-auto w-full"
		style="max-width: 100%; height: auto;"
		viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
		role="img"
		aria-label="Bar chart showing document counts by category"
	>
		{#if data.length === 0}
			<text
				x={dimensions.width / 2}
				y={dimensions.height / 2}
				text-anchor="middle"
				class="text-sm text-muted-foreground"
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

	:global(.bar) {
		transition: fill 0.2s ease;
	}

	:global(.x-axis .domain),
	:global(.y-axis .domain) {
		stroke-width: 1;
	}

	:global(.tick line) {
		stroke-width: 1;
	}
</style>

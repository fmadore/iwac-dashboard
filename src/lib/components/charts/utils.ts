import { scaleLinear, scaleBand } from 'd3-scale';
import { max } from 'd3-array';
import type { ScaleLinear, ScaleBand } from 'd3-scale';

/**
 * Chart margin configuration
 */
export interface ChartMargins {
	top: number;
	right: number;
	bottom: number;
	left: number;
}

/**
 * Default margins for charts
 */
export const DEFAULT_MARGINS: ChartMargins = {
	top: 20,
	right: 20,
	bottom: 40,
	left: 60
};

/**
 * Chart data interface for bar charts
 */
export interface ChartDataItem {
	category: string;
	documents: number;
}

/**
 * Calculate inner dimensions based on container size and margins
 */
export function getInnerDimensions(
	width: number,
	height: number,
	margins: ChartMargins = DEFAULT_MARGINS
) {
	return {
		width: Math.max(0, width - margins.left - margins.right),
		height: Math.max(0, height - margins.top - margins.bottom)
	};
}

/**
 * Create a linear scale for the Y axis (values)
 */
export function createYScale(data: ChartDataItem[], height: number): ScaleLinear<number, number> {
	const maxValue = max(data, (d) => d.documents) || 0;
	return scaleLinear().domain([0, maxValue]).range([height, 0]).nice(); // Rounds the domain to nice round numbers
}

/**
 * Create a band scale for the X axis (categories)
 */
export function createXScale(
	data: ChartDataItem[],
	width: number,
	padding: number = 0.1
): ScaleBand<string> {
	return scaleBand()
		.domain(data.map((d) => d.category))
		.range([0, width])
		.padding(padding);
}

/**
 * Truncate text if it's longer than maxLength
 */
export function truncateText(text: string, maxLength: number = 10): string {
	if (text.length <= maxLength) return text;
	return `${text.slice(0, maxLength)}…`;
}

/**
 * Get responsive chart dimensions based on container size
 */
export function getResponsiveDimensions(
	containerWidth: number,
	containerHeight: number,
	aspectRatio: number = 16 / 9
): { width: number; height: number } {
	// Ensure minimum dimensions
	const minWidth = 300;
	const minHeight = 200;

	const width = Math.max(minWidth, containerWidth);
	let height = Math.max(minHeight, containerHeight);

	// If no height is provided, calculate based on aspect ratio
	if (containerHeight === 0) {
		height = Math.max(minHeight, width / aspectRatio);
	}

	return { width, height };
}

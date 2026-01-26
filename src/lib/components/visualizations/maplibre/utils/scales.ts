import { scaleSqrt, scaleLinear, scaleLog, scaleQuantile } from 'd3-scale';

/**
 * Create a radius scale for bubble markers
 */
export function createRadiusScale(
	domain: [number, number],
	range: [number, number] = [5, 40]
): (value: number) => number {
	return scaleSqrt().domain(domain).range(range);
}

/**
 * Create a color scale for bubble markers
 */
export function createColorScale(
	domain: [number, number],
	range: [string, string]
): (value: number) => string {
	return scaleLinear<string>().domain(domain).range(range);
}

/**
 * Create a color scale for choropleth maps
 */
export function createChoroplethScale(
	data: number[],
	colorRange: string[],
	mode: 'linear' | 'log' | 'quantile' = 'log'
): (value: number) => string {
	const validData = data.filter((v) => Number.isFinite(v) && v > 0);

	if (validData.length === 0) {
		return () => colorRange[0];
	}

	const min = Math.min(...validData);
	const max = Math.max(...validData);

	// Handle edge case where all values are the same
	if (min === max) {
		return () => colorRange[Math.floor(colorRange.length / 2)];
	}

	// Quantile mode: assigns discrete colors based on data distribution
	if (mode === 'quantile') {
		return scaleQuantile<string>().domain(validData).range(colorRange);
	}

	// For log and linear modes, create threshold-based scale for discrete colors
	const numBins = colorRange.length;

	if (mode === 'log') {
		const safeMin = Math.max(1, min);
		const safeMax = Math.max(safeMin + 1, max);
		const logMin = Math.log10(safeMin);
		const logMax = Math.log10(safeMax);
		const step = (logMax - logMin) / numBins;

		// Create thresholds in log space
		const thresholds = Array.from({ length: numBins - 1 }, (_, i) =>
			Math.pow(10, logMin + (i + 1) * step)
		);

		return (value: number) => {
			if (!Number.isFinite(value) || value <= 0) return colorRange[0];
			const idx = thresholds.findIndex((t) => value < t);
			return idx === -1 ? colorRange[colorRange.length - 1] : colorRange[idx];
		};
	}

	// Linear mode with thresholds
	const step = (max - min) / numBins;
	const thresholds = Array.from({ length: numBins - 1 }, (_, i) => min + (i + 1) * step);

	return (value: number) => {
		if (!Number.isFinite(value)) return colorRange[0];
		const idx = thresholds.findIndex((t) => value < t);
		return idx === -1 ? colorRange[colorRange.length - 1] : colorRange[idx];
	};
}

/**
 * Create line width scale for network edges
 */
export function createLineWidthScale(
	domain: [number, number],
	range: [number, number] = [1, 4]
): (value: number) => number {
	return scaleLinear().domain(domain).range(range);
}

/**
 * Create opacity scale
 */
export function createOpacityScale(
	domain: [number, number],
	range: [number, number] = [0.3, 0.8]
): (value: number) => number {
	return scaleLinear().domain(domain).range(range);
}

/**
 * Darken a hex color by a given amount (0-1)
 */
export function darkenColor(hex: string, amount: number): string {
	// Remove # if present
	const color = hex.replace('#', '');

	// Parse RGB
	const r = parseInt(color.substring(0, 2), 16);
	const g = parseInt(color.substring(2, 4), 16);
	const b = parseInt(color.substring(4, 6), 16);

	// Darken
	const newR = Math.round(r * (1 - amount));
	const newG = Math.round(g * (1 - amount));
	const newB = Math.round(b * (1 - amount));

	// Convert back to hex
	return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`;
}

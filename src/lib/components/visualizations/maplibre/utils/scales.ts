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

	if (mode === 'quantile') {
		return scaleQuantile<string>().domain(validData).range(colorRange);
	}

	const min = Math.min(...validData);
	const max = Math.max(...validData);

	if (mode === 'log') {
		const safeMin = Math.max(1, min);
		return scaleLog<string>()
			.domain([safeMin, max])
			.range([colorRange[0], colorRange[colorRange.length - 1]])
			.clamp(true);
	}

	return scaleLinear<string>()
		.domain([min, max])
		.range([colorRange[0], colorRange[colorRange.length - 1]]);
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

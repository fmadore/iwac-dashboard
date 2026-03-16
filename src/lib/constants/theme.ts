import { browser } from '$app/environment';

/**
 * CSS variable names for entity type colors.
 * These map to --entity-* variables in app.css.
 */
export const ENTITY_COLOR_VARS = {
	person: '--entity-person',
	organization: '--entity-organization',
	event: '--entity-event',
	subject: '--entity-subject',
	location: '--entity-location',
	topic: '--entity-topic',
	article: '--entity-article',
	author: '--entity-author',
	authority: '--entity-authority'
} as const;

/**
 * Edge relationship color CSS variables.
 * These map to --chart-* variables for typed edges.
 */
export const EDGE_COLOR_VARS = {
	part_of: '--chart-4',
	has_part: '--chart-12',
	related_to: '--chart-5',
	succeeded_by: '--chart-6',
	located_in: '--chart-7',
	co_occurs_with: '--muted-foreground',
	co_authored_with: '--chart-3'
} as const;

/**
 * Fallback hex colors for canvas/WebGL contexts where CSS variables
 * cannot be resolved (SSR or getComputedStyle failure).
 * Light-mode values — dark mode is handled via getComputedStyle at runtime.
 */
export const FALLBACK_COLORS: Record<string, string> = {
	'--primary': '#d97706',
	'--secondary': '#f5f7fa',
	'--background': '#f0f4f8',
	'--foreground': '#1a1a2e',
	'--muted': '#e5e9ed',
	'--muted-foreground': '#71717a',
	'--border': '#d4dbe4',
	'--card': '#ffffff',
	'--popover': '#ffffff',
	'--popover-foreground': '#1a1a2e',
	'--chart-1': '#c2610c',
	'--chart-2': '#2563eb',
	'--chart-3': '#0d9467',
	'--chart-4': '#7c3aed',
	'--chart-5': '#b8860b',
	'--chart-6': '#dc3414',
	'--chart-7': '#0891b2',
	'--chart-8': '#be185d',
	'--chart-9': '#65a30d',
	'--chart-10': '#15803d',
	'--chart-11': '#ea580c',
	'--chart-12': '#6d28d9',
	'--chart-13': '#0e7490',
	'--chart-14': '#a21caf',
	'--chart-15': '#ca8a04',
	'--chart-16': '#1d4ed8',
	'--entity-person': '#2563eb',
	'--entity-organization': '#7c3aed',
	'--entity-event': '#ea580c',
	'--entity-subject': '#0d9467',
	'--entity-location': '#be185d',
	'--entity-topic': '#0d9467',
	'--entity-article': '#2563eb',
	'--entity-author': '#2563eb',
	'--entity-authority': '#78716c'
};

/**
 * Resolve a CSS variable to a usable color string.
 * For canvas/Sigma.js contexts that need actual color values.
 */
export function resolveCSSColor(variable: string): string {
	if (!browser) return FALLBACK_COLORS[variable] || '#666666';

	const value = getComputedStyle(document.documentElement).getPropertyValue(variable).trim();
	if (!value) return FALLBACK_COLORS[variable] || '#666666';

	// If already a hex color, return directly
	if (value.startsWith('#')) return value;

	// For any non-hex value (oklch, hsl, rgb, color(srgb), etc.),
	// resolve via a temp element to get a browser-computed rgb() value
	const resolved = resolveColorViaElement(value);
	if (resolved) return resolved;

	// Last resort: use fallback
	return FALLBACK_COLORS[variable] || '#666666';
}

/**
 * Canvas element used for reliable CSS color → hex conversion.
 * Uses getImageData (pixel readback) which always returns sRGB 0-255
 * regardless of input color space (oklch, hsl, color(srgb), etc.).
 * Modern browsers preserve oklch() in fillStyle and getComputedStyle,
 * so pixel readback is the only reliable conversion path.
 */
let colorCanvas: HTMLCanvasElement | null = null;
let colorCtx: CanvasRenderingContext2D | null = null;

function getColorContext(): CanvasRenderingContext2D | null {
	if (!browser) return null;
	if (!colorCanvas) {
		colorCanvas = document.createElement('canvas');
		colorCanvas.width = 1;
		colorCanvas.height = 1;
		colorCtx = colorCanvas.getContext('2d', { willReadFrequently: true });
	}
	return colorCtx;
}

/**
 * Resolve any CSS color string to hex via canvas pixel readback.
 * This is the only approach that reliably converts oklch(), hsl(),
 * color(srgb ...) etc. to hex in modern browsers.
 */
function resolveColorViaElement(colorValue: string): string | null {
	if (!browser) return null;
	try {
		const ctx = getColorContext();
		if (!ctx) return null;

		ctx.clearRect(0, 0, 1, 1);
		ctx.fillStyle = colorValue;
		ctx.fillRect(0, 0, 1, 1);
		const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
		return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)}`;
	} catch {
		return null;
	}
}

/**
 * Convert an "rgb(r, g, b)" or "rgba(r, g, b, a)" string to hex.
 * Handles both comma-separated and space-separated formats.
 */
/** @internal Exported for testing */
export function rgbStringToHex(rgb: string): string {
	// Comma-separated: rgb(255, 128, 0) or rgba(255, 128, 0, 1)
	let match = rgb.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
	if (!match) {
		// Space-separated (modern syntax): rgb(255 128 0) or rgb(255 128 0 / 0.5)
		match = rgb.match(/rgba?\(\s*(\d+)\s+(\d+)\s+(\d+)/);
	}
	if (!match) {
		// color(srgb 0.5 0.3 0.1) — convert to 0-255 range
		const srgbMatch = rgb.match(/color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)/);
		if (srgbMatch) {
			const r = Math.round(parseFloat(srgbMatch[1]) * 255);
			const g = Math.round(parseFloat(srgbMatch[2]) * 255);
			const b = Math.round(parseFloat(srgbMatch[3]) * 255);
			if (!isNaN(r) && !isNaN(g) && !isNaN(b)) {
				return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)}`;
			}
		}
		return '#666666';
	}
	const r = parseInt(match[1], 10);
	const g = parseInt(match[2], 10);
	const b = parseInt(match[3], 10);
	if (isNaN(r) || isNaN(g) || isNaN(b)) return '#666666';
	return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)}`;
}

/**
 * Get resolved entity type colors as a hex map (for Sigma.js / canvas).
 */
export function getEntityColorsHex(): Record<string, string> {
	const colors: Record<string, string> = {};
	for (const [type, variable] of Object.entries(ENTITY_COLOR_VARS)) {
		colors[type] = resolveCSSColor(variable);
	}
	return colors;
}

/**
 * Get resolved edge type colors as a hex map.
 */
export function getEdgeColorsHex(): Record<string, string> {
	const colors: Record<string, string> = {};
	for (const [type, variable] of Object.entries(EDGE_COLOR_VARS)) {
		colors[type] = resolveCSSColor(variable);
	}
	return colors;
}

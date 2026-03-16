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
	'--foreground': '#1a1a2e',
	'--muted-foreground': '#71717a',
	'--background': '#f0f4f8',
	'--popover': '#ffffff',
	'--popover-foreground': '#1a1a2e',
	'--border': '#d4dbe4',
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

	// OKLCH values need conversion via a temp element
	if (value.startsWith('oklch(')) {
		return resolveOklchColor(value);
	}

	return value;
}

/**
 * Resolve an oklch() color string to a hex value via a temporary DOM element.
 */
function resolveOklchColor(oklchValue: string): string {
	if (!browser) return '#666666';
	const el = document.createElement('div');
	el.style.color = oklchValue;
	document.body.appendChild(el);
	const computed = getComputedStyle(el).color;
	document.body.removeChild(el);
	return rgbStringToHex(computed);
}

/**
 * Convert an "rgb(r, g, b)" or "rgba(r, g, b, a)" string to hex.
 */
function rgbStringToHex(rgb: string): string {
	const match = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
	if (!match) return '#666666';
	const r = parseInt(match[1], 10);
	const g = parseInt(match[2], 10);
	const b = parseInt(match[3], 10);
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

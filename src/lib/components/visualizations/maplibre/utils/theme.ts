import { browser } from '$app/environment';
import { FALLBACK_COLORS, resolveCSSColor } from '$lib/constants/theme.js';

/**
 * Check if the current theme is dark mode
 */
export function isDarkTheme(): boolean {
	if (!browser) return false;
	return document.documentElement.classList.contains('dark');
}

/**
 * Get CSS variable value from the document
 */
export function getCssVar(name: string, fallback: string): string {
	if (!browser) return fallback;
	const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
	return value || fallback;
}

/**
 * Get CSS variable as hex color for D3/MapLibre compatibility.
 * Delegates to the shared resolveCSSColor() which handles OKLCH-to-hex conversion.
 * Falls back to FALLBACK_COLORS or the provided fallback string.
 */
export function getCssVarAsHex(name: string, fallback: string): string {
	if (!browser) return FALLBACK_COLORS[name] || fallback;
	const resolved = resolveCSSColor(name);
	return ensureHex(resolved, FALLBACK_COLORS[name] || fallback);
}

/**
 * Create a MutationObserver that watches for theme changes on the document element
 * Returns a cleanup function to disconnect the observer
 */
export function createThemeObserver(callback: () => void): () => void {
	if (!browser) return () => {};

	const observer = new MutationObserver((mutations) => {
		for (const mutation of mutations) {
			if (mutation.attributeName === 'class') {
				callback();
				break;
			}
		}
	});

	observer.observe(document.documentElement, {
		attributes: true,
		attributeFilter: ['class']
	});

	return () => observer.disconnect();
}

/**
 * Get theme-aware colors for map elements.
 * Returns hex colors for D3/MapLibre compatibility.
 * Uses resolveCSSColor() at runtime which reads current computed styles
 * (including dark mode), with FALLBACK_COLORS as SSR/failure fallback.
 */
/**
 * Ensure a value is a valid hex color for MapLibre.
 * Guards against oklch/hsl/rgb strings leaking through.
 */
function ensureHex(color: string, fallback: string): string {
	return /^#[0-9a-fA-F]{6}$/.test(color) ? color : fallback;
}

export function getThemeColors() {
	return {
		primary: ensureHex(resolveCSSColor('--primary'), '#d97706'),
		secondary: ensureHex(resolveCSSColor('--chart-2'), '#2563eb'),
		background: ensureHex(resolveCSSColor('--background'), '#f0f4f8'),
		foreground: ensureHex(resolveCSSColor('--foreground'), '#1a1a2e'),
		muted: ensureHex(resolveCSSColor('--muted'), '#e5e9ed'),
		mutedForeground: ensureHex(resolveCSSColor('--muted-foreground'), '#71717a'),
		border: ensureHex(resolveCSSColor('--border'), '#d4dbe4'),
		card: ensureHex(resolveCSSColor('--card'), '#ffffff'),
		chart1: ensureHex(resolveCSSColor('--chart-1'), '#c2610c'),
		chart2: ensureHex(resolveCSSColor('--chart-2'), '#2563eb'),
		chart3: ensureHex(resolveCSSColor('--chart-3'), '#0d9467'),
		chart6: ensureHex(resolveCSSColor('--chart-6'), '#dc3414')
	};
}

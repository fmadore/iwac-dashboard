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
	return resolveCSSColor(name) || fallback;
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
export function getThemeColors() {
	return {
		primary: resolveCSSColor('--primary'),
		secondary: resolveCSSColor('--chart-2'),
		background: resolveCSSColor('--background'),
		foreground: resolveCSSColor('--foreground'),
		muted: resolveCSSColor('--muted'),
		mutedForeground: resolveCSSColor('--muted-foreground'),
		border: resolveCSSColor('--border'),
		card: resolveCSSColor('--card'),
		chart1: resolveCSSColor('--chart-1'),
		chart2: resolveCSSColor('--chart-2'),
		chart3: resolveCSSColor('--chart-3'),
		chart6: resolveCSSColor('--chart-6')
	};
}

import { browser } from '$app/environment';

/**
 * OKLCH to hex color mapping for theme variables.
 * MapLibre and D3 can't interpolate OKLCH colors, so we need hex equivalents.
 * These are pre-computed conversions of the OKLCH values in app.css.
 */
const THEME_COLOR_HEX: Record<string, { light: string; dark: string }> = {
	'--primary': { light: '#d97706', dark: '#e68a1a' },
	'--secondary': { light: '#f5f7fa', dark: '#1e2533' },
	'--background': { light: '#f0f4f8', dark: '#1a1f2e' },
	'--foreground': { light: '#1a2332', dark: '#f0f4f8' },
	'--muted': { light: '#e5e9ed', dark: '#2a3142' },
	'--muted-foreground': { light: '#5c6b7a', dark: '#9ca3af' },
	'--border': { light: '#dce1e8', dark: '#3a4252' },
	'--card': { light: '#ffffff', dark: '#242936' },
	'--chart-1': { light: '#d97706', dark: '#e68a1a' },
	'--chart-2': { light: '#3b82f6', dark: '#60a5fa' },
	'--chart-3': { light: '#10b981', dark: '#34d399' },
	'--chart-5': { light: '#eab308', dark: '#facc15' },
	'--chart-6': { light: '#ef4444', dark: '#f87171' },
	'--chart-11': { light: '#f59e0b', dark: '#fbbf24' },
	'--chart-15': { light: '#fcd34d', dark: '#fde68a' }
};

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
 * Uses pre-computed hex values since OKLCH can't be interpolated by D3.
 */
export function getCssVarAsHex(name: string, fallback: string): string {
	const themeHex = THEME_COLOR_HEX[name];
	if (themeHex) {
		return isDarkTheme() ? themeHex.dark : themeHex.light;
	}
	return fallback;
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
 */
export function getThemeColors() {
	const dark = isDarkTheme();
	return {
		primary: dark ? '#e68a1a' : '#d97706',
		secondary: dark ? '#60a5fa' : '#3b82f6',
		background: dark ? '#1a1f2e' : '#ffffff',
		foreground: dark ? '#f0f4f8' : '#1a2332',
		muted: dark ? '#2a3142' : '#e5e9ed',
		mutedForeground: dark ? '#9ca3af' : '#5c6b7a',
		border: dark ? '#3a4252' : '#dce1e8',
		card: dark ? '#242936' : '#ffffff',
		chart1: dark ? '#e68a1a' : '#d97706',
		chart2: dark ? '#60a5fa' : '#3b82f6',
		chart3: dark ? '#34d399' : '#10b981',
		chart6: dark ? '#f87171' : '#ef4444'
	};
}

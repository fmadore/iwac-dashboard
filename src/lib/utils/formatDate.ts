/**
 * Format a date string to a localized display string.
 *
 * @param dateStr - ISO date string (e.g., "2024-01-15") or null/undefined
 * @param locale - Current language code ("en" or "fr")
 * @returns Formatted date string, or empty string if input is falsy
 */
export function formatDate(dateStr: string | null | undefined, locale: string): string {
	if (!dateStr) return '';
	try {
		const date = new Date(dateStr);
		return date.toLocaleDateString(locale === 'fr' ? 'fr-FR' : 'en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	} catch {
		return dateStr;
	}
}

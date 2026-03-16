import { describe, it, expect } from 'vitest';
import { formatDate } from './formatDate.js';

describe('formatDate', () => {
	it('formats a valid ISO date string in English', () => {
		const result = formatDate('2024-01-15', 'en');
		expect(result).toContain('Jan');
		expect(result).toContain('15');
		expect(result).toContain('2024');
	});

	it('formats a valid ISO date string in French', () => {
		const result = formatDate('2024-01-15', 'fr');
		expect(result).toContain('janv');
		expect(result).toContain('15');
		expect(result).toContain('2024');
	});

	it('returns empty string for null input', () => {
		expect(formatDate(null, 'en')).toBe('');
	});

	it('returns empty string for undefined input', () => {
		expect(formatDate(undefined, 'en')).toBe('');
	});

	it('returns empty string for empty string input', () => {
		expect(formatDate('', 'en')).toBe('');
	});

	it('returns "Invalid Date" for an unparseable date string', () => {
		// new Date('not-a-date') produces Invalid Date, toLocaleDateString returns 'Invalid Date'
		expect(formatDate('not-a-date', 'en')).toBe('Invalid Date');
	});

	it('handles date-only strings (YYYY-MM-DD)', () => {
		const result = formatDate('2023-12-25', 'en');
		expect(result).toContain('Dec');
		expect(result).toContain('25');
		expect(result).toContain('2023');
	});

	it('handles ISO datetime strings', () => {
		const result = formatDate('2024-06-01T12:00:00Z', 'en');
		expect(result).toContain('Jun');
		expect(result).toContain('2024');
	});

	it('defaults to en-US locale for unknown language codes', () => {
		// Any non-'fr' locale falls through to 'en-US'
		const result = formatDate('2024-03-10', 'de');
		expect(result).toContain('Mar');
		expect(result).toContain('10');
		expect(result).toContain('2024');
	});

	it('formats different months correctly in French', () => {
		const result = formatDate('2024-07-04', 'fr');
		expect(result).toContain('juil');
		expect(result).toContain('4');
		expect(result).toContain('2024');
	});
});

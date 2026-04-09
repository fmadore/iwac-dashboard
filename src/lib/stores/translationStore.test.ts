import { describe, it, expect, beforeEach } from 'vitest';
import { translations, languageStore, t } from './translationStore.svelte.js';

// ── translations object structure ────────────────────────────────────

describe('translations object', () => {
	const enKeys = Object.keys(translations.en);
	const frKeys = Object.keys(translations.fr);

	it('has both en and fr locales', () => {
		expect(translations).toHaveProperty('en');
		expect(translations).toHaveProperty('fr');
	});

	it('en has a non-empty set of keys', () => {
		expect(enKeys.length).toBeGreaterThan(0);
	});

	it('fr has a non-empty set of keys', () => {
		expect(frKeys.length).toBeGreaterThan(0);
	});

	it('en and fr have the same set of keys', () => {
		const enSet = new Set(enKeys);
		const frSet = new Set(frKeys);

		const missingInFr = enKeys.filter((k) => !frSet.has(k));
		const missingInEn = frKeys.filter((k) => !enSet.has(k));

		expect(missingInFr, `Keys in EN but missing in FR: ${missingInFr.join(', ')}`).toEqual([]);
		expect(missingInEn, `Keys in FR but missing in EN: ${missingInEn.join(', ')}`).toEqual([]);
	});

	it('all EN values are non-empty strings', () => {
		const emptyKeys = enKeys.filter((k) => {
			const val = translations.en[k as keyof typeof translations.en];
			return typeof val !== 'string' || val.trim() === '';
		});
		expect(emptyKeys, `EN keys with empty values: ${emptyKeys.join(', ')}`).toEqual([]);
	});

	it('all FR values are non-empty strings', () => {
		const emptyKeys = frKeys.filter((k) => {
			const val = translations.fr[k as keyof typeof translations.fr];
			return typeof val !== 'string' || val.trim() === '';
		});
		expect(emptyKeys, `FR keys with empty values: ${emptyKeys.join(', ')}`).toEqual([]);
	});
});

// ── a11y translations ────────────────────────────────────────────────

describe('a11y translations', () => {
	const enKeys = Object.keys(translations.en);
	const frKeys = Object.keys(translations.fr);
	const a11yKeysEn = enKeys.filter((k) => k.startsWith('a11y.'));
	const a11yKeysFr = frKeys.filter((k) => k.startsWith('a11y.'));

	it('has a11y keys in EN', () => {
		expect(a11yKeysEn.length).toBeGreaterThan(0);
	});

	it('has the same a11y keys in both EN and FR', () => {
		expect(a11yKeysEn.sort()).toEqual(a11yKeysFr.sort());
	});

	it('all a11y EN values are non-empty strings', () => {
		for (const key of a11yKeysEn) {
			const val = translations.en[key as keyof typeof translations.en];
			expect(val, `a11y key "${key}" should be a non-empty string`).toBeTruthy();
			expect(typeof val).toBe('string');
		}
	});

	it('all a11y FR values are non-empty strings', () => {
		for (const key of a11yKeysFr) {
			const val = translations.fr[key as keyof typeof translations.fr];
			expect(val, `a11y key "${key}" should be a non-empty string`).toBeTruthy();
			expect(typeof val).toBe('string');
		}
	});
});

// ── Spot-check known translation pairs ───────────────────────────────

describe('spot-check known translations', () => {
	it('app.title is correct in EN', () => {
		expect(translations.en['app.title']).toBe('IWAC Dashboard');
	});

	it('app.title is correct in FR', () => {
		expect(translations.fr['app.title']).toBe('Tableau de bord');
	});

	it('nav.overview is correct in EN', () => {
		expect(translations.en['nav.overview']).toBe('Overview');
	});

	it('nav.overview is correct in FR', () => {
		expect(translations.fr['nav.overview']).toBe("Vue d'ensemble");
	});

	it('chart.documents exists in both languages', () => {
		expect(translations.en['chart.documents']).toBe('Documents');
		expect(translations.fr['chart.documents']).toBeTruthy();
	});
});

// ── languageStore ────────────────────────────────────────────────────

describe('languageStore', () => {
	beforeEach(() => {
		languageStore.set('en');
	});

	it('defaults to en after reset', () => {
		expect(languageStore.current).toBe('en');
	});

	it('can switch language to fr', () => {
		languageStore.set('fr');
		expect(languageStore.current).toBe('fr');
	});

	it('can switch language back to en', () => {
		languageStore.set('fr');
		languageStore.set('en');
		expect(languageStore.current).toBe('en');
	});
});

// ── t() function - key lookup ────────────────────────────────────────

describe('t() function - key lookup', () => {
	beforeEach(() => {
		languageStore.set('en');
	});

	it('returns English translation for a known key when language is en', () => {
		expect(t('app.title')).toBe('IWAC Dashboard');
	});

	it('returns French translation for a known key when language is fr', () => {
		languageStore.set('fr');
		expect(t('app.title')).toBe('Tableau de bord');
	});

	it('returns the key itself when translation is missing', () => {
		expect(t('nonexistent.key')).toBe('nonexistent.key');
	});

	it('handles nav keys (dot-notation)', () => {
		expect(t('nav.overview')).toBe('Overview');
		expect(t('nav.countries')).toBe('Countries');
	});

	it('handles deeply nested-looking keys', () => {
		expect(t('stats.total_items')).toBe('Total Items');
	});

	it('returns the key for an empty string key', () => {
		expect(t('')).toBe('');
	});
});

// ── t() function - parameter substitution ────────────────────────────

describe('t() function - parameter substitution', () => {
	beforeEach(() => {
		languageStore.set('en');
	});

	it('replaces {0} placeholder with provided parameter', () => {
		// 'chart.languages_in_type': 'Languages in {0}'
		expect(t('chart.languages_in_type', ['Press Article'])).toBe('Languages in Press Article');
	});

	it('replaces multiple placeholders {0} and {1}', () => {
		// 'chart.languages_in_type_country': 'Languages in {0} - {1}'
		expect(t('chart.languages_in_type_country', ['Book', 'Niger'])).toBe(
			'Languages in Book - Niger'
		);
	});

	it('returns translation without modification when no params given for placeholder text', () => {
		// 'chart.languages_in_type': 'Languages in {0}'
		expect(t('chart.languages_in_type')).toBe('Languages in {0}');
	});

	it('returns translation without modification when empty params array given', () => {
		expect(t('chart.languages_in_type', [])).toBe('Languages in {0}');
	});

	it('handles extra parameters gracefully (ignores them)', () => {
		// Only {0} placeholder exists but we pass two params
		expect(t('chart.languages_in_type', ['Press Article', 'Extra'])).toBe(
			'Languages in Press Article'
		);
	});

	it('works with French translations and parameters', () => {
		languageStore.set('fr');
		// FR: 'chart.others': 'Autres ({0})'
		expect(t('chart.others', ['5'])).toBe('Autres (5)');
	});

	it('handles numeric parameters by converting to string via template', () => {
		expect(t('chart.languages_count', [42])).toBe('42 languages');
	});
});

// ── t() function via languageStore.t() directly ─────────────────────

describe('languageStore.t() direct call', () => {
	beforeEach(() => {
		languageStore.set('en');
	});

	it('returns the same result as the exported t() function', () => {
		expect(languageStore.t('app.title')).toBe(t('app.title'));
	});

	it('handles parameters the same way', () => {
		expect(languageStore.t('chart.languages_in_type', ['Book'])).toBe(
			t('chart.languages_in_type', ['Book'])
		);
	});

	it('returns key for missing translation', () => {
		expect(languageStore.t('does.not.exist')).toBe('does.not.exist');
	});
});

// ── Translation key naming conventions ───────────────────────────────

describe('translation key conventions', () => {
	const allKeys = Object.keys(translations.en);

	it('all keys use dot notation (namespace.key format)', () => {
		const badKeys = allKeys.filter((k) => !k.includes('.'));
		expect(badKeys, `Keys without dot notation: ${badKeys.join(', ')}`).toEqual([]);
	});

	it('no keys have leading or trailing whitespace', () => {
		const badKeys = allKeys.filter((k) => k !== k.trim());
		expect(badKeys, `Keys with whitespace: ${badKeys.join(', ')}`).toEqual([]);
	});

	it('no duplicate keys in EN', () => {
		// Object.keys already deduplicates, but we can check the count
		// against a Set for sanity
		const unique = new Set(allKeys);
		expect(allKeys.length).toBe(unique.size);
	});
});

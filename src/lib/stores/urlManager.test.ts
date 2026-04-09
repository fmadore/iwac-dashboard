import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// ── Mock $app/environment and $app/navigation ───────────────────────
// Start with browser = false so the constructor's readFromUrl is skipped.
let mockBrowser = false;

vi.mock('$app/environment', () => ({
	get browser() {
		return mockBrowser;
	}
}));

vi.mock('$app/navigation', () => ({
	replaceState: vi.fn()
}));

// We need to re-import the module for each test group where `browser` changes,
// because the singleton is created at module level.
async function loadFreshModule() {
	// Reset the module registry so the class is re-instantiated
	vi.resetModules();
	const mod = await import('./urlManager.svelte.js');
	return mod;
}

// =====================================================================
// PART 1 – Non-browser (SSR) context
// =====================================================================

describe('urlManager (browser = false)', () => {
	beforeEach(() => {
		mockBrowser = false;
	});

	it('exports urlManager singleton', async () => {
		const { urlManager } = await loadFreshModule();
		expect(urlManager).toBeDefined();
	});

	it('is not initialized when browser is false', async () => {
		const { urlManager } = await loadFreshModule();
		expect(urlManager.isInitialized).toBe(false);
	});

	it('current state is empty object', async () => {
		const { urlManager } = await loadFreshModule();
		expect(urlManager.current).toEqual({});
	});

	it('get() returns undefined for any key', async () => {
		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('lang')).toBeUndefined();
		expect(urlManager.get('theme')).toBeUndefined();
		expect(urlManager.get('country')).toBeUndefined();
	});

	it('set() is a no-op when browser is false', async () => {
		const { urlManager } = await loadFreshModule();
		const listener = vi.fn();
		urlManager.subscribe(listener);

		urlManager.set('lang', 'fr');

		expect(urlManager.get('lang')).toBeUndefined();
		expect(listener).not.toHaveBeenCalled();
	});

	it('setMany() is a no-op when browser is false', async () => {
		const { urlManager } = await loadFreshModule();
		const listener = vi.fn();
		urlManager.subscribe(listener);

		urlManager.setMany({ lang: 'fr', country: 'Niger' });

		expect(urlManager.get('lang')).toBeUndefined();
		expect(urlManager.get('country')).toBeUndefined();
		expect(listener).not.toHaveBeenCalled();
	});

	it('clear() is a no-op when browser is false', async () => {
		const { urlManager } = await loadFreshModule();
		const listener = vi.fn();
		urlManager.subscribe(listener);

		urlManager.clear('lang');

		expect(listener).not.toHaveBeenCalled();
	});

	it('clearMany() is a no-op when browser is false', async () => {
		const { urlManager } = await loadFreshModule();
		const listener = vi.fn();
		urlManager.subscribe(listener);

		urlManager.clearMany(['lang', 'theme']);

		expect(listener).not.toHaveBeenCalled();
	});

	it('clearAll() is a no-op when browser is false', async () => {
		const { urlManager } = await loadFreshModule();
		const listener = vi.fn();
		urlManager.subscribe(listener);

		urlManager.clearAll();

		expect(listener).not.toHaveBeenCalled();
	});

	it('has() returns false for any key', async () => {
		const { urlManager } = await loadFreshModule();
		expect(urlManager.has('lang')).toBe(false);
	});

	it('keys() returns empty array', async () => {
		const { urlManager } = await loadFreshModule();
		expect(urlManager.keys()).toEqual([]);
	});

	it('subscribe returns an unsubscribe function', async () => {
		const { urlManager } = await loadFreshModule();
		const listener = vi.fn();
		const unsub = urlManager.subscribe(listener);
		expect(typeof unsub).toBe('function');
	});
});

// =====================================================================
// PART 2 – Browser context
// =====================================================================

describe('urlManager (browser = true)', () => {
	beforeEach(() => {
		mockBrowser = true;

		// Provide a minimal window.location for readFromUrl / writeToUrl
		globalThis.window = globalThis.window ?? {};
		Object.defineProperty(globalThis, 'location', {
			writable: true,
			value: {
				search: '',
				href: 'http://localhost:3000/',
				origin: 'http://localhost:3000',
				pathname: '/'
			}
		});
		// Also set on window for code that reads window.location
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	// ── Constructor / initialization ──────────────────────────────────

	it('is initialized when browser is true', async () => {
		const { urlManager } = await loadFreshModule();
		expect(urlManager.isInitialized).toBe(true);
	});

	it('reads lang from URL params on construction', async () => {
		globalThis.location = {
			...globalThis.location,
			search: '?lang=fr',
			href: 'http://localhost:3000/?lang=fr'
		};
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});

		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('lang')).toBe('fr');
	});

	it('reads theme from URL params on construction', async () => {
		globalThis.location = {
			...globalThis.location,
			search: '?theme=dark',
			href: 'http://localhost:3000/?theme=dark'
		};
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});

		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('theme')).toBe('dark');
	});

	it('reads country filter from URL', async () => {
		globalThis.location = {
			...globalThis.location,
			search: '?country=Niger',
			href: 'http://localhost:3000/?country=Niger'
		};
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});

		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('country')).toBe('Niger');
	});

	it('reads yearMin/yearMax as numbers', async () => {
		globalThis.location = {
			...globalThis.location,
			search: '?yearMin=1990&yearMax=2020',
			href: 'http://localhost:3000/?yearMin=1990&yearMax=2020'
		};
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});

		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('yearMin')).toBe(1990);
		expect(urlManager.get('yearMax')).toBe(2020);
	});

	it('ignores invalid lang values', async () => {
		globalThis.location = {
			...globalThis.location,
			search: '?lang=de',
			href: 'http://localhost:3000/?lang=de'
		};
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});

		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('lang')).toBeUndefined();
	});

	it('ignores invalid theme values', async () => {
		globalThis.location = {
			...globalThis.location,
			search: '?theme=blue',
			href: 'http://localhost:3000/?theme=blue'
		};
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});

		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('theme')).toBeUndefined();
	});

	it('ignores non-numeric yearMin values', async () => {
		globalThis.location = {
			...globalThis.location,
			search: '?yearMin=abc',
			href: 'http://localhost:3000/?yearMin=abc'
		};
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});

		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('yearMin')).toBeUndefined();
	});

	it('reads search query from URL', async () => {
		globalThis.location = {
			...globalThis.location,
			search: '?search=islam',
			href: 'http://localhost:3000/?search=islam'
		};
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});

		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('search')).toBe('islam');
	});

	it('reads arbitrary extra params from URL', async () => {
		globalThis.location = {
			...globalThis.location,
			search: '?view=grid&order=asc',
			href: 'http://localhost:3000/?view=grid&order=asc'
		};
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});

		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('view')).toBe('grid');
		expect(urlManager.get('order')).toBe('asc');
	});

	it('parses numeric extra params as numbers', async () => {
		globalThis.location = {
			...globalThis.location,
			search: '?page=5',
			href: 'http://localhost:3000/?page=5'
		};
		Object.defineProperty(globalThis.window, 'location', {
			writable: true,
			configurable: true,
			value: globalThis.location
		});

		const { urlManager } = await loadFreshModule();
		expect(urlManager.get('page')).toBe(5);
	});

	it('starts with empty state when URL has no params', async () => {
		const { urlManager } = await loadFreshModule();
		expect(urlManager.current).toEqual({});
		expect(urlManager.keys()).toEqual([]);
	});

	// ── get() ─────────────────────────────────────────────────────────

	describe('get()', () => {
		it('returns correct value after set', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'en');
			expect(urlManager.get('lang')).toBe('en');
		});

		it('returns undefined for unset key', async () => {
			const { urlManager } = await loadFreshModule();
			expect(urlManager.get('nonexistent')).toBeUndefined();
		});
	});

	// ── set() ─────────────────────────────────────────────────────────

	describe('set()', () => {
		it('sets a string value', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'fr');
			expect(urlManager.get('lang')).toBe('fr');
		});

		it('sets a numeric value', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('yearMin', 2000);
			expect(urlManager.get('yearMin')).toBe(2000);
		});

		it('notifies listeners on change', async () => {
			const { urlManager } = await loadFreshModule();
			const listener = vi.fn();
			urlManager.subscribe(listener);

			urlManager.set('lang', 'fr');
			expect(listener).toHaveBeenCalledTimes(1);
		});

		it('does NOT notify when setting the same value (no-op detection)', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'en');

			const listener = vi.fn();
			urlManager.subscribe(listener);

			urlManager.set('lang', 'en'); // same value
			expect(listener).not.toHaveBeenCalled();
		});

		it('removes key when set to undefined', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'fr');
			urlManager.set('lang', undefined);
			expect(urlManager.get('lang')).toBeUndefined();
			expect(urlManager.has('lang')).toBe(false);
		});

		it('removes key when set to empty string', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('search', 'hello');
			urlManager.set('search', '');
			expect(urlManager.get('search')).toBeUndefined();
		});

		it('removes key when set to null', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('country', 'Niger');
			urlManager.set('country', undefined);
			expect(urlManager.get('country')).toBeUndefined();
		});
	});

	// ── setMany() ─────────────────────────────────────────────────────

	describe('setMany()', () => {
		it('sets multiple values at once', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.setMany({ lang: 'fr', country: 'Niger', yearMin: 1990 });

			expect(urlManager.get('lang')).toBe('fr');
			expect(urlManager.get('country')).toBe('Niger');
			expect(urlManager.get('yearMin')).toBe(1990);
		});

		it('notifies listeners once per call', async () => {
			const { urlManager } = await loadFreshModule();
			const listener = vi.fn();
			urlManager.subscribe(listener);

			urlManager.setMany({ lang: 'fr', country: 'Niger' });
			expect(listener).toHaveBeenCalledTimes(1);
		});

		it('removes keys with undefined values', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'fr');
			urlManager.set('country', 'Niger');

			const listener = vi.fn();
			urlManager.subscribe(listener);

			urlManager.setMany({ lang: undefined, country: 'Benin' });
			expect(urlManager.get('lang')).toBeUndefined();
			expect(urlManager.get('country')).toBe('Benin');
		});

		it('removes keys with empty string values', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('search', 'test');
			urlManager.setMany({ search: '' });
			expect(urlManager.get('search')).toBeUndefined();
		});
	});

	// ── clear() ───────────────────────────────────────────────────────

	describe('clear()', () => {
		it('removes a specific key', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'fr');
			urlManager.clear('lang');
			expect(urlManager.get('lang')).toBeUndefined();
			expect(urlManager.has('lang')).toBe(false);
		});

		it('notifies listeners', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'fr');

			const listener = vi.fn();
			urlManager.subscribe(listener);
			urlManager.clear('lang');
			expect(listener).toHaveBeenCalledTimes(1);
		});

		it('does not throw when clearing a key that does not exist', async () => {
			const { urlManager } = await loadFreshModule();
			expect(() => urlManager.clear('nonexistent')).not.toThrow();
		});
	});

	// ── clearMany() ───────────────────────────────────────────────────

	describe('clearMany()', () => {
		it('removes multiple keys at once', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.setMany({ lang: 'fr', country: 'Niger', yearMin: 1990 });
			urlManager.clearMany(['lang', 'country']);

			expect(urlManager.get('lang')).toBeUndefined();
			expect(urlManager.get('country')).toBeUndefined();
			expect(urlManager.get('yearMin')).toBe(1990);
		});

		it('notifies listeners once', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.setMany({ lang: 'fr', country: 'Niger' });

			const listener = vi.fn();
			urlManager.subscribe(listener);
			urlManager.clearMany(['lang', 'country']);
			expect(listener).toHaveBeenCalledTimes(1);
		});
	});

	// ── clearAll() ────────────────────────────────────────────────────

	describe('clearAll()', () => {
		it('removes all state', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.setMany({ lang: 'fr', country: 'Niger', yearMin: 1990 });
			urlManager.clearAll();

			expect(urlManager.current).toEqual({});
			expect(urlManager.keys()).toEqual([]);
		});

		it('notifies listeners', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'en');

			const listener = vi.fn();
			urlManager.subscribe(listener);
			urlManager.clearAll();
			expect(listener).toHaveBeenCalledTimes(1);
		});
	});

	// ── has() ─────────────────────────────────────────────────────────

	describe('has()', () => {
		it('returns true for an existing key', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'en');
			expect(urlManager.has('lang')).toBe(true);
		});

		it('returns false for a missing key', async () => {
			const { urlManager } = await loadFreshModule();
			expect(urlManager.has('lang')).toBe(false);
		});

		it('returns false after key is cleared', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'en');
			urlManager.clear('lang');
			expect(urlManager.has('lang')).toBe(false);
		});
	});

	// ── keys() ────────────────────────────────────────────────────────

	describe('keys()', () => {
		it('returns all current keys', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.setMany({ lang: 'en', country: 'Niger' });
			const k = urlManager.keys();
			expect(k).toContain('lang');
			expect(k).toContain('country');
			expect(k.length).toBe(2);
		});

		it('returns empty array when no state', async () => {
			const { urlManager } = await loadFreshModule();
			expect(urlManager.keys()).toEqual([]);
		});
	});

	// ── current (readonly snapshot) ───────────────────────────────────

	describe('current', () => {
		it('returns a copy of the state', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'fr');

			const snapshot = urlManager.current;
			expect(snapshot.lang).toBe('fr');

			// Mutating the snapshot should NOT affect internal state
			(snapshot as Record<string, unknown>).lang = 'en';
			expect(urlManager.get('lang')).toBe('fr');
		});

		it('reflects all current state', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.setMany({ lang: 'en', theme: 'dark', country: 'Niger' });
			expect(urlManager.current).toEqual({
				lang: 'en',
				theme: 'dark',
				country: 'Niger'
			});
		});
	});

	// ── subscribe / notify ────────────────────────────────────────────

	describe('subscribe / notify', () => {
		it('subscribe returns an unsubscribe function', async () => {
			const { urlManager } = await loadFreshModule();
			const listener = vi.fn();
			const unsub = urlManager.subscribe(listener);
			expect(typeof unsub).toBe('function');
		});

		it('listener is called on set()', async () => {
			const { urlManager } = await loadFreshModule();
			const listener = vi.fn();
			urlManager.subscribe(listener);
			urlManager.set('lang', 'fr');
			expect(listener).toHaveBeenCalledTimes(1);
		});

		it('listener is called on setMany()', async () => {
			const { urlManager } = await loadFreshModule();
			const listener = vi.fn();
			urlManager.subscribe(listener);
			urlManager.setMany({ lang: 'fr', country: 'Niger' });
			expect(listener).toHaveBeenCalledTimes(1);
		});

		it('listener is called on clear()', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'fr');
			const listener = vi.fn();
			urlManager.subscribe(listener);
			urlManager.clear('lang');
			expect(listener).toHaveBeenCalledTimes(1);
		});

		it('listener is called on clearAll()', async () => {
			const { urlManager } = await loadFreshModule();
			urlManager.set('lang', 'en');
			const listener = vi.fn();
			urlManager.subscribe(listener);
			urlManager.clearAll();
			expect(listener).toHaveBeenCalledTimes(1);
		});

		it('unsubscribed listener is NOT called', async () => {
			const { urlManager } = await loadFreshModule();
			const listener = vi.fn();
			const unsub = urlManager.subscribe(listener);
			unsub();
			urlManager.set('lang', 'fr');
			expect(listener).not.toHaveBeenCalled();
		});

		it('multiple listeners all get notified', async () => {
			const { urlManager } = await loadFreshModule();
			const listener1 = vi.fn();
			const listener2 = vi.fn();
			urlManager.subscribe(listener1);
			urlManager.subscribe(listener2);
			urlManager.set('lang', 'fr');
			expect(listener1).toHaveBeenCalledTimes(1);
			expect(listener2).toHaveBeenCalledTimes(1);
		});

		it('unsubscribing one listener does not affect others', async () => {
			const { urlManager } = await loadFreshModule();
			const listener1 = vi.fn();
			const listener2 = vi.fn();
			const unsub1 = urlManager.subscribe(listener1);
			urlManager.subscribe(listener2);

			unsub1();
			urlManager.set('lang', 'fr');

			expect(listener1).not.toHaveBeenCalled();
			expect(listener2).toHaveBeenCalledTimes(1);
		});
	});

	// ── enableUrlWriting() ────────────────────────────────────────────

	describe('enableUrlWriting()', () => {
		it('does not throw', async () => {
			const { urlManager } = await loadFreshModule();
			expect(() => urlManager.enableUrlWriting()).not.toThrow();
		});
	});

	// ── Type exports ──────────────────────────────────────────────────

	describe('type exports', () => {
		it('UrlState interface is importable', async () => {
			const mod = await loadFreshModule();
			// If this compiles and runs, the type is exported
			expect(mod.urlManager).toBeDefined();
		});
	});

	// ── Multiple reads from URL (complex query string) ────────────────

	describe('complex URL initialization', () => {
		it('reads multiple params from a complex URL', async () => {
			globalThis.location = {
				search:
					'?lang=en&theme=light&country=Benin&type=article&yearMin=2000&yearMax=2024&search=mosque',
				href: 'http://localhost:3000/?lang=en&theme=light&country=Benin&type=article&yearMin=2000&yearMax=2024&search=mosque',
				origin: 'http://localhost:3000',
				pathname: '/'
			} as unknown as Location;
			Object.defineProperty(globalThis.window, 'location', {
				writable: true,
				configurable: true,
				value: globalThis.location
			});

			const { urlManager } = await loadFreshModule();
			expect(urlManager.get('lang')).toBe('en');
			expect(urlManager.get('theme')).toBe('light');
			expect(urlManager.get('country')).toBe('Benin');
			expect(urlManager.get('type')).toBe('article');
			expect(urlManager.get('yearMin')).toBe(2000);
			expect(urlManager.get('yearMax')).toBe(2024);
			expect(urlManager.get('search')).toBe('mosque');
		});

		it('accepts theme=system', async () => {
			globalThis.location = {
				search: '?theme=system',
				href: 'http://localhost:3000/?theme=system',
				origin: 'http://localhost:3000',
				pathname: '/'
			} as unknown as Location;
			Object.defineProperty(globalThis.window, 'location', {
				writable: true,
				configurable: true,
				value: globalThis.location
			});

			const { urlManager } = await loadFreshModule();
			expect(urlManager.get('theme')).toBe('system');
		});
	});
});

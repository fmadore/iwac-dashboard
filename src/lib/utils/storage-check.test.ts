import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// We need fresh module imports to reset the `storageAvailable` cache
async function loadFreshModule() {
	vi.resetModules();
	return await import('./storage-check.js');
}

// =====================================================================
// Helper: create a mock localStorage
// =====================================================================
function createMockStorage(): Storage {
	const store = new Map<string, string>();
	return {
		getItem: vi.fn((key: string) => store.get(key) ?? null),
		setItem: vi.fn((key: string, value: string) => {
			store.set(key, value);
		}),
		removeItem: vi.fn((key: string) => {
			store.delete(key);
		}),
		clear: vi.fn(() => store.clear()),
		get length() {
			return store.size;
		},
		key: vi.fn((index: number) => {
			const keys = [...store.keys()];
			return keys[index] ?? null;
		})
	};
}

function createThrowingStorage(): Storage {
	return {
		getItem: vi.fn(() => {
			throw new DOMException('Blocked', 'SecurityError');
		}),
		setItem: vi.fn(() => {
			throw new DOMException('Blocked', 'SecurityError');
		}),
		removeItem: vi.fn(() => {
			throw new DOMException('Blocked', 'SecurityError');
		}),
		clear: vi.fn(() => {
			throw new DOMException('Blocked', 'SecurityError');
		}),
		length: 0,
		key: vi.fn(() => null)
	};
}

// =====================================================================
// isStorageAvailable()
// =====================================================================

describe('isStorageAvailable()', () => {
	let originalLocalStorage: Storage;

	beforeEach(() => {
		originalLocalStorage = globalThis.localStorage;
	});

	afterEach(() => {
		// Restore original localStorage
		Object.defineProperty(globalThis, 'localStorage', {
			value: originalLocalStorage,
			writable: true,
			configurable: true
		});
	});

	it('returns true when localStorage is accessible', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { isStorageAvailable } = await loadFreshModule();
		expect(isStorageAvailable()).toBe(true);
	});

	it('returns false when localStorage throws', async () => {
		const throwingStorage = createThrowingStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: throwingStorage,
			writable: true,
			configurable: true
		});

		const { isStorageAvailable } = await loadFreshModule();
		expect(isStorageAvailable()).toBe(false);
	});

	it('caches the result (only probes once)', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { isStorageAvailable } = await loadFreshModule();

		// First call probes
		isStorageAvailable();
		// Second call should use cache
		isStorageAvailable();

		// setItem should have been called only once (the test probe)
		expect(mockStorage.setItem).toHaveBeenCalledTimes(1);
	});

	it('uses __storage_test__ as the probe key', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { isStorageAvailable } = await loadFreshModule();
		isStorageAvailable();

		expect(mockStorage.setItem).toHaveBeenCalledWith('__storage_test__', '__storage_test__');
		expect(mockStorage.removeItem).toHaveBeenCalledWith('__storage_test__');
	});

	it('cleans up the probe key after testing', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { isStorageAvailable } = await loadFreshModule();
		isStorageAvailable();

		expect(mockStorage.removeItem).toHaveBeenCalledWith('__storage_test__');
	});

	it('returns boolean type', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { isStorageAvailable } = await loadFreshModule();
		const result = isStorageAvailable();
		expect(typeof result).toBe('boolean');
	});

	it('returns false when localStorage is undefined', async () => {
		Object.defineProperty(globalThis, 'localStorage', {
			get() {
				throw new ReferenceError('localStorage is not defined');
			},
			configurable: true
		});

		const { isStorageAvailable } = await loadFreshModule();
		expect(isStorageAvailable()).toBe(false);
	});
});

// =====================================================================
// isInIframe()
// =====================================================================

describe('isInIframe()', () => {
	const hasNativeWindow = typeof globalThis.window !== 'undefined';
	let originalWindow: typeof globalThis.window;

	beforeEach(() => {
		originalWindow = globalThis.window;
		// Ensure a window-like object exists for testing
		if (!hasNativeWindow) {
			const fakeWindow = {} as typeof globalThis.window;
			Object.defineProperty(fakeWindow, 'self', {
				value: fakeWindow,
				writable: true,
				configurable: true
			});
			Object.defineProperty(fakeWindow, 'top', {
				value: fakeWindow,
				writable: true,
				configurable: true
			});
			globalThis.window = fakeWindow;
		}
	});

	afterEach(() => {
		if (!hasNativeWindow) {
			globalThis.window = originalWindow;
		} else {
			// Restore original self/top on native window
			Object.defineProperty(globalThis.window, 'self', {
				value: globalThis.window,
				writable: true,
				configurable: true
			});
			Object.defineProperty(globalThis.window, 'top', {
				value: globalThis.window,
				writable: true,
				configurable: true
			});
		}
	});

	it('returns false when window.self === window.top (not in iframe)', async () => {
		// Ensure self === top
		Object.defineProperty(globalThis.window, 'self', {
			value: globalThis.window,
			writable: true,
			configurable: true
		});
		Object.defineProperty(globalThis.window, 'top', {
			value: globalThis.window,
			writable: true,
			configurable: true
		});

		const { isInIframe } = await loadFreshModule();
		expect(isInIframe()).toBe(false);
	});

	it('returns true when window.self !== window.top (in iframe)', async () => {
		const fakeTop = {} as Window;
		Object.defineProperty(globalThis.window, 'self', {
			value: globalThis.window,
			writable: true,
			configurable: true
		});
		Object.defineProperty(globalThis.window, 'top', {
			value: fakeTop,
			writable: true,
			configurable: true
		});

		const { isInIframe } = await loadFreshModule();
		expect(isInIframe()).toBe(true);
	});

	it('returns true when accessing window.top throws (cross-origin)', async () => {
		Object.defineProperty(globalThis.window, 'top', {
			get() {
				throw new DOMException('Blocked', 'SecurityError');
			},
			configurable: true
		});

		const { isInIframe } = await loadFreshModule();
		expect(isInIframe()).toBe(true);
	});

	it('returns boolean type', async () => {
		const { isInIframe } = await loadFreshModule();
		expect(typeof isInIframe()).toBe('boolean');
	});
});

// =====================================================================
// safeStorage.getItem()
// =====================================================================

describe('safeStorage.getItem()', () => {
	let originalLocalStorage: Storage;

	beforeEach(() => {
		originalLocalStorage = globalThis.localStorage;
	});

	afterEach(() => {
		Object.defineProperty(globalThis, 'localStorage', {
			value: originalLocalStorage,
			writable: true,
			configurable: true
		});
	});

	it('returns value when storage is available and key exists', async () => {
		const mockStorage = createMockStorage();
		mockStorage.setItem('testKey', 'testValue');
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		expect(safeStorage.getItem('testKey')).toBe('testValue');
	});

	it('returns null when storage is available but key does not exist', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		expect(safeStorage.getItem('nonexistent')).toBeNull();
	});

	it('returns null when storage is blocked', async () => {
		const throwingStorage = createThrowingStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: throwingStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		expect(safeStorage.getItem('anything')).toBeNull();
	});

	it('does not throw when storage is blocked', async () => {
		const throwingStorage = createThrowingStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: throwingStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		expect(() => safeStorage.getItem('key')).not.toThrow();
	});

	it('returns null when getItem itself throws after storage check passes', async () => {
		// Storage probe succeeds but subsequent getItem throws
		let callCount = 0;
		const weirdStorage: Storage = {
			...createMockStorage(),
			setItem: vi.fn(),
			removeItem: vi.fn(),
			getItem: vi.fn(() => {
				callCount++;
				if (callCount > 0) {
					throw new Error('Unexpected error');
				}
				return null;
			})
		};
		Object.defineProperty(globalThis, 'localStorage', {
			value: weirdStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		// The isStorageAvailable check will pass (uses setItem/removeItem)
		// Then getItem will throw, and safeStorage should catch it
		expect(safeStorage.getItem('key')).toBeNull();
	});
});

// =====================================================================
// safeStorage.setItem()
// =====================================================================

describe('safeStorage.setItem()', () => {
	let originalLocalStorage: Storage;

	beforeEach(() => {
		originalLocalStorage = globalThis.localStorage;
	});

	afterEach(() => {
		Object.defineProperty(globalThis, 'localStorage', {
			value: originalLocalStorage,
			writable: true,
			configurable: true
		});
	});

	it('stores value when storage is available', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		safeStorage.setItem('myKey', 'myValue');

		// The probe setItem + our setItem = at least our call
		expect(mockStorage.setItem).toHaveBeenCalledWith('myKey', 'myValue');
	});

	it('does not throw when storage is blocked', async () => {
		const throwingStorage = createThrowingStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: throwingStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		expect(() => safeStorage.setItem('key', 'value')).not.toThrow();
	});

	it('silently fails when storage is not available (does not write)', async () => {
		const throwingStorage = createThrowingStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: throwingStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		safeStorage.setItem('key', 'value');

		// setItem was called once during probe (which threw), not again for our call
		// because isStorageAvailable() returned false
		expect(throwingStorage.setItem).toHaveBeenCalledTimes(1);
	});

	it('does not throw when setItem itself throws after storage check passes', async () => {
		// Storage probe succeeds but subsequent setItem throws (e.g., quota exceeded)
		let probed = false;
		const quotaStorage: Storage = {
			...createMockStorage(),
			setItem: vi.fn((key: string) => {
				if (key === '__storage_test__') {
					probed = true;
					return; // probe succeeds
				}
				if (probed) {
					throw new DOMException('QuotaExceeded', 'QuotaExceededError');
				}
			}),
			removeItem: vi.fn()
		};
		Object.defineProperty(globalThis, 'localStorage', {
			value: quotaStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		expect(() => safeStorage.setItem('big', 'data')).not.toThrow();
	});

	it('accepts empty string as value', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		safeStorage.setItem('key', '');
		expect(mockStorage.setItem).toHaveBeenCalledWith('key', '');
	});
});

// =====================================================================
// safeStorage.removeItem()
// =====================================================================

describe('safeStorage.removeItem()', () => {
	let originalLocalStorage: Storage;

	beforeEach(() => {
		originalLocalStorage = globalThis.localStorage;
	});

	afterEach(() => {
		Object.defineProperty(globalThis, 'localStorage', {
			value: originalLocalStorage,
			writable: true,
			configurable: true
		});
	});

	it('removes item when storage is available', async () => {
		const mockStorage = createMockStorage();
		mockStorage.setItem('myKey', 'myValue');
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		safeStorage.removeItem('myKey');

		// removeItem called once during probe (__storage_test__) + once for myKey
		expect(mockStorage.removeItem).toHaveBeenCalledWith('myKey');
	});

	it('does not throw when storage is blocked', async () => {
		const throwingStorage = createThrowingStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: throwingStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		expect(() => safeStorage.removeItem('anything')).not.toThrow();
	});

	it('silently fails when storage is not available (does not call removeItem)', async () => {
		const throwingStorage = createThrowingStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: throwingStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		safeStorage.removeItem('key');

		// removeItem was never called because isStorageAvailable() returned false
		// (the probe used setItem which threw)
		expect(throwingStorage.removeItem).not.toHaveBeenCalled();
	});

	it('does not throw when removeItem itself throws after storage check passes', async () => {
		let probed = false;
		const weirdStorage: Storage = {
			...createMockStorage(),
			setItem: vi.fn(() => {
				probed = true;
			}),
			removeItem: vi.fn((key: string) => {
				if (key !== '__storage_test__' && probed) {
					throw new Error('Unexpected error on remove');
				}
			})
		};
		Object.defineProperty(globalThis, 'localStorage', {
			value: weirdStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		expect(() => safeStorage.removeItem('key')).not.toThrow();
	});

	it('does not throw for non-existent key', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		expect(() => safeStorage.removeItem('never_existed')).not.toThrow();
	});
});

// =====================================================================
// Integration: safeStorage round-trip
// =====================================================================

describe('safeStorage round-trip', () => {
	let originalLocalStorage: Storage;

	beforeEach(() => {
		originalLocalStorage = globalThis.localStorage;
	});

	afterEach(() => {
		Object.defineProperty(globalThis, 'localStorage', {
			value: originalLocalStorage,
			writable: true,
			configurable: true
		});
	});

	it('set then get returns the value', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		safeStorage.setItem('round', 'trip');
		expect(safeStorage.getItem('round')).toBe('trip');
	});

	it('set then remove then get returns null', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		safeStorage.setItem('temp', 'data');
		safeStorage.removeItem('temp');
		expect(safeStorage.getItem('temp')).toBeNull();
	});

	it('overwriting a key updates the value', async () => {
		const mockStorage = createMockStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: mockStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();
		safeStorage.setItem('key', 'first');
		safeStorage.setItem('key', 'second');
		expect(safeStorage.getItem('key')).toBe('second');
	});

	it('all operations are no-ops when storage is blocked', async () => {
		const throwingStorage = createThrowingStorage();
		Object.defineProperty(globalThis, 'localStorage', {
			value: throwingStorage,
			writable: true,
			configurable: true
		});

		const { safeStorage } = await loadFreshModule();

		// None of these should throw
		safeStorage.setItem('key', 'value');
		expect(safeStorage.getItem('key')).toBeNull();
		safeStorage.removeItem('key');
	});
});

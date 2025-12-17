/**
 * Utility to check if localStorage is available.
 * This is important for iframe embedding scenarios where tracking prevention
 * may block storage access.
 */

let storageAvailable: boolean | null = null;

/**
 * Checks if localStorage is available and accessible.
 * Returns false in cross-origin iframe contexts where tracking prevention blocks storage.
 */
export function isStorageAvailable(): boolean {
	if (storageAvailable !== null) {
		return storageAvailable;
	}

	try {
		const testKey = '__storage_test__';
		localStorage.setItem(testKey, testKey);
		localStorage.removeItem(testKey);
		storageAvailable = true;
		return true;
	} catch {
		storageAvailable = false;
		return false;
	}
}

/**
 * Checks if the current page is running inside an iframe.
 */
export function isInIframe(): boolean {
	try {
		return window.self !== window.top;
	} catch {
		// If we can't access window.top due to cross-origin restrictions, we're in an iframe
		return true;
	}
}

/**
 * Safe localStorage wrapper that handles blocked storage gracefully.
 */
export const safeStorage = {
	getItem(key: string): string | null {
		if (!isStorageAvailable()) return null;
		try {
			return localStorage.getItem(key);
		} catch {
			return null;
		}
	},

	setItem(key: string, value: string): void {
		if (!isStorageAvailable()) return;
		try {
			localStorage.setItem(key, value);
		} catch {
			// Silently fail - storage not available
		}
	},

	removeItem(key: string): void {
		if (!isStorageAvailable()) return;
		try {
			localStorage.removeItem(key);
		} catch {
			// Silently fail - storage not available
		}
	}
};

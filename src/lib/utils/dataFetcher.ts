import { browser } from '$app/environment';
import { base } from '$app/paths';

/**
 * In-memory cache for fetched data
 */
const memoryCache = new Map<string, { data: unknown; timestamp: number }>();

/**
 * Default cache TTL: 5 minutes
 */
const DEFAULT_CACHE_TTL = 5 * 60 * 1000;

interface FetchDataOptions {
	/**
	 * Whether to use in-memory caching
	 */
	cache?: boolean;
	/**
	 * Cache time-to-live in milliseconds
	 */
	cacheTTL?: number;
	/**
	 * Custom fetch options
	 */
	fetchOptions?: RequestInit;
	/**
	 * Whether to parse as JSON (default: true)
	 */
	parseJson?: boolean;
}

/**
 * Fetch JSON data with optional caching
 *
 * @param path - Path relative to /data/ (e.g., 'index-entities.json')
 * @param options - Fetch options
 * @returns Parsed JSON data
 */
export async function fetchData<T>(
	path: string,
	options: FetchDataOptions = {}
): Promise<T> {
	const { cache = true, cacheTTL = DEFAULT_CACHE_TTL, fetchOptions = {}, parseJson = true } =
		options;

	const url = `${base}/data/${path}`;

	// Check in-memory cache
	if (cache && browser) {
		const cached = memoryCache.get(url);
		if (cached && Date.now() - cached.timestamp < cacheTTL) {
			return cached.data as T;
		}
	}

	const response = await fetch(url, {
		...fetchOptions,
		headers: {
			// Accept compressed responses (browsers handle this automatically,
			// but being explicit doesn't hurt)
			Accept: 'application/json',
			...fetchOptions.headers
		}
	});

	if (!response.ok) {
		throw new Error(`Failed to fetch ${path}: HTTP ${response.status}`);
	}

	const data = parseJson ? await response.json() : await response.text();

	// Store in memory cache
	if (cache && browser) {
		memoryCache.set(url, { data, timestamp: Date.now() });
	}

	return data as T;
}

/**
 * Prefetch multiple data files in parallel
 *
 * @param paths - Array of paths relative to /data/
 * @returns Array of fetched data
 */
export async function prefetchData<T extends unknown[]>(
	paths: string[]
): Promise<T> {
	const results = await Promise.all(paths.map((path) => fetchData(path)));
	return results as T;
}

/**
 * Clear the in-memory cache
 *
 * @param path - Optional specific path to clear, or all if omitted
 */
export function clearDataCache(path?: string): void {
	if (path) {
		const url = `${base}/data/${path}`;
		memoryCache.delete(url);
	} else {
		memoryCache.clear();
	}
}

/**
 * Create a paginated data fetcher for large datasets
 *
 * @param basePath - Base path for the data (e.g., 'topics/')
 * @param pageSize - Number of items per page
 * @returns Paginated fetcher functions
 */
export function createPaginatedFetcher<T>(basePath: string, pageSize: number = 10) {
	let currentPage = 0;
	let hasMore = true;
	const allItems: T[] = [];

	return {
		/**
		 * Fetch the next page of data
		 */
		async fetchNextPage(): Promise<T[]> {
			if (!hasMore) return [];

			try {
				const data = await fetchData<T[]>(`${basePath}page-${currentPage}.json`);
				if (data.length < pageSize) {
					hasMore = false;
				}
				allItems.push(...data);
				currentPage++;
				return data;
			} catch {
				hasMore = false;
				return [];
			}
		},

		/**
		 * Get all fetched items
		 */
		getAllItems(): T[] {
			return allItems;
		},

		/**
		 * Check if more pages are available
		 */
		hasMorePages(): boolean {
			return hasMore;
		},

		/**
		 * Reset the fetcher
		 */
		reset(): void {
			currentPage = 0;
			hasMore = true;
			allItems.length = 0;
		}
	};
}

/**
 * Fetch data with automatic retry on failure
 *
 * @param path - Path relative to /data/
 * @param maxRetries - Maximum number of retry attempts
 * @param delayMs - Delay between retries in milliseconds
 * @returns Fetched data
 */
export async function fetchDataWithRetry<T>(
	path: string,
	maxRetries: number = 3,
	delayMs: number = 1000
): Promise<T> {
	let lastError: Error | null = null;

	for (let attempt = 0; attempt < maxRetries; attempt++) {
		try {
			return await fetchData<T>(path, { cache: false });
		} catch (e) {
			lastError = e instanceof Error ? e : new Error('Unknown error');
			if (attempt < maxRetries - 1) {
				await new Promise((resolve) => setTimeout(resolve, delayMs * (attempt + 1)));
			}
		}
	}

	throw lastError || new Error(`Failed to fetch ${path} after ${maxRetries} attempts`);
}

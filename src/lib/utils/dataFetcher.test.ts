import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// ── Mocks ────────────────────────────────────────────────────────────
// Must be hoisted before the import of the module under test.

let mockBrowser = true;

vi.mock('$app/environment', () => ({
	get browser() {
		return mockBrowser;
	}
}));

vi.mock('$app/paths', () => ({ base: '' }));

const mockFetch = vi.fn();
(globalThis as Record<string, unknown>).fetch = mockFetch;

import {
	fetchData,
	prefetchData,
	clearDataCache,
	createPaginatedFetcher,
	fetchDataWithRetry
} from './dataFetcher.js';

// ── Helpers ──────────────────────────────────────────────────────────

/** Build a minimal Response-like object that fetch() would return. */
function jsonResponse<T>(data: T, status = 200): Response {
	return {
		ok: status >= 200 && status < 300,
		status,
		json: () => Promise.resolve(data),
		text: () => Promise.resolve(JSON.stringify(data))
	} as unknown as Response;
}

function textResponse(text: string, status = 200): Response {
	return {
		ok: status >= 200 && status < 300,
		status,
		json: () => Promise.reject(new Error('not json')),
		text: () => Promise.resolve(text)
	} as unknown as Response;
}

function errorResponse(status: number): Response {
	return {
		ok: false,
		status,
		json: () => Promise.resolve({}),
		text: () => Promise.resolve('')
	} as unknown as Response;
}

// ── Setup / Teardown ─────────────────────────────────────────────────

beforeEach(() => {
	mockFetch.mockReset();
	clearDataCache();
	mockBrowser = true;
});

afterEach(() => {
	vi.restoreAllMocks();
	vi.useRealTimers();
});

// =====================================================================
// fetchData
// =====================================================================

describe('fetchData', () => {
	it('constructs the correct URL from path', async () => {
		mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true }));
		await fetchData('index-entities.json');
		expect(mockFetch).toHaveBeenCalledWith(
			'/data/index-entities.json',
			expect.objectContaining({
				headers: expect.objectContaining({ Accept: 'application/json' })
			})
		);
	});

	it('returns parsed JSON on success', async () => {
		const payload = { items: [1, 2, 3] };
		mockFetch.mockResolvedValueOnce(jsonResponse(payload));
		const result = await fetchData<typeof payload>('items.json');
		expect(result).toEqual(payload);
	});

	it('throws on HTTP 404', async () => {
		mockFetch.mockResolvedValueOnce(errorResponse(404));
		await expect(fetchData('missing.json')).rejects.toThrow('HTTP 404');
	});

	it('throws on HTTP 500', async () => {
		mockFetch.mockResolvedValueOnce(errorResponse(500));
		await expect(fetchData('broken.json')).rejects.toThrow('HTTP 500');
	});

	// ── Caching ──────────────────────────────────────────────────────

	it('returns cached data on second call without re-fetching', async () => {
		const payload = { cached: true };
		mockFetch.mockResolvedValueOnce(jsonResponse(payload));

		const first = await fetchData('cached.json');
		const second = await fetchData('cached.json');

		expect(first).toEqual(payload);
		expect(second).toEqual(payload);
		expect(mockFetch).toHaveBeenCalledTimes(1);
	});

	it('re-fetches after cache TTL expires', async () => {
		vi.useFakeTimers();

		const first = { version: 1 };
		const second = { version: 2 };
		mockFetch.mockResolvedValueOnce(jsonResponse(first));
		mockFetch.mockResolvedValueOnce(jsonResponse(second));

		const r1 = await fetchData('ttl.json', { cacheTTL: 1000 });
		expect(r1).toEqual(first);

		// Advance past TTL
		vi.advanceTimersByTime(1500);

		const r2 = await fetchData('ttl.json', { cacheTTL: 1000 });
		expect(r2).toEqual(second);
		expect(mockFetch).toHaveBeenCalledTimes(2);
	});

	it('bypasses cache when cache: false', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ n: 1 }));

		await fetchData('no-cache.json', { cache: false });
		await fetchData('no-cache.json', { cache: false });

		expect(mockFetch).toHaveBeenCalledTimes(2);
	});

	it('does not cache when browser is false', async () => {
		mockBrowser = false;
		mockFetch.mockResolvedValue(jsonResponse({ server: true }));

		await fetchData('server.json');
		await fetchData('server.json');

		expect(mockFetch).toHaveBeenCalledTimes(2);
	});

	// ── parseJson option ─────────────────────────────────────────────

	it('returns raw text when parseJson is false', async () => {
		const raw = '<html>hello</html>';
		mockFetch.mockResolvedValueOnce(textResponse(raw));

		const result = await fetchData<string>('page.html', { parseJson: false });
		expect(result).toBe(raw);
	});

	// ── fetchOptions passthrough ─────────────────────────────────────

	it('passes custom fetchOptions through to fetch', async () => {
		mockFetch.mockResolvedValueOnce(jsonResponse({}));
		await fetchData('opts.json', {
			fetchOptions: { method: 'POST', body: '{}' }
		});
		expect(mockFetch).toHaveBeenCalledWith(
			'/data/opts.json',
			expect.objectContaining({
				method: 'POST',
				body: '{}'
			})
		);
	});

	it('merges custom headers with default Accept header', async () => {
		mockFetch.mockResolvedValueOnce(jsonResponse({}));
		await fetchData('headers.json', {
			fetchOptions: { headers: { Authorization: 'Bearer token' } }
		});
		const calledOptions = mockFetch.mock.calls[0][1];
		expect(calledOptions.headers).toEqual(
			expect.objectContaining({
				Accept: 'application/json',
				Authorization: 'Bearer token'
			})
		);
	});

	// ── Edge case: empty base path ───────────────────────────────────

	it('handles empty base path correctly', async () => {
		mockFetch.mockResolvedValueOnce(jsonResponse({}));
		await fetchData('test.json');
		expect(mockFetch.mock.calls[0][0]).toBe('/data/test.json');
	});
});

// =====================================================================
// prefetchData
// =====================================================================

describe('prefetchData', () => {
	it('fetches all paths in parallel and returns results in order', async () => {
		const data1 = { id: 1 };
		const data2 = { id: 2 };
		const data3 = { id: 3 };

		mockFetch.mockResolvedValueOnce(jsonResponse(data1));
		mockFetch.mockResolvedValueOnce(jsonResponse(data2));
		mockFetch.mockResolvedValueOnce(jsonResponse(data3));

		const results = await prefetchData<[typeof data1, typeof data2, typeof data3]>([
			'a.json',
			'b.json',
			'c.json'
		]);

		expect(results).toEqual([data1, data2, data3]);
		expect(mockFetch).toHaveBeenCalledTimes(3);
	});

	it('returns empty array for empty paths list', async () => {
		const results = await prefetchData([]);
		expect(results).toEqual([]);
		expect(mockFetch).not.toHaveBeenCalled();
	});

	it('propagates error from any failed fetch', async () => {
		mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true }));
		mockFetch.mockResolvedValueOnce(errorResponse(500));

		await expect(prefetchData(['good.json', 'bad.json'])).rejects.toThrow('HTTP 500');
	});
});

// =====================================================================
// clearDataCache
// =====================================================================

describe('clearDataCache', () => {
	it('clears specific path from cache', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ data: true }));

		await fetchData('specific.json');
		expect(mockFetch).toHaveBeenCalledTimes(1);

		clearDataCache('specific.json');

		await fetchData('specific.json');
		expect(mockFetch).toHaveBeenCalledTimes(2);
	});

	it('clears all cache when no path is given', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ data: true }));

		await fetchData('file1.json');
		await fetchData('file2.json');
		expect(mockFetch).toHaveBeenCalledTimes(2);

		clearDataCache();

		await fetchData('file1.json');
		await fetchData('file2.json');
		expect(mockFetch).toHaveBeenCalledTimes(4);
	});

	it('does not affect other cached entries when clearing specific path', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ data: true }));

		await fetchData('keep.json');
		await fetchData('remove.json');
		expect(mockFetch).toHaveBeenCalledTimes(2);

		clearDataCache('remove.json');

		// "keep.json" should still be cached
		await fetchData('keep.json');
		expect(mockFetch).toHaveBeenCalledTimes(2);

		// "remove.json" should re-fetch
		await fetchData('remove.json');
		expect(mockFetch).toHaveBeenCalledTimes(3);
	});
});

// =====================================================================
// createPaginatedFetcher
// =====================================================================

describe('createPaginatedFetcher', () => {
	it('fetchNextPage returns first page data', async () => {
		const page0 = [{ id: 1 }, { id: 2 }, { id: 3 }];
		mockFetch.mockResolvedValueOnce(jsonResponse(page0));

		const fetcher = createPaginatedFetcher<{ id: number }>('topics/', 3);
		const result = await fetcher.fetchNextPage();

		expect(result).toEqual(page0);
		expect(mockFetch).toHaveBeenCalledWith('/data/topics/page-0.json', expect.anything());
	});

	it('multiple fetchNextPage calls increment page number', async () => {
		const page0 = [1, 2, 3];
		const page1 = [4, 5, 6];
		mockFetch.mockResolvedValueOnce(jsonResponse(page0));
		mockFetch.mockResolvedValueOnce(jsonResponse(page1));

		const fetcher = createPaginatedFetcher<number>('items/', 3);
		await fetcher.fetchNextPage();
		await fetcher.fetchNextPage();

		expect(mockFetch).toHaveBeenCalledWith('/data/items/page-0.json', expect.anything());
		expect(mockFetch).toHaveBeenCalledWith('/data/items/page-1.json', expect.anything());
	});

	it('hasMorePages returns false when data.length < pageSize', async () => {
		const partialPage = [1, 2]; // pageSize is 5
		mockFetch.mockResolvedValueOnce(jsonResponse(partialPage));

		const fetcher = createPaginatedFetcher<number>('items/', 5);
		expect(fetcher.hasMorePages()).toBe(true);

		await fetcher.fetchNextPage();
		expect(fetcher.hasMorePages()).toBe(false);
	});

	it('hasMorePages stays true when data.length equals pageSize', async () => {
		const fullPage = [1, 2, 3, 4, 5];
		mockFetch.mockResolvedValueOnce(jsonResponse(fullPage));

		const fetcher = createPaginatedFetcher<number>('items/', 5);
		await fetcher.fetchNextPage();

		expect(fetcher.hasMorePages()).toBe(true);
	});

	it('getAllItems accumulates across pages', async () => {
		const page0 = [1, 2, 3];
		const page1 = [4, 5, 6];
		const page2 = [7]; // partial page
		mockFetch.mockResolvedValueOnce(jsonResponse(page0));
		mockFetch.mockResolvedValueOnce(jsonResponse(page1));
		mockFetch.mockResolvedValueOnce(jsonResponse(page2));

		const fetcher = createPaginatedFetcher<number>('items/', 3);
		await fetcher.fetchNextPage();
		await fetcher.fetchNextPage();
		await fetcher.fetchNextPage();

		expect(fetcher.getAllItems()).toEqual([1, 2, 3, 4, 5, 6, 7]);
	});

	it('reset clears state and allows re-fetching from page 0', async () => {
		const page0 = [1, 2];
		mockFetch.mockResolvedValue(jsonResponse(page0));

		const fetcher = createPaginatedFetcher<number>('items/', 5);
		await fetcher.fetchNextPage();
		expect(fetcher.hasMorePages()).toBe(false); // 2 < 5

		fetcher.reset();
		expect(fetcher.hasMorePages()).toBe(true);
		expect(fetcher.getAllItems()).toEqual([]);

		// Clear the data cache so the second fetchNextPage actually calls fetch
		clearDataCache();

		await fetcher.fetchNextPage();
		// Should fetch page-0 again
		const calls = mockFetch.mock.calls.map((c) => c[0]);
		expect(calls.filter((url: string) => url === '/data/items/page-0.json')).toHaveLength(2);
	});

	it('returns empty array when no more pages', async () => {
		const partialPage = [1];
		mockFetch.mockResolvedValueOnce(jsonResponse(partialPage));

		const fetcher = createPaginatedFetcher<number>('items/', 5);
		await fetcher.fetchNextPage(); // sets hasMore = false

		const result = await fetcher.fetchNextPage();
		expect(result).toEqual([]);
	});

	it('returns empty array and sets hasMore=false on fetch error', async () => {
		mockFetch.mockResolvedValueOnce(errorResponse(500));

		const fetcher = createPaginatedFetcher<number>('items/', 5);
		const result = await fetcher.fetchNextPage();

		expect(result).toEqual([]);
		expect(fetcher.hasMorePages()).toBe(false);
	});
});

// =====================================================================
// fetchDataWithRetry
// =====================================================================

describe('fetchDataWithRetry', () => {
	it('returns data on first success', async () => {
		const data = { success: true };
		mockFetch.mockResolvedValueOnce(jsonResponse(data));

		const result = await fetchDataWithRetry<typeof data>('ok.json', 3, 100);
		expect(result).toEqual(data);
		expect(mockFetch).toHaveBeenCalledTimes(1);
	});

	it('retries on failure and succeeds on a subsequent attempt', async () => {
		vi.useFakeTimers();

		mockFetch.mockResolvedValueOnce(errorResponse(500));
		mockFetch.mockResolvedValueOnce(jsonResponse({ recovered: true }));

		const promise = fetchDataWithRetry('flaky.json', 3, 100);

		// First attempt fails, then wait 100ms * 1 = 100ms before retry
		await vi.advanceTimersByTimeAsync(100);

		const result = await promise;
		expect(result).toEqual({ recovered: true });
		expect(mockFetch).toHaveBeenCalledTimes(2);
	});

	it('throws after all retries are exhausted', async () => {
		mockFetch.mockResolvedValue(errorResponse(500));

		// Use a short delay to keep the test fast with real timers.
		// Fake timers cause unhandled-rejection warnings because the
		// microtask that rejects inside fetchData settles before the
		// catch in fetchDataWithRetry runs.
		await expect(fetchDataWithRetry('fail.json', 3, 1)).rejects.toThrow('HTTP 500');
		expect(mockFetch).toHaveBeenCalledTimes(3);
	});

	it('uses linear backoff (delayMs * (attempt + 1))', async () => {
		vi.useFakeTimers();
		const setTimeoutSpy = vi.spyOn(globalThis, 'setTimeout');

		mockFetch.mockResolvedValueOnce(errorResponse(500));
		mockFetch.mockResolvedValueOnce(errorResponse(500));
		mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true }));

		const promise = fetchDataWithRetry('backoff.json', 3, 100);

		// After attempt 0 fails: delay = 100 * (0+1) = 100ms
		await vi.advanceTimersByTimeAsync(100);
		// After attempt 1 fails: delay = 100 * (1+1) = 200ms
		await vi.advanceTimersByTimeAsync(200);

		await promise;

		// Check the setTimeout calls: first delay 100ms, second delay 200ms
		const delayCalls = setTimeoutSpy.mock.calls
			.map((call) => call[1])
			.filter((ms): ms is number => typeof ms === 'number' && ms >= 100);
		expect(delayCalls).toContain(100);
		expect(delayCalls).toContain(200);

		setTimeoutSpy.mockRestore();
	});

	it('uses cache: false for each attempt', async () => {
		mockFetch.mockResolvedValueOnce(jsonResponse({ data: true }));

		// First pre-populate the cache
		await fetchData('retry-cache.json');

		// Reset mock to track retry calls
		mockFetch.mockReset();
		mockFetch.mockResolvedValueOnce(jsonResponse({ fresh: true }));

		const result = await fetchDataWithRetry('retry-cache.json', 1, 100);
		expect(result).toEqual({ fresh: true });
		// Should have called fetch because cache:false is used internally
		expect(mockFetch).toHaveBeenCalledTimes(1);
	});

	it('handles maxRetries of 1 (single attempt, no retry)', async () => {
		mockFetch.mockResolvedValueOnce(errorResponse(500));

		await expect(fetchDataWithRetry('once.json', 1, 100)).rejects.toThrow('HTTP 500');
		expect(mockFetch).toHaveBeenCalledTimes(1);
	});
});
